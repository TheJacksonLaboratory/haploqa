from bisect import bisect_left, bisect_right
from bson.objectid import ObjectId
from bson.son import SON
from celery import Celery
import flask
import json
import math
import numpy as np
import os
import pymongo
import tempfile
import uuid

import haploqa.haplohmm as hhmm
import haploqa.mongods as mds
import haploqa.finalreportimport as finalin
import haploqa.usermanagement as usrmgmt

app = flask.Flask(__name__)
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
app.config.update(
    CELERY_BROKER_URL=BROKER_URL,
    CELERY_RESULT_BACKEND=BROKER_URL,
)
app.jinja_env.globals.update(isnan=math.isnan)


# TODO this key must be changed to something secret (ie. not committed to the repo).
# Comment out the print message when this is done
print('===================================================')
print('THIS VERSION OF HaploQA IS NOT SECURE. YOU MUST    ')
print('REGENERATE THE SECRET KEY BEFORE DEPLOYMENT. SEE   ')
print('"How to generate good secret keys" AT			  ')
print('http://flask.pocoo.org/docs/quickstart/ FOR DETAILS')
print('===================================================')
app.secret_key = b'\x12}\x08\xfa\xbc\xaa6\x8b\xdd>%\x81`xk\x04\xb1\xdc\x8a0\xda\xa1\xab\x0f'


# special sample tag used to mark a strain as a potential haplotype
HAPLOTYPE_TAG = 'haplotype-strain'


#####################################################################
# FLASK/CELERY INITIALIZATION
#####################################################################

# make celery function based on http://flask.pocoo.org/docs/0.10/patterns/celery/
def _make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)

    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = _make_celery(app)


MAX_CONTRIB_STRAIN_COUNT = 15


@app.template_global()
def maximum_contributing_strain_count():
    return MAX_CONTRIB_STRAIN_COUNT


@app.template_global()
def escape_forward_slashes(s):
    """
    Escape forward slashes for our custom escape scheme where
    '/' escapes to '\f' and '\' escapes to '\b'. Note that
    http://flask.pocoo.org/snippets/76/ recommends against
    doing this, but the problem is that URL variable
    boundaries can be ambiguous in some cases if we don't do
    a simple escaping like this.

    :param s: the string
    :return: the escaped string
    """
    return s.replace('\\', '\\b').replace('/', '\\f')


@app.template_global()
def unescape_forward_slashes(s):
    """
    Unescape forward slashes for our custom escape scheme where
    '/' escapes to '\f' and '\' escapes to '\b'. Note that
    http://flask.pocoo.org/snippets/76/ recommends against
    doing this, but the problem is that URL variable
    boundaries can be ambiguous in some cases if we don't do
    a simple escaping like this.

    :param s: the escaped string
    :return: the unescaped string
    """
    return s.replace('\\f', '/').replace('\\b', '\\')


@app.after_request
def do_after(response):
    # tell browser not to cache non-static responses
    if not flask.request.path.startswith(app.static_url_path):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


#####################################################################
# USER ACCOUNT/LOGIN FUNCTIONS
#####################################################################


@app.before_request
def lookup_user_from_session():
    if not flask.request.path.startswith(app.static_url_path):
        # lookup the current user if the user_id is found in the session
        user_email_address = flask.session.get('user_email_address')
        if user_email_address:
            if flask.request.remote_addr == flask.session.get('remote_addr'):
                user = usrmgmt.lookup_user(user_email_address, mds.get_db())
                user_id = user.pop('_id', None)
                if user_id:
                    user['id'] = str(user_id)

                flask.g.user = user
            else:
                # If IP addresses don't match we're going to reset the session for
                # a bit of extra safety. Unfortunately this also means that we're
                # forcing valid users to log in again when they change networks
                _set_session_user(None)
        else:
            flask.g.user = None


@app.route('/invite-user.html', methods=['GET', 'POST'])
def invite_user_html():
    """
    Invite a new user to the application using their email address. Upon get
    the invite-user template is rendered. Upon successful POST the
    invite email is sent out and the browser is redirected to index.html
    """

    user = flask.g.user
    if user is None:
        return flask.render_template('login-required.html')
    elif not user['administrator']:
        flask.abort(403)
    else:
        if flask.request.method == 'GET':
            return flask.render_template('invite-user.html')
        elif flask.request.method == 'POST':
            form = flask.request.form
            usrmgmt.invite_admin(form['email'])

            # TODO flash a success message

            return flask.redirect(flask.url_for('index_html'), 303)


@app.route('/reset-password.html', methods=['POST', 'GET'])
def reset_password_html():
    if flask.request.method == 'GET':
        return flask.render_template('reset-password.html')
    elif flask.request.method == 'POST':
        form = flask.request.form
        usrmgmt.reset_password(form['email'])

        return flask.redirect(flask.url_for('index_html'), 303)


@app.route('/login.json', methods=['POST'])
def login_json():
    _form_login()
    user = flask.g.user
    if user is None:
        response = flask.jsonify({'success': False})
        response.status_code = 400

        return response
    else:
        return flask.jsonify(user)


def _set_session_user(user):
    flask.session.pop('user_email_address', None)
    flask.session.pop('remote_addr', None)
    if user is None:
        flask.g.user = None
    else:
        flask.session['user_email_address'] = user['email_address']
        remote_addr = flask.request.remote_addr
        if remote_addr:
            flask.session['remote_addr'] = remote_addr

        lookup_user_from_session()


def _form_login():
    _set_session_user(None)

    form = flask.request.form
    user = usrmgmt.authenticate_user(form['email'], form['password'], mds.get_db())
    if user is not None:
        _set_session_user(user)


@app.route('/logout.json', methods=['POST'])
def logout_json():
    _set_session_user(None)
    return flask.jsonify({'success': True})


@app.route('/validate-reset/<password_reset_id>.html', methods=['GET', 'POST'])
def validate_reset(password_reset_id):
    """
    A user should only arrive at this page if they have received a password reset email. Upon GET
    the reset password template is rendered. Upon POST we attempt to actually update the password
    :param password_reset_id: this ID is the secret that authorizes a password reset. It should
                              be contained in the reset email that was sent to the user
    """

    db = mds.get_db()
    form = flask.request.form
    user_to_reset = db.users.find_one({'password_reset_hash': usrmgmt.hash_str(password_reset_id)})
    if user_to_reset is None:
        # TODO create an message page explaining what went wrong and that the user
        # should try to reset their password again or contact an administrator if
        # they don't think it's a problem with an expired ID
        raise Exception('invalid password reset ID. It may have expired')

    if flask.request.method == 'POST':
        new_password = form['password']
        if len(new_password) < usrmgmt.MIN_PASSWORD_LENGTH:
            flask.flash('The given password is too short. It must contain at least {} characters.'.format(
                usrmgmt.MIN_PASSWORD_LENGTH
            ))
            return flask.render_template('validate-reset.html', reset_user=user_to_reset)
        else:
            new_salt = str(uuid.uuid4())
            db.users.update_one(
                {'password_reset_hash': usrmgmt.hash_str(password_reset_id)},
                {
                    '$set': {
                        'salt': new_salt,
                        'password_hash': usrmgmt.hash_str(new_password + new_salt)
                    },
                    '$unset': {
                        'password_reset_hash': ''
                    },
                }
            )
            user = usrmgmt.authenticate_user(user_to_reset['email_address'], new_password, db)
            _set_session_user(user)

            return flask.redirect(flask.url_for('index_html'), 303)
    elif flask.request.method == 'GET':
        return flask.render_template('validate-reset.html', reset_user=user_to_reset)


@app.route('/change-password.html', methods=['GET', 'POST'])
def change_password_html():
    """
    Render the HTML change-password template for gets and try to actually change
    the password for posts (followed by a redirect to index.html on success)
    """

    user = flask.g.user
    if user is not None:
        if flask.request.method == 'POST':

            form = flask.request.form
            old_password = form['old-password']
            new_password = form['new-password']
            if len(new_password) < usrmgmt.MIN_PASSWORD_LENGTH:
                flask.flash('The given password is too short. It must contain at least {} characters.'.format(
                    usrmgmt.MIN_PASSWORD_LENGTH
                ))
                return flask.render_template('change-password.html')
            else:
                new_salt = str(uuid.uuid4())

                db = mds.get_db()
                user_salt = usrmgmt.lookup_salt(user['email_address'], db)
                result = db.users.update_one(
                    {
                        'password_hash': usrmgmt.hash_str(old_password + user_salt)
                    },
                    {
                        '$set': {
                            'salt': new_salt,
                            'password_hash': usrmgmt.hash_str(new_password + new_salt)
                        },
                        '$unset': {
                            'password_reset_hash': ''
                        },
                    }
                )
                if result.modified_count:
                    return flask.redirect(flask.url_for('index_html'), 303)
                else:
                    flask.flash('bad password. Please try again, or logout and reset via the forgotten password link.')
                    return flask.render_template('change-password.html')
        elif flask.request.method == 'GET':
            return flask.render_template('change-password.html')


#####################################################################
# DATA IMPORT FUNCTIONS
#####################################################################


def _unique_temp_filename():
    return os.path.join(tempfile.tempdir, str(uuid.uuid4()))


@app.route('/sample-import-status/<task_id>.html')
def sample_import_status_html(task_id):
    """
    Render template for checking the status of a (potentially long-running) sample import task
    :param task_id: the celery task ID for the import
    :return: the Flask response object for the template
    """
    return flask.render_template('import-status.html', task_id=task_id)


@app.route('/sample-import-status/<task_id>.json')
def sample_import_status_json(task_id):
    """
    Render a JSON response describing the status of a (potentially long-running) sample import task.
    :param task_id: the celery task ID for the import
    :return: the flask response object for the status
    """

    async_result = sample_data_import_task.AsyncResult(task_id)

    # TODO check that user is logged in

    msg_dict = {
        'ready': async_result.ready(),
        'failed': async_result.failed(),
    }
    if async_result.failed():
        msg_dict['error_message'] = str(async_result.result)
        response = flask.jsonify(**msg_dict)

        # server error code
        response.status_code = 500

        return response
    else:
        msg_dict['result_tag'] = async_result.result

        return flask.jsonify(**msg_dict)


@app.route('/sample-data-import.html', methods=['GET', 'POST'])
def sample_data_import_html():
    """
    render the template for importing datasets
    """

    user = flask.g.user
    if user is None:
        return flask.render_template('login-required.html')
    else:
        form = flask.request.form
        files = flask.request.files

        db = mds.get_db()
        platform_ids = [x['platform_id'] for x in db.platforms.find({}, {'platform_id': 1})]

        if flask.request.method == 'POST':
            platform_id = form['platform-select']

            sample_map_filename = _unique_temp_filename()
            files['sample-map-file'].save(sample_map_filename)

            final_report_filename = _unique_temp_filename()
            final_report_file = files['final-report-file']
            final_report_file.save(final_report_filename)

            sample_group_name = os.path.splitext(final_report_file.filename)[0]
            import_task = sample_data_import_task.delay(
                platform_id,
                sample_map_filename,
                final_report_filename,
                sample_group_name)

            # perform a 303 redirect to the URL that uniquely identifies this run
            new_location = flask.url_for('sample_import_status_html', task_id=import_task.task_id)
            return flask.redirect(new_location, 303)
        else:
            return flask.render_template('sample-data-import.html', platform_ids=platform_ids)


@celery.task(name='sample_data_import_task')
def sample_data_import_task(platform_id, sample_map_filename, final_report_filename, sample_group_name):
    """
    Our long-running import task, triggered from the import page of the app
    """
    try:
        db = mds.get_db()
        tags = [sample_group_name, platform_id]
        finalin.import_final_report(final_report_filename, platform_id, tags, db)
    finally:
        # we don't need the files after the import is complete
        if os.path.isfile(sample_map_filename):
            os.remove(sample_map_filename)
        if os.path.isfile(final_report_filename):
            os.remove(final_report_filename)

    return sample_group_name


#####################################################################
# SAMPLE LISTING PAGES
#####################################################################


@app.route('/all-samples.html')
def all_samples_html():
    # look up all samples. Only return top level information though (snp-level data is too much)
    db = mds.get_db()
    samples = db.samples.find(
        {},
        {'chromosome_data': 0, 'unannotated_snps': 0}
    ).sort('sample_id', pymongo.ASCENDING)
    samples = list(samples)
    for sample in samples:
        _add_default_attributes(sample)

    return flask.render_template('samples.html', samples=samples)


@app.route('/tag/<tag_id>.html')
def sample_tag_html(tag_id):
    # this tag_id uses a home-grown forward slash escape.
    tag_id = unescape_forward_slashes(tag_id)

    # look up all samples with this tag ID. Only return top level information though
    # (snp-level data is too much)
    db = mds.get_db()
    matching_samples = db.samples.find(
        {'tags': tag_id},
        {'chromosome_data': 0, 'unannotated_snps': 0}
    ).sort('sample_id', pymongo.ASCENDING)
    matching_samples = list(matching_samples)
    for sample in matching_samples:
        _add_default_attributes(sample)

    return flask.render_template('sample-tag.html', samples=matching_samples, tag_id=tag_id)


@app.route('/standard-designation/<standard_designation>.html')
def standard_designation_html(standard_designation):
    # this standard_designation uses a home-grown forward slash escape.
    standard_designation = unescape_forward_slashes(standard_designation)

    # look up all samples with this standard_designation. Only return top level information though
    # (snp-level data is too much)
    db = mds.get_db()
    matching_samples = db.samples.find(
        {'standard_designation': standard_designation},
        {'chromosome_data': 0, 'unannotated_snps': 0}
    ).sort('sample_id', pymongo.ASCENDING)
    matching_samples = list(matching_samples)
    for sample in matching_samples:
        _add_default_attributes(sample)

    return flask.render_template(
        'standard-designation.html',
        samples=matching_samples,
        standard_designation=standard_designation)


#####################################################################
# index.html AND SEVERAL OTHER GENERAL INFORMATIVE TEMPLATES
#####################################################################


@app.route('/index.html')
@app.route('/')
def index_html():
    db = mds.get_db()

    # this pipeline should get us all tags along with their sample counts
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])},
    ]
    tags = db.samples.aggregate(pipeline)
    tags = [{'name': tag['_id'], 'sample_count': tag['count']} for tag in tags]

    sample_count = db.samples.count({})

    return flask.render_template('index.html', tags=tags, total_sample_count=sample_count)


@app.route('/help.html')
def help_html():
    return flask.render_template('help.html')


@app.route('/about.html')
def about_html():
    return flask.render_template('about.html')


@app.route('/contact.html')
def contact_html():
    return flask.render_template('contact.html')


#####################################################################
# SAMPLE VIEWING/EDITING FUNCTIONS
#####################################################################


def _add_default_attributes(sample):
    """
    Jinja2 templates are not as tolerant of missing attributes as I would like. This function
    serves to fill in default attribute values missing values in order to keep the templates
    happy
    :param sample: a sample dict as read from our mongo DB
    """
    # add call percents
    try:
        total_count = sample['heterozygous_count'] + \
                      sample['homozygous_count'] + \
                      sample['no_read_count']
        if total_count > 0:
            sample['heterozygous_percent'] = sample['heterozygous_count'] * 100.0 / total_count
            sample['homozygous_percent'] = sample['homozygous_count'] * 100.0 / total_count
            sample['no_read_percent'] = sample['no_read_count'] * 100.0 / total_count
    except KeyError:
        pass

    # add haplotype/concordance defaults
    if 'viterbi_haplotypes' not in sample:
        sample['viterbi_haplotypes'] = {}
    viterbi_haplotypes = sample['viterbi_haplotypes']

    if 'chromosome_data' not in viterbi_haplotypes:
        viterbi_haplotypes['chromosome_data'] = {}

    if 'informative_count' not in viterbi_haplotypes or 'concordant_count' not in viterbi_haplotypes:
        viterbi_haplotypes['informative_count'] = 0
        viterbi_haplotypes['concordant_count'] = 0
        viterbi_haplotypes['concordant_percent'] = None
    elif viterbi_haplotypes['informative_count'] == 0:
        viterbi_haplotypes['concordant_percent'] = None
    else:
        viterbi_haplotypes['concordant_percent'] = \
            viterbi_haplotypes['concordant_count'] * 100.0 / viterbi_haplotypes['informative_count']

    # add default color
    if 'color' not in sample:
        sample['color'] = '#000000'

    if 'standard_designation' not in sample:
        sample['standard_designation'] = None

    if 'gender' not in sample:
        sample['gender'] = None

    if 'notes' not in sample:
        sample['notes'] = None


@app.route('/sample/<mongo_id>.html')
def sample_html(mongo_id):
    """
    Render the HTML template for the sample
    :param mongo_id: the mongo ID string for the sample we're interested in
    :return: the Flask response for the template
    """

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = db.samples.find_one({'_id': obj_id})
    _add_default_attributes(sample)

    haplotype_samples = db.samples.find(
        {'tags': HAPLOTYPE_TAG, 'platform_id': sample['platform_id']},
        {'chromosome_data': 0, 'unannotated_snps': 0},
    )
    haplotype_samples = list(haplotype_samples)
    for curr_hap_sample in haplotype_samples:
        _add_default_attributes(curr_hap_sample)

    def contrib_strain_lbl(contrib_strain):
        if contrib_strain['standard_designation']:
            return contrib_strain['standard_designation']
        else:
            return contrib_strain['sample_id']
    contrib_strain_tokens = [
        {'value': str(x['_id']), 'label': contrib_strain_lbl(x)}
        for x in haplotype_samples
        if x['_id'] in sample['contributing_strains']
    ]

    all_tags = db.samples.distinct('tags')

    return flask.render_template(
        'sample.html',
        sample=sample,
        haplotype_samples=haplotype_samples,
        contrib_strain_tokens=contrib_strain_tokens,
        all_tags=all_tags,
    )


@app.route('/sample/<mongo_id>.json', methods=['POST'])
def update_sample(mongo_id):
    """
    Accepts a POST to update the sample identified by the given mongo_id string
    """

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)

    task_ids = []

    form = flask.request.form
    update_dict = dict()
    if 'sample_id' in form:
        update_dict['sample_id'] = form['sample_id'].strip()

    if 'tags' in form:
        update_dict['tags'] = json.loads(form['tags'])

    if 'color' in form:
        update_dict['color'] = form['color'].strip()

    if 'standard_designation' in form:
        update_dict['standard_designation'] = form['standard_designation'].strip()

    if 'notes' in form:
        update_dict['notes'] = form['notes'].strip()

    if 'contributing_strain_ids' in form:
        sample = db.samples.find_one({'_id': obj_id}, {'platform_id': 1, 'gender': 1})
        platform = db.platforms.find_one({'platform_id': sample['platform_id']})

        # remove Y chromosome from haplotype scan if sample is female
        unset_dict = dict()
        chr_ids = platform['chromosomes']
        if sample.get('gender', None) == 'female':
            unset_dict['viterbi_haplotypes.chromosome_data.Y'] = ''
            try:
                chr_ids.remove('Y')
            except ValueError:
                pass

        new_strain_ids = json.loads(form['contributing_strain_ids'])
        new_strain_ids = [ObjectId(x) for x in new_strain_ids[:MAX_CONTRIB_STRAIN_COUNT]]

        # we need to abort if not all contributing stains have the same platform
        for new_strain_id in new_strain_ids:
            new_strain = db.samples.find_one({'_id': new_strain_id}, {'platform_id': 1})
            if new_strain is None or 'platform_id' not in new_strain or new_strain['platform_id'] != sample['platform_id']:
                raise Exception('failed to find strain having id = {} and platform = {}'.format(
                    new_strain_id,
                    sample['platform_id']))

        haplotype_inference_uuid = str(uuid.uuid4())

        # we need to update the document and invalidate existing haplotypes
        update_dict['contributing_strains'] = new_strain_ids
        update_dict['haplotype_inference_uuid'] = haplotype_inference_uuid
        for chr_id in chr_ids:
            update_dict['viterbi_haplotypes.chromosome_data.' + chr_id] = {
                'results_pending': bool(new_strain_ids)
            }
        update_dict['viterbi_haplotypes.informative_count'] = 0
        update_dict['viterbi_haplotypes.concordant_count'] = 0
        if unset_dict:
            db.samples.update_one({'_id': obj_id}, {'$set': update_dict, '$unset': unset_dict})
        else:
            db.samples.update_one({'_id': obj_id}, {'$set': update_dict})

        # since we invalidated haplotypes lets kick off tasks to recalculate
        if new_strain_ids:
            sample_obj_id = str(sample['_id'])
            for chr_id in chr_ids:
                t = infer_haplotype_structure_task.delay(
                    sample_obj_id,
                    chr_id,
                    haplotype_inference_uuid,
                )
                task_ids.append(t.task_id)

    elif update_dict:
        db.samples.update_one({'_id': obj_id}, {'$set': update_dict})

    return flask.jsonify(task_ids=task_ids)


#####################################################################
# SAMPLE HAPLOTYPE/HMM FUNCTIONS
#####################################################################


DEFAULT_CANDIDATE_HAPLOTYPE_LIMIT = 20


@app.route('/best-haplotype-candidates/<sample_mongo_id_str>/chr<chr_id>-<int:start_pos_bp>-<int:end_pos_bp>.json')
def best_haplotype_candidates(sample_mongo_id_str, chr_id, start_pos_bp, end_pos_bp):
    """
    This function will search all possible combinations of haplotypes for the given sample
    and interval, finding the most likely haplotype combinations and returning them
    in sorted order (from most likely to least likely)
    :param sample_mongo_id_str:
    :param chr_id: the chromosome ID string. like: "X", "2", ...
    :param start_pos_bp: the start position to search
    :param end_pos_bp: the end position to search
    :return: the JSON response containing the most likely haplotype combinations
    """

    # TODO: this is a bit too heavyweight for a web request and should be delegated to the celery task queue

    limit = flask.request.args.get('limit', None)
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            limit = None

    if limit is None:
        limit = DEFAULT_CANDIDATE_HAPLOTYPE_LIMIT

    db = mds.get_db()
    obj_id = ObjectId(sample_mongo_id_str)
    sample = db.samples.find_one(
        {'_id': obj_id},
        {
            'platform_id': 1,
            'chromosome_data.' + chr_id + '.allele1_fwds': 1,
            'chromosome_data.' + chr_id + '.allele2_fwds': 1,
        }
    )

    # calculate which SNPs fall within the interval of interest
    snps = list(mds.get_snps(sample['platform_id'], chr_id, db))
    snp_positions = [x['position_bp'] for x in snps]
    left_index = bisect_left(snp_positions, start_pos_bp)
    right_index = bisect_right(snp_positions, end_pos_bp, left_index)
    snp_limit = right_index - left_index
    snps = snps[left_index:right_index]

    best_candidates = []
    if snps:
        # get sliced versions of our main sample and the haplotype samples
        sample = db.samples.find_one(
            {'_id': obj_id},
            {
                'platform_id': 1,
                'chromosome_data.' + chr_id + '.allele1_fwds': {'$slice': [left_index, snp_limit]},
                'chromosome_data.' + chr_id + '.allele2_fwds': {'$slice': [left_index, snp_limit]},
            }
        )
        sample_ab = hhmm.samples_to_ab_codes([sample], chr_id, snps)

        haplotype_samples = list(db.samples.find(
            {
                '_id': {'$ne': obj_id},
                'tags': HAPLOTYPE_TAG,
                'platform_id': sample['platform_id']
            },
            {
                'sample_id': 1,
                'standard_designation': 1,
                'color': 1,
                'chromosome_data.' + chr_id + '.allele1_fwds': {'$slice': [left_index, snp_limit]},
                'chromosome_data.' + chr_id + '.allele2_fwds': {'$slice': [left_index, snp_limit]},
            }
        ))
        for hap_sample in haplotype_samples:
            _add_default_attributes(hap_sample)
        hap_sample_count = len(haplotype_samples)
        haplotype_samples_ab = hhmm.samples_to_ab_codes(haplotype_samples, chr_id, snps)

        # get the haplotype indexes and sort them by likelihood
        haplo_likelihoods = []
        hmm = _make_hmm()
        for i in range(hap_sample_count):
            for j in range(i, hap_sample_count):
                curr_loglikelihood = hmm.log_likelihood(
                    haplotype_samples_ab[:, i],
                    haplotype_samples_ab[:, j],
                    sample_ab[:, 0])
                haplo_likelihoods.append((i, j, curr_loglikelihood))
        haplo_likelihoods.sort(key=lambda tup: -tup[2])
        haplo_likelihoods = haplo_likelihoods[:limit]

        for i, j, curr_loglikelihood in haplo_likelihoods:
            hap1 = haplotype_samples[i]
            hap2 = haplotype_samples[j]
            best_candidates.append({
                'haplotype_1': {
                    '_id': str(hap1['_id']),
                    'sample_id': hap1['sample_id'],
                    'standard_designation': hap1['standard_designation'],
                },
                'haplotype_2': {
                    '_id': str(hap2['_id']),
                    'sample_id': hap2['sample_id'],
                    'standard_designation': hap2['standard_designation'],
                },
                'neg_log_likelihood': -curr_loglikelihood,
            })

    return flask.jsonify(best_candidates=best_candidates);


@app.route('/sample/<mongo_id>/viterbi-haplotypes.json')
def viterbi_haplotypes_json(mongo_id):
    """
    Fetches and returns the previously calculated haplotypes for the sample indicated by mongo_id.
    Note that if haplotype calculation is underway, any incomplete chromosomes will have an
    results_pending value set to true like:
    sample.viterbi_haplotypes.chromosome_data.<chr_id>.results_pending = True
    :param mongo_id: the mongo ID string
    :return: the haplotype JSON response
    """

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = db.samples.find_one({'_id': obj_id}, {'viterbi_haplotypes': 1, 'contributing_strains': 1})
    _add_default_attributes(sample)
    haplotype_samples = [
        db.samples.find_one({'_id': x}, {'sample_id': 1, 'color': 1})
        for x in sample['contributing_strains']
    ]
    for curr_hap_sample in haplotype_samples:
        _add_default_attributes(curr_hap_sample)
    haplotype_samples = [
        {'obj_id': str(x['_id']), 'sample_id': x['sample_id']}
        for x in haplotype_samples
    ]

    return flask.jsonify(
        viterbi_haplotypes=sample['viterbi_haplotypes'],
        haplotype_samples=haplotype_samples
    )


def _earliest_run_start(
        prev1_start, prev1_haplo, curr1_haplo,
        prev2_start, prev2_haplo, curr2_haplo):
    """
    find the earliest "prev start" such that the "prev" and "curr" haplos match
    """

    earliest_start = None
    if prev1_haplo == curr1_haplo:
        earliest_start = prev1_start

    if prev2_haplo == curr2_haplo:
        if earliest_start is None or prev2_start < prev1_start:
            earliest_start = prev2_start

    return earliest_start


def _extend_haplotype_blocks(blocks):
    """
    A greedy algorithm extending haplotype runs as long as possible. While the greedy algorithm does not
    give the optimal solution in all cases it should normally give the right result and is fast and
    easy to implement.

    :param blocks: the haplotype blocks to extend
    :return: None
    """
    if blocks:
        blocks = iter(blocks)
        prev_block = next(blocks)
        prev1_start = 0
        prev2_start = 0
        for curr_block in blocks:
            curr1 = curr_block['haplotype_index_1']
            curr2 = curr_block['haplotype_index_2']
            prev1 = prev_block['haplotype_index_1']
            prev2 = prev_block['haplotype_index_2']

            # can we extend the longest haplotype by doing a swap? if so we'll do it
            earliest_swapped_start = _earliest_run_start(prev1_start, prev1, curr2, prev2_start, prev2, curr1)
            if earliest_swapped_start is not None:
                earliest_noswap_start = _earliest_run_start(prev1_start, prev1, curr1, prev2_start, prev2, curr2)
                if earliest_noswap_start is None or earliest_swapped_start < earliest_noswap_start:
                    curr_block['haplotype_index_1'] = curr2
                    curr_block['haplotype_index_2'] = curr1

            # update previous block and haplotype start positions for next iteration
            if curr_block['haplotype_index_1'] != prev1:
                prev1_start = curr_block['start_position_bp']
            if curr_block['haplotype_index_2'] != prev2:
                prev2_start = curr_block['start_position_bp']
            prev_block = curr_block


def _make_hmm():
    """
    Make an HMM with our hardcoded parameters.
    """

    # TODO params should be adjustable (the user should be able to modify these and save them to the DB)

    # construct an HMM model
    hom_obs_probs = np.array([
        50,     # matching homozygous
        0.5,    # opposite homozygous
        1,      # het
        1,      # no read
    ], dtype=np.float64)
    het_obs_probs = np.array([
        50,     # het obs
        2,      # hom obs
        2,      # no read obs
    ], dtype=np.float64)
    n_obs_probs = np.ones(3, dtype=np.float64)

    trans_prob = 0.01
    hmm = hhmm.SnpHaploHMM(trans_prob, hom_obs_probs, het_obs_probs, n_obs_probs)

    return hmm


@celery.task(name='infer_haplotype_structure_task')
def infer_haplotype_structure_task(sample_obj_id_str, chr_id, haplotype_inference_uuid):
    """
    This celery task does the heavy lifting of actually calculating the haplotypes for a given
    strain. This involves extracting SNP sequences from this sample as well as from all of
    the contributing_strains samples and delegating the HMM calculation to our HMM model.
    :param sample_obj_id_str: the mongo string ID for the sample we're haplotyping
    :param chr_id: the chromosome to haplotype
    :param haplotype_inference_uuid:
        this tag is just used to make sure that haplotypes are
        inferred with the latest HMM settings (we need to prevent older inference
        tasks from overwriting the results from newer inference tasks since we're
        doing inference asynchronously)
    """
    # look up all of the sample IDs and get their ab codes
    sample_obj_id = ObjectId(sample_obj_id_str)
    db = mds.get_db()
    sample = db.samples.find_one(
        {
            # TODO add an index for this
            '_id': sample_obj_id,
            'haplotype_inference_uuid': haplotype_inference_uuid,
        },
        {
            'contributing_strains': 1,
            'platform_id': 1,
            'chromosome_data.' + chr_id: 1,
        })

    if sample is not None and sample['contributing_strains']:
        snps = list(mds.get_snps(sample['platform_id'], chr_id, db))
        contrib_strains = [
            db.samples.find_one({'_id': obj_id}, {'chromosome_data.' + chr_id: 1})
            for obj_id in sample['contributing_strains']
        ]
        contrib_ab_codes = hhmm.samples_to_ab_codes(contrib_strains, chr_id, snps)
        sample_ab_codes = hhmm.samples_to_ab_codes([sample], chr_id, snps)[:, 0]

        hmm = _make_hmm()

        # run viterbi to get maximum likelihood path
        max_likelihood_states, max_final_likelihood = hmm.viterbi(
            haplotype_ab_codes=contrib_ab_codes,
            observation_ab_codes=sample_ab_codes)
        haplotype_dict = _call_concordance(
            max_likelihood_states,
            sample_ab_codes,
            contrib_ab_codes,
            snps,
        )

        # convert haplotypes into coordinates representation
        num_snps = len(snps)
        haplotype_blocks = []
        start_state = max_likelihood_states[0]
        start_pos_bp = snps[0]['position_bp']
        curr_state = None
        for curr_index in range(1, num_snps):
            curr_state = max_likelihood_states[curr_index]
            if curr_state != start_state:
                haplotype_blocks.append({
                    'start_position_bp': start_pos_bp,
                    'end_position_bp': snps[curr_index]['position_bp'] - 1,
                    'haplotype_index_1': start_state[0],
                    'haplotype_index_2': start_state[1],
                })

                start_state = curr_state
                start_pos_bp = snps[curr_index]['position_bp']

        haplotype_blocks.append({
            'start_position_bp': start_pos_bp,
            'end_position_bp': snps[num_snps - 1]['position_bp'],
            'haplotype_index_1': curr_state[0],
            'haplotype_index_2': curr_state[1],
        })
        _extend_haplotype_blocks(haplotype_blocks)
        haplotype_dict['haplotype_blocks'] = haplotype_blocks
        haplotype_dict['results_pending'] = False

        print('updating haplotypes for sample {}, chr {}'.format(sample_obj_id_str, chr_id))
        db.samples.update_one(
            {
                # TODO add an index for this
                '_id': sample_obj_id,
                'haplotype_inference_uuid': haplotype_inference_uuid,
            },
            {
                '$set': {'viterbi_haplotypes.chromosome_data.' + chr_id: haplotype_dict},
                '$inc': {
                    'viterbi_haplotypes.informative_count': haplotype_dict['informative_count'],
                    'viterbi_haplotypes.concordant_count': haplotype_dict['concordant_count'],
                }
            },
        )


CONCORDANCE_BIN_SIZE = 50


def _call_concordance(max_likelihood_states, sample_ab_codes, contrib_ab_codes, snps):
    """
    Calculates call concordance as a series of bins (the resulting concordance values are what
    we use to render the histograms on the karyotype plots)
    """

    informative_count = 0
    concordant_count = 0
    # TODO storing indexes in this way is very fragile (if SNP count or ordering changes at all
    #      the whole thing is broken). The advantage is that it's very space-compact. Is there
    #      anything that gives us the best of both (how much space do obj ids take?)
    discordant_snp_indexes = []
    concordance_bins = []
    curr_bin_start_pos = -1
    curr_bin_informative = 0
    curr_bin_concordant = 0

    for t, curr_state in enumerate(max_likelihood_states):
        if curr_bin_start_pos == -1:
            curr_bin_start_pos = snps[t]['position_bp']

        curr_state_calls = {contrib_ab_codes[t, curr_state[0]], contrib_ab_codes[t, curr_state[1]]}
        curr_sample_call = sample_ab_codes[t]

        if curr_sample_call != hhmm.N_CODE:
            if hhmm.N_CODE in curr_state_calls or hhmm.H_CODE in curr_state_calls:
                is_concordant = False
            elif len(curr_state_calls) == 2:
                is_concordant = curr_sample_call == hhmm.H_CODE
            else:
                assert len(curr_state_calls) == 1
                is_concordant = curr_sample_call == next(iter(curr_state_calls))

            curr_bin_informative += 1
            informative_count += 1
            if is_concordant:
                curr_bin_concordant += 1
                concordant_count += 1
            else:
                discordant_snp_indexes.append(t)

            if curr_bin_informative >= CONCORDANCE_BIN_SIZE:
                # TODO this start/end isn't consistent with how we're doing haplotype start/end
                concordance_bins.append({
                    'start_position_bp': curr_bin_start_pos,
                    'end_position_bp': snps[t]['position_bp'],
                    'informative_count': curr_bin_informative,
                    'concordant_count': curr_bin_concordant,
                })
                curr_bin_start_pos = -1
                curr_bin_informative = 0
                curr_bin_concordant = 0

    if curr_bin_informative > 0:
        # TODO maybe we should require a higher number of informative than 1?
        concordance_bins.append({
            'start_position_bp': curr_bin_start_pos,
            'end_position_bp': snps[-1]['position_bp'],
            'informative_count': curr_bin_informative,
            'concordant_count': curr_bin_concordant,
        })

    return {
        'informative_count': informative_count,
        'concordant_count': concordant_count,
        'discordant_snp_indexes': discordant_snp_indexes,
        'concordance_bins': concordance_bins,
    }


if __name__ == '__main__':
    # start server (for development use only)
    app.debug = True
    app.run(host='0.0.0.0')
