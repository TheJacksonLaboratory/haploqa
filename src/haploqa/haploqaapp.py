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
import sys
import tempfile
import uuid
from werkzeug.routing import BaseConverter
import datetime

from haploqa.config import HAPLOQA_CONFIG
import haploqa.gemminference as gemminf
import haploqa.haplohmm as hhmm
import haploqa.mongods as mds
import haploqa.finalreportimport as finalin
import haploqa.sampleannoimport as sai
import haploqa.usermanagement as usrmgmt

app = flask.Flask(__name__)
APP_VERSION = 0, 0
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
app.config.update(
    CELERY_BROKER_URL=BROKER_URL,
    CELERY_RESULT_BACKEND=BROKER_URL,
)
app.jinja_env.globals.update(isnan=math.isnan)


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


def unescape_forward_slashes(s):
    """
    Unescape forward slashes for our custom escape scheme where
    '/' escapes to '\f' and '\' escapes to '\b'.

    :param s: the escaped string
    :return: the unescaped string
    """
    return s.replace('\\f', '/').replace('\\b', '\\')


class EscForwardSlashConverter(BaseConverter):
    def to_python(self, value):
        return unescape_forward_slashes(BaseConverter.to_python(self, value))

    def to_url(self, value):
        return BaseConverter.to_url(self, escape_forward_slashes(value))


# Attaches the EscForwardSlashConverter to the given app
# with the typename "escfwd"
app.url_map.converters['escfwd'] = EscForwardSlashConverter


class CustomJSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        """Implement this method in a subclass such that it returns a
        serializable object for ``o``, or calls the base implementation (to
        raise a :exc:`TypeError`).

        This implementation supports ObjectId in addition to default values
        supported by flask
        """
        if isinstance(o, ObjectId):
            return str(o)
        return flask.json.JSONEncoder.default(self, o)


app.json_encoder = CustomJSONEncoder


# TODO this key must be changed to something secret (ie. not committed to the repo).
# Comment out the print message when this is done
print('===================================================')
print('THIS VERSION OF HaploQA IS NOT SECURE. YOU MUST    ')
print('REGENERATE THE SECRET KEY BEFORE DEPLOYMENT. SEE   ')
print('"How to generate good secret keys" AT			  ')
print('http://flask.pocoo.org/docs/quickstart/ FOR DETAILS')
print('===================================================')
app.secret_key = b'\x12}\x08\xfa\xbc\xaa6\x8b\xdd>%\x81`xk\x04\xb1\xdc\x8a0\xda\xa1\xab\x0f'


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


@app.context_processor
def inject_vars():
    """
    Inject variables to be available in all template contexts
    """
    return {
        'app_version': '.'.join([str(x) for x in APP_VERSION])
    }


MAX_CONTRIB_STRAIN_COUNT = 15


@app.template_global()
def maximum_contributing_strain_count():
    return MAX_CONTRIB_STRAIN_COUNT


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
    flask.session.permanent = True
    if not flask.request.path.startswith(app.static_url_path):
        # lookup the current user if the user_id is found in the session
        user_email_address = flask.session.get('user_email_address')
        if user_email_address:
            if flask.request.remote_addr == flask.session.get('remote_addr'):
                user = usrmgmt.lookup_user(user_email_address, mds.get_db())
                flask.g.user = user
                flask.session['admin'] = user['administrator']
            else:
                # If IP addresses don't match we're going to reset the session for
                # a bit of extra safety. Unfortunately this also means that we're
                # forcing valid users to log in again when they change networks
                _set_session_user(None)
        else:
            flask.g.user = None

@app.route('/show-users.html')
def show_users():
    '''
    show all users
    :return:
    '''

    users = usrmgmt.get_all_users()
    return flask.render_template(
        'show-users.html',
        users=users,
    )

@app.route('/switch-admin.json', methods=['POST'])
def switch_admin():
    """
    Promote a user to admin
    :return: True / False
    """
    user = flask.g.user
    if user['administrator'] is not True:
        flask.abort(400)

    form = flask.request.form
    if usrmgmt.switch_admin(form['email'], form['administrator']) is not None:
        return flask.jsonify({'success': True})
    else:
        return flask.jsonify({'success': False})

@app.route('/remove-user.json', methods=['POST'])
def remove_user():
    """
    remove a user
    :return: True / False
    """
    user = flask.g.user
    if user['administrator'] is not True:
        flask.abort(400)

    form = flask.request.form
    if usrmgmt.remove_user(form['email']) is not None:
        return flask.jsonify({'success': True})
    else:
        return flask.jsonify({'success': False})


@app.route('/invite-user.html', methods=['GET', 'POST'])
def invite_user_html():
    """
    Invite a new user to the application using their email address. Upon get
    the invite-user template is rendered. Upon successful POST the
    invite email is sent out and the browser is redirected to index.html
    """

    user = flask.g.user
    if user is None or not user['administrator']:
        return flask.render_template('login-required.html')
    else:
        if flask.request.method == 'GET':
            return flask.render_template('invite-user.html')
        elif flask.request.method == 'POST':
            form = flask.request.form
            if (usrmgmt.invite_user(form['email'], form['affiliation'])) is not None:
                return flask.render_template(
                    'invite-user.html',
                    msg='Your invite has been sent')
            else:
                return flask.render_template(
                    'invite-user.html',
                    msg='That user already exists, please try again')

@app.route('/reset-password.html', methods=['POST', 'GET'])
def reset_password_html():
    if flask.request.method == 'GET':
        return flask.render_template('reset-password.html')
    elif flask.request.method == 'POST':
        form = flask.request.form
        if usrmgmt.reset_password(form['email']) is not None:
            return flask.render_template(
                'reset-password.html',
                msg='An email has been sent to you with instructions for resetting your password')
        else:
            return flask.render_template('reset-password.html', msg="That email does not exist in the system")

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
        flask.session['admin'] = None
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
        if len(new_password) < HAPLOQA_CONFIG['MIN_PASSWORD_LENGTH']:
            flask.flash('The given password is too short. It must contain at least {} characters.'.format(
                HAPLOQA_CONFIG['MIN_PASSWORD_LENGTH']
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
            if len(new_password) < HAPLOQA_CONFIG['MIN_PASSWORD_LENGTH']:
                flask.flash('The given password is too short. It must contain at least {} characters.'.format(
                    HAPLOQA_CONFIG['MIN_PASSWORD_LENGTH']
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


@app.route('/users.html')
def users_html():
    user = flask.g.user
    if user is not None:
        db = mds.get_db()
        users = list(db.users.find({}, {'email_address': 1}))
        return flask.render_template('users.html', users=users)


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


@app.route('/sample-data-export.html')
def sample_data_export_html():
    db = mds.get_db()
    samples = _find_and_anno_samples(
        {},
        {
            'chromosome_data': 0,
            'unannotated_snps': 0,
            'viterbi_haplotypes.chromosome_data': 0,
            'contributing_strains': 0,
        },
        db=db,
        cursor_func=lambda c: c.sort('sample_id', pymongo.ASCENDING),
    )
    samples = list(samples)
    platform_ids = [x['platform_id'] for x in db.platforms.find({}, {'platform_id': 1})]
    all_tags = db.samples.distinct('tags')

    return flask.render_template(
            'sample-data-export.html',
            samples=samples,
            all_tags=all_tags,
            platform_ids=platform_ids,
    )


@app.route('/sample-data-export.txt', methods=['POST'])
def sample_data_export_file():
    db = mds.get_db()
    req_data_json_str = flask.request.form['download-request-json']
    req_data = json.loads(req_data_json_str)
    interval = None
    try:
        interval = req_data['interval']
    except KeyError:
        pass

    @flask.stream_with_context
    def response_gen():
        samples = []
        platform = None
        for mongo_id in req_data['selectedSampleIDs']:
            obj_id = ObjectId(mongo_id)
            curr_sample = _find_one_and_anno_samples({'_id': obj_id}, {}, db)
            for chr_val in curr_sample['chromosome_data'].values():
                curr_sample['uses_snp_format'] = 'snps' in chr_val
            samples.append(curr_sample)

            if platform is None:
                platform = db.platforms.find_one({'platform_id': curr_sample['platform_id']})

        # yield the header
        yield _iter_to_row(['snp_id', 'chromosome', 'position_bp'] + [curr_sample['sample_id'] for curr_sample in samples])

        chr_ids = platform['chromosomes']
        for chr_id in chr_ids:
            if (interval is None or interval['chr'] == chr_id) and any(chr_id in sample['chromosome_data'] for sample in samples):
                snps = list(mds.get_snps(platform['platform_id'], chr_id, db))
                for snp_index, curr_snp in enumerate(snps):
                    if interval is None or interval['startPos'] <= curr_snp['position_bp'] <= interval['endPos']:
                        snp_calls = []
                        for curr_sample in samples:
                            if curr_sample['uses_snp_format']:
                                snp_calls.append(curr_sample['chromosome_data'][chr_id]['snps'][snp_index])
                            else:
                                curr_call = (
                                    curr_sample['chromosome_data'][chr_id]['allele1_fwds'][snp_index] +
                                    curr_sample['chromosome_data'][chr_id]['allele2_fwds'][snp_index]
                                )
                                snp_calls.append(curr_call)

                        yield _iter_to_row([curr_snp['snp_id'], curr_snp['chromosome'], str(curr_snp['position_bp'])] + snp_calls)

    resp = flask.Response(response_gen(), mimetype='text/plain')
    resp.headers['Content-Disposition'] = 'attachment; filename="sample-data-export.txt"'

    return resp

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
            if (files['sample-map-file'].filename == '') or (files['final-report-file'].filename == ''):
                return flask.render_template('sample-data-import.html', platform_ids=platform_ids,
                                             msg='Error: you must provide both files in order to process your request')
            else:
                sample_map_filename = _unique_temp_filename()
                files['sample-map-file'].save(sample_map_filename)

                final_report_filename = _unique_temp_filename()
                final_report_file = files['final-report-file']
                final_report_file.save(final_report_filename)

                generate_ids = HAPLOQA_CONFIG['GENERATE_IDS_DEFAULT']
                on_duplicate = HAPLOQA_CONFIG['ON_DUPLICATE_ID_DEFAULT']

                user_email = flask.g.user['email_address'].strip().lower()

                sample_group_name = os.path.splitext(final_report_file.filename)[0]
                import_task = sample_data_import_task.delay(
                    user_email,
                    generate_ids,
                    on_duplicate,
                    final_report_filename,
                    sample_map_filename,
                    platform_id,
                    sample_group_name,
                )

                # perform a 303 redirect to the URL that uniquely identifies this run
                new_location = flask.url_for('sample_import_status_html', task_id=import_task.task_id)
                return flask.redirect(new_location, 303)
        else:
            return flask.render_template('sample-data-import.html', platform_ids=platform_ids)


@celery.task(name='sample_data_import_task')
def sample_data_import_task(user_email, generate_ids, on_duplicate, final_report_filename, sample_map_filename, platform_id, sample_group_name):
    """
    Our long-running import task, triggered from the import page of the app
    """
    try:
        db = mds.get_db()
        tags = [sample_group_name, platform_id]
        sample_anno_dicts = sai.sample_anno_dicts(sample_map_filename) if sample_map_filename else dict()
        finalin.import_final_report(user_email, generate_ids, on_duplicate, final_report_filename, sample_anno_dicts, platform_id, tags, db)
    finally:
        # we don't need the files after the import is complete
        try:
            if sample_map_filename is not None and os.path.isfile(sample_map_filename):
                os.remove(sample_map_filename)
        finally:
            if os.path.isfile(final_report_filename):
                os.remove(final_report_filename)

    return sample_group_name


#####################################################################
# SAMPLE LISTING PAGES
#####################################################################

def _get_strain_map(db):
    return {
        x['standard_designation']: {
            'color': x['color'],
            'url': flask.url_for('standard_designation_html', standard_designation=x['standard_designation']),
        }
        for x in db.standard_designations.find({})
    }


@app.route('/all-samples.html')
def all_samples_html():
    # look up all samples. Only return top level information though (snp-level data is too much)
    db = mds.get_db()
    samples = _find_and_anno_samples(
        {},
        {
            'chromosome_data': 0,
            'unannotated_snps': 0,
            'viterbi_haplotypes.chromosome_data': 0,
            'contributing_strains': 0,
        },
        db=db,
        cursor_func=lambda c: c.sort('sample_id', pymongo.ASCENDING),
    )
    samples = list(samples)
    all_tags = db.samples.distinct('tags')

    return flask.render_template(
            'samples.html',
            samples=samples,
            strain_colors=_get_strain_map(db),
            all_tags=all_tags,
    )


@app.route('/tag/<escfwd:tag_id>.html')
def sample_tag_html(tag_id):

    # look up all samples with this tag ID. Only return top level information though
    # (snp-level data is too much)
    db = mds.get_db()
    matching_samples = _find_and_anno_samples(
        {'tags': tag_id},
        {
            'chromosome_data': 0,
            'unannotated_snps': 0,
            'viterbi_haplotypes.chromosome_data': 0,
            'contributing_strains': 0,
        },
        db=db,
        cursor_func=lambda c: c.sort('sample_id', pymongo.ASCENDING),
    )
    matching_samples = list(matching_samples)
    all_tags = db.samples.distinct('tags')

    return flask.render_template(
            'sample-tag.html',
            samples=matching_samples,
            strain_colors=_get_strain_map(db),
            all_tags=all_tags,
            tag_id=tag_id)


@app.route('/standard-designation/<escfwd:standard_designation>.html')
def standard_designation_html(standard_designation):
    # look up all samples with this standard_designation. Only return top level information though
    # (snp-level data is too much)
    db = mds.get_db()
    matching_samples = _find_and_anno_samples(
        {'standard_designation': standard_designation},
        {
            'chromosome_data': 0,
            'unannotated_snps': 0,
            'viterbi_haplotypes.chromosome_data': 0,
            'contributing_strains': 0,
        },
        db=db,
        cursor_func=lambda c: c.sort('sample_id', pymongo.ASCENDING),
    )
    matching_samples = list(matching_samples)
    all_tags = db.samples.distinct('tags')

    return flask.render_template(
            'standard-designation.html',
            samples=matching_samples,
            strain_colors=_get_strain_map(db),
            all_tags=all_tags,
            standard_designation=standard_designation)


@app.route('/search')
def search_html():

    search_text = flask.request.args['search-text']

    # look up all samples with this search term. Only return top level information though
    # (snp-level data is too much)
    db = mds.get_db()
    matching_samples = _find_and_anno_samples(
        {'$text': {'$search': search_text}},
        {
            'chromosome_data': 0,
            'unannotated_snps': 0,
            'viterbi_haplotypes.chromosome_data': 0,
            'contributing_strains': 0,
        },
        db=db,
    )
    matching_samples = list(matching_samples)
    all_tags = db.samples.distinct('tags')

    return flask.render_template(
            'search.html',
            samples=matching_samples,
            strain_colors=_get_strain_map(db),
            all_tags=all_tags,
            search_text=search_text)


#####################################################################
# index.html AND SEVERAL OTHER GENERAL INFORMATIVE TEMPLATES
#####################################################################


@app.route('/index.html')
@app.route('/')
def index_html():
    user = flask.g.user
    db = mds.get_db()

    # this pipeline should get us all tags along with their sample counts
    pipeline = [
        {'$unwind': '$tags'},
        {'$group': {'_id': '$tags', 'count': {'$sum': 1}}},
        {'$sort': SON([('count', -1), ('_id', -1)])},
    ]
    if user is None:
        # anonymous users should only be given access to public samples
        pipeline.insert(0, {'$match': {'is_public': True}})
        sample_count = db.samples.count({'is_public': True})
    else:
        sample_count = db.samples.count({})

    tags = db.samples.aggregate(pipeline)
    tags = [{'name': tag['_id'], 'sample_count': tag['count']} for tag in tags]

    return flask.render_template('index.html', tags=tags, total_sample_count=sample_count)


@app.route('/contact.html')
def contact_html():
    return flask.render_template('contact.html')


@app.route('/help.html')
def help_html():
    return flask.render_template('help.html')


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

    def default_to(property, default_val):
        if property not in sample:
            sample[property] = default_val

    default_to('color', '#000000')
    default_to('standard_designation', None)
    default_to('notes', None)
    default_to('owner', None)
    default_to('write_groups', [])
    default_to('is_public', False)
    default_to('sex', 'unknown')
    default_to('pos_ctrl_eng_tgts', [])
    default_to('neg_ctrl_eng_tgts', [])
    default_to('haplotype_candidate', False)


def _find_and_anno_samples(query, projection, db=None, require_write_perms=False, cursor_func=None):
    """
    This function is basically performing the sample find operation specified by the
    query and projection but it is performing the find in such a way that it only
    returns samples that the user has sufficient permissions for. This encapsulates
    sample access security in a single function.

    :param query: the query to supply to the find function (the actual query performed will
                  be more complex to account for security concerns)
    :param projection: the projection to supply to the find function
    :param db: the mongo database (we'll use mds.get_db() if this value is not supplied)
    :param require_write_perms:
            if true we will filter out any samples for which the user
            only has read permissions
    :param cursor_func:
            a function that takes a cursor as it's only parameter and returns a compatible
            cursor. This allows a sort to be applied for example
    :return: an iterable containing the samples from mongo
    """

    if db is None:
        db = mds.get_db()

    user = flask.g.user
    user_mongoid = None if user is None else user['_id']

    def anno_sample(sample):
        sample['user_can_write'] = user is not None
        if user is None and 'is_public' not in sample:
            sample['is_public'] = True
        _add_default_attributes(sample)

        sample['user_is_owner'] = user_mongoid is not None and user_mongoid == sample['owner']

        return sample

    if user is None:
        if require_write_perms:
            # anonymous users don't have write access to anything
            return []
        else:
            # since this is anonymous access only return publicly visible samples
            query = {
                '$and': [
                    {'is_public': True},
                    query,
                ]
            }

    if projection:
        cursor = db.samples.find(query, projection)
    else:
        cursor = db.samples.find(query)
    if cursor_func:
        cursor = cursor_func(cursor)

    return map(anno_sample, cursor)


def _find_one_and_anno_samples(query, projection, db=None, require_write_perms=False, cursor_func=None):
    """
    parameters work the same as in _find_and_anno_samples.
    :return: if any samples are found the 1st is returned, otherwise None is returned
    """
    samples = _find_and_anno_samples(query, projection, db, require_write_perms, cursor_func)
    try:
        return next(iter(samples))
    except StopIteration:
        return None


@app.route('/sample/<mongo_id>.html')
def sample_html(mongo_id):
    """
    Render the HTML template for the sample
    :param mongo_id: the mongo ID string for the sample we're interested in
    :return: the Flask response for the template
    """

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = _find_one_and_anno_samples(
        {'_id': obj_id},
        {'chromosome_data': 0, 'unannotated_snps': 0, 'viterbi_haplotypes': 0, 'haplotype_inference_uuid': 0},
        db
    )
    if sample is None:
        return flask.render_template('login-required.html')

    all_tags = db.samples.distinct('tags')
    all_eng_tgts = db.snps.distinct('engineered_target', {'platform_id': sample['platform_id']})

    return flask.render_template(
        'sample.html',
        sample=sample,
        all_tags=all_tags,
        all_eng_tgts=all_eng_tgts,
        strain_map=_get_strain_map(db),
    )


def _iter_to_row(iterable):
    return '\t'.join(iterable) + '\n'


@app.route('/sample/<mongo_id>-snp-report.txt')
def sample_snp_report(mongo_id):
    """
    tab-delimited row-per-SNP report for the sample
    :param mongo_id: the mongo ID string for the sample we're interested in
    :return: the Flask response
    """

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = _find_one_and_anno_samples({'_id': obj_id}, {}, db)
    if sample is None:
        flask.abort(400)
    sample_uses_snp_format = False
    for chr_val in sample['chromosome_data'].values():
        sample_uses_snp_format = 'snps' in chr_val

    contributing_strains = sample['contributing_strains']

    def tsv_generator():
        # generate a header 1st
        if sample_uses_snp_format:
            yield _iter_to_row((
                'sample_id',
                'snp_id',
                'chromosome',
                'position_bp',
                'snp_call',
                'haplotype1',
                'haplotype2',
            ))
        else:
            yield _iter_to_row((
                'sample_id',
                'snp_id',
                'chromosome',
                'position_bp',
                'allele1_fwd',
                'allele2_fwd',
                'haplotype1',
                'haplotype2',
            ))

        platform = db.platforms.find_one({'platform_id': sample['platform_id']})
        chr_ids = platform['chromosomes']
        for chr_id in chr_ids:
            if chr_id in sample['chromosome_data']:
                snps = list(mds.get_snps(sample['platform_id'], chr_id, db))
                try:
                    haplotype_blocks = sample['viterbi_haplotypes']['chromosome_data'][chr_id]['haplotype_blocks']
                except KeyError:
                    haplotype_blocks = []

                hap_block_index = 0
                for snp_index, curr_snp in enumerate(snps):
                    snp_hap_block = None
                    for hap_block_index in range(hap_block_index, len(haplotype_blocks)):
                        curr_hap_block = haplotype_blocks[hap_block_index]
                        if curr_hap_block['end_position_bp'] >= curr_snp['position_bp']:
                            if curr_hap_block['start_position_bp'] <= curr_snp['position_bp']:
                                snp_hap_block = curr_hap_block
                            break

                    if sample_uses_snp_format:
                        yield _iter_to_row((
                            sample['sample_id'],
                            curr_snp['snp_id'],
                            curr_snp['chromosome'],
                            str(curr_snp['position_bp']),
                            sample['chromosome_data'][chr_id]['snps'][snp_index],
                            '' if snp_hap_block is None else contributing_strains[snp_hap_block['haplotype_index_1']],
                            '' if snp_hap_block is None else contributing_strains[snp_hap_block['haplotype_index_2']],
                        ))
                    else:
                        yield _iter_to_row((
                            sample['sample_id'],
                            curr_snp['snp_id'],
                            curr_snp['chromosome'],
                            str(curr_snp['position_bp']),
                            sample['chromosome_data'][chr_id]['allele1_fwds'][snp_index],
                            sample['chromosome_data'][chr_id]['allele2_fwds'][snp_index],
                            '' if snp_hap_block is None else contributing_strains[snp_hap_block['haplotype_index_1']],
                            '' if snp_hap_block is None else contributing_strains[snp_hap_block['haplotype_index_2']],
                        ))

    return flask.Response(tsv_generator(), mimetype='text/tab-separated-values')

@app.route('/combined-report/<escfwd:sdid>_summary_report.txt')
def combined_report(sdid):
    '''
    generate an aggregated composition report based on all samples
    under a standard designation.
    :param sdid: standard designation id
    :return: summary report in .txt format
    '''
    # look up all samples with this standard_designation. Only return top level information though
    # (snp-level data is too much)
    # TODO: this runs very quickly, but we only really need the sample ids returned ideally.
    # would need a new function
    db = mds.get_db()
    matching_samples = _find_and_anno_samples(
        {'standard_designation': sdid},
        {
            'chromosome_data': 0,
            'unannotated_snps': 0,
            'viterbi_haplotypes.chromosome_data': 0,
            'contributing_strains': 0,
        },
        db=db,
        cursor_func=lambda c: c.sort('sample_id', pymongo.ASCENDING),
    )

    samples = list(matching_samples)
    # header
    report = _iter_to_row(('sample_id', 'haplotype_1', 'haplotype_2', 'percent_of_genome'))
    for sample in samples:
        id = str(sample['_id'])
        # TODO: check if the report is empty and add a message
        report += _summary_report_data(id)

    return flask.Response(report, mimetype='text/tab-separated-values')


def _summary_report_data(mongo_id):
    """
    tab-delimited report for the sample showing parental strain composition (by percent)
    :param mongo_id: the mongo ID string for the sample we're interested in
    :return: the Flask response
    """

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = _find_one_and_anno_samples({'_id': obj_id}, {}, db)
    # TODO: do a clean error here
    if sample is None:
        flask.abort(400)

    contributing_strains = sample['contributing_strains']
    # get every possible sample ID combination (where order doesn't matter) and initialize distances to 0
    total_distance = 0
    cumulative_distance_dict = dict()
    for hap_index_lte in range(len(contributing_strains)):
        for hap_index_gte in range(hap_index_lte, len(contributing_strains)):
            cumulative_distance_dict[(hap_index_lte, hap_index_gte)] = 0

    # iterate through all of the haplotype blocks and accumulate distances
    try:
        chr_ids = sample['viterbi_haplotypes']['chromosome_data'].keys()
    except KeyError:
        chr_ids = []

    for chr_id in chr_ids:
        try:
            haplotype_blocks = sample['viterbi_haplotypes']['chromosome_data'][chr_id]['haplotype_blocks']
        except KeyError:
            haplotype_blocks = []

        for curr_block in haplotype_blocks:
            curr_dist = 1 + curr_block['end_position_bp'] - curr_block['start_position_bp']
            total_distance += curr_dist

            hap_index_1 = curr_block['haplotype_index_1']
            hap_index_2 = curr_block['haplotype_index_2']
            hap_index_lte = min(hap_index_1, hap_index_2)
            hap_index_gte = max(hap_index_1, hap_index_2)
            cumulative_distance_dict[(hap_index_lte, hap_index_gte)] += curr_dist

    def tsv_generator():
        for hap_index_lte in range(len(contributing_strains)):
            for hap_index_gte in range(hap_index_lte, len(contributing_strains)):
                curr_hap_distance = cumulative_distance_dict[(hap_index_lte, hap_index_gte)]
                if curr_hap_distance:
                    yield _iter_to_row((
                        sample['sample_id'],
                        contributing_strains[hap_index_lte],
                        contributing_strains[hap_index_gte],
                        str(100 * curr_hap_distance / total_distance),
                    ))

    data = tsv_generator()

    report = ""
    for row in data:
        report += row
    return report

@app.route('/sample/<mongo_id>-summary-report.txt')
def sample_summary_report(mongo_id):
    """
    tab-delimited report for the sample showing parental strain composition (by percent)
    :param mongo_id: the mongo ID string for the sample we're interested in
    :return: the Flask response
    """

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = _find_one_and_anno_samples({'_id': obj_id}, {}, db)
    if sample is None:
        flask.abort(400)

    contributing_strains = sample['contributing_strains']

    # get every possible sample ID combination (where order doesn't matter) and initialize distances to 0
    total_distance = 0
    cumulative_distance_dict = dict()
    for hap_index_lte in range(len(contributing_strains)):
        for hap_index_gte in range(hap_index_lte, len(contributing_strains)):
            cumulative_distance_dict[(hap_index_lte, hap_index_gte)] = 0

    # iterate through all of the haplotype blocks and accumulate distances
    try:
        chr_ids = sample['viterbi_haplotypes']['chromosome_data'].keys()
    except KeyError:
        chr_ids = []

    for chr_id in chr_ids:
        try:
            haplotype_blocks = sample['viterbi_haplotypes']['chromosome_data'][chr_id]['haplotype_blocks']
        except KeyError:
            haplotype_blocks = []

        for curr_block in haplotype_blocks:
            curr_dist = 1 + curr_block['end_position_bp'] - curr_block['start_position_bp']
            total_distance += curr_dist

            hap_index_1 = curr_block['haplotype_index_1']
            hap_index_2 = curr_block['haplotype_index_2']
            hap_index_lte = min(hap_index_1, hap_index_2)
            hap_index_gte = max(hap_index_1, hap_index_2)
            cumulative_distance_dict[(hap_index_lte, hap_index_gte)] += curr_dist

    def tsv_generator():
        yield _iter_to_row(('sample_id', 'haplotype_1', 'haplotype_2', 'percent_of_genome'))
        for hap_index_lte in range(len(contributing_strains)):
            for hap_index_gte in range(hap_index_lte, len(contributing_strains)):
                curr_hap_distance = cumulative_distance_dict[(hap_index_lte, hap_index_gte)]
                if curr_hap_distance:
                    yield _iter_to_row((
                        sample['sample_id'],
                        contributing_strains[hap_index_lte],
                        contributing_strains[hap_index_gte],
                        str(100 * curr_hap_distance / total_distance),
                    ))

    return flask.Response(tsv_generator(), mimetype='text/tab-separated-values')


@app.route('/sample/<mongo_id>.json', methods=['POST'])
def update_sample(mongo_id):
    """
    Accepts a POST to update the sample identified by the given mongo_id string
    """

    if not flask.g.user:
        flask.abort(401)

    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = _find_one_and_anno_samples(
            {'_id': obj_id},
            {'platform_id': 1, 'sex': 1},
            db=db,
            require_write_perms=True)
    if sample is None:
        # either the sample does not exist or the user has no permissions to it
        flask.abort(400)

    task_ids = []

    form = flask.request.form
    update_dict = dict()

    ts = '{:%m/%d/%Y %H:%M %p}'.format(datetime.datetime.now())
    update_dict['last_update'] = ts
    update_dict['updated_by'] = flask.g.user['email_address']

    if 'sample_id' in form:
        update_dict['sample_id'] = form['sample_id'].strip()

    if 'owner' in form:
        update_dict['owner'] = form['owner'].strip()

    if 'tags' in form:
        update_dict['tags'] = json.loads(form['tags'])

    if 'color' in form:
        update_dict['color'] = form['color'].strip()

    if 'standard_designation' in form:
        update_dict['standard_designation'] = form['standard_designation'].strip()

    if 'notes' in form:
        update_dict['notes'] = form['notes'].strip()

    if 'is_public' in form:
        update_dict['is_public'] = form['is_public'] == 'true'

    if 'sex' in form:
        update_dict['sex'] = form['sex']

    if 'pos_ctrl_eng_tgts' in form:
        update_dict['pos_ctrl_eng_tgts'] = json.loads(form['pos_ctrl_eng_tgts'])

    if 'neg_ctrl_eng_tgts' in form:
        update_dict['neg_ctrl_eng_tgts'] = json.loads(form['neg_ctrl_eng_tgts'])

    if 'contributing_strains' in form or 'sex' in form:
        platform = db.platforms.find_one({'platform_id': sample['platform_id']})
        chr_ids = platform['chromosomes']

        if 'contributing_strains' in form:
            update_dict['contributing_strains'] = json.loads(form['contributing_strains'])

        # we invalidate any existing haplotypes before calculating new haplotypes
        haplotype_inference_uuid = str(uuid.uuid4())
        update_dict['haplotype_inference_uuid'] = haplotype_inference_uuid
        for chr_id in chr_ids:
            update_dict['viterbi_haplotypes.chromosome_data.' + chr_id] = {
                'results_pending': True
            }

        update_dict['viterbi_haplotypes.informative_count'] = 0
        update_dict['viterbi_haplotypes.concordant_count'] = 0
        db.samples.update_one({'_id': obj_id}, {'$set': update_dict})

        # since we invalidated haplotypes lets kick off tasks to recalculate
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


@app.route('/update-samples.json', methods=['POST'])
def update_samples():
    """
    Accepts a POST to update the sample identified by the given mongo_id string
    """

    if not flask.g.user:
        flask.abort(401)

    db = mds.get_db()

    # extract form parameters
    form = flask.request.form
    sample_ids_to_update = [ObjectId(x) for x in json.loads(form['samples_to_update'])]
    tags = json.loads(form['tags'])
    tags_action = form['tags_action']
    contributing_strains = json.loads(form['contributing_strains'])
    contributing_strains_action = form['contributing_strains_action']
    sample_visibility_action = form['sample_visibility']

    if not sample_ids_to_update:
        # there's nothing to do
        return flask.jsonify(task_ids=[])

    add_to_set_dict = dict()
    remove_dict = dict()
    set_dict = dict()

    def save_updates():
        update_dict = dict()
        if add_to_set_dict:
            update_dict['$addToSet'] = add_to_set_dict
        if remove_dict:
            update_dict['$pullAll'] = remove_dict
        if set_dict:
            update_dict['$set'] = set_dict

        db.samples.update_many({'_id': {'$in': sample_ids_to_update}}, update_dict)

    if sample_visibility_action == 'public':
        set_dict['is_public'] = True
    elif sample_visibility_action == 'private':
        set_dict['is_public'] = False

    tag_change = tags or tags_action == 'set'
    if tag_change:
        if tags_action == 'add':
            add_to_set_dict['tags'] = {
                '$each': tags
            }
        elif tags_action == 'remove':
            remove_dict['tags'] = tags
        elif tags_action == 'set':
            set_dict['tags'] = tags

    chr_ids = set()
    platform_ids = db.samples.distinct('platform_id', {'_id': {'$in': sample_ids_to_update}})
    for curr_platform in db.platforms.find({'platform_id': {'$in': platform_ids}}):
        chr_ids |= set(curr_platform['chromosomes'])

    task_ids = []
    contributing_strains_change = contributing_strains or contributing_strains_action == 'set'
    if contributing_strains_change:
        if contributing_strains_action == 'add':
            add_to_set_dict['contributing_strains'] = {
                '$each': contributing_strains
            }
        elif contributing_strains_action == 'remove':
            remove_dict['contributing_strains'] = contributing_strains
        elif contributing_strains_action == 'set':
            set_dict['contributing_strains'] = contributing_strains

        haplotype_inference_uuid = str(uuid.uuid4())
        set_dict['haplotype_inference_uuid'] = haplotype_inference_uuid
        for chr_id in chr_ids:
            set_dict['viterbi_haplotypes.chromosome_data.' + chr_id] = {'results_pending': True}
        set_dict['viterbi_haplotypes.informative_count'] = 0
        set_dict['viterbi_haplotypes.concordant_count'] = 0
        save_updates()

        for sample_id in sample_ids_to_update:
            sample_obj_id = str(sample_id)
            for chr_id in chr_ids:
                t = infer_haplotype_structure_task.delay(
                    sample_obj_id,
                    chr_id,
                    haplotype_inference_uuid,
                )
                task_ids.append(t.task_id)
    else:
        save_updates()

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
        {'platform_id': 1}
    )
    if sample is None:
        flask.abort(400)

    # calculate which SNPs fall within the interval of interest
    snps = list(mds.get_snps(sample['platform_id'], chr_id, db))
    snp_positions = [x['position_bp'] for x in snps]
    left_index = bisect_left(snp_positions, start_pos_bp)
    right_index = bisect_right(snp_positions, end_pos_bp, left_index)
    snps = snps[left_index:right_index]

    def slice_snps(sample_to_slice):
        try:
            chr_data = sample_to_slice['chromosome_data'][chr_id]
            try:
                chr_data['allele1_fwds'] = chr_data['allele1_fwds'][left_index:right_index]
            except KeyError:
                pass

            try:
                chr_data['allele2_fwds'] = chr_data['allele2_fwds'][left_index:right_index]
            except KeyError:
                pass

            try:
                chr_data['snps'] = chr_data['snps'][left_index:right_index]
            except KeyError:
                pass

        except KeyError:
            pass

    best_candidates = []
    if snps:
        # get sliced versions of our main sample and the haplotype samples
        sample = _find_one_and_anno_samples(
            {'_id': obj_id},
            {
                'sample_id': 1,
                'platform_id': 1,
                'chromosome_data.' + chr_id + '.allele1_fwds': 1,
                'chromosome_data.' + chr_id + '.allele2_fwds': 1,
                'chromosome_data.' + chr_id + '.snps': 1,
            },
            db=db,
        )
        if sample is None:
            flask.abort(400)
        slice_snps(sample)
        sample_ab = hhmm.samples_to_ab_codes([sample], chr_id, snps)

        haplotype_samples = list(_find_and_anno_samples(
            {
                '_id': {'$ne': obj_id},
                'haplotype_candidate': True,
                'platform_id': sample['platform_id']
            },
            {
                'sample_id': 1,
                'standard_designation': 1,
                'color': 1,
                'chromosome_data.' + chr_id + '.allele1_fwds': 1,
                'chromosome_data.' + chr_id + '.allele2_fwds': 1,
                'chromosome_data.' + chr_id + '.snps': 1,
            },
            db=db,
        ))
        for curr_hap_sample in haplotype_samples:
            slice_snps(curr_hap_sample)
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
            best_candidates.append({
                'haplotype_1': haplotype_samples[i]['standard_designation'],
                'haplotype_2': haplotype_samples[j]['standard_designation'],
                'neg_log_likelihood': -curr_loglikelihood,
            })

    return flask.jsonify(best_candidates=best_candidates)


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
    sample = _find_one_and_anno_samples({'_id': obj_id}, {'viterbi_haplotypes': 1, 'contributing_strains': 1}, db=db)
    if sample is None:
        flask.abort(400)

    return flask.jsonify(
        viterbi_haplotypes=sample['viterbi_haplotypes'],
        contributing_strains=sample['contributing_strains'],
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
            'sample_id': 1,
            'contributing_strains': 1,
            'platform_id': 1,
            'chromosome_data.' + chr_id: 1,
            'sex': 1,
        })
    if sample is None:
        # nothing to do if we can't find the sample (or if the UUID has changed)
        return

    platform_id = sample['platform_id']
    platform_obj = db.platforms.find_one({'platform_id': platform_id})
    platform_chrs = set(platform_obj['chromosomes'])
    if ((chr_id == 'Y' and sample.get('sex', None) == 'female')
                or not sample['contributing_strains']
                or chr_id not in platform_chrs):
        # if the above condition is met we're just going to delete and skip past this chromosome
        db.samples.update_one(
            {
                # TODO add an index for this
                '_id': sample_obj_id,
                'haplotype_inference_uuid': haplotype_inference_uuid,
            },
            {
                '$unset': {'viterbi_haplotypes.chromosome_data.' + chr_id: ''},
            },
        )

    else:
        snps = list(mds.get_snps(platform_id, chr_id, db))
        contrib_strains = [
            db.samples.find_one(
                {
                    'haplotype_candidate': True,
                    'standard_designation': strain_name,
                    'platform_id': platform_id,
                },
                {'sample_id': 1, 'chromosome_data.' + chr_id: 1})
            for strain_name in sample['contributing_strains']
        ]
        if None in contrib_strains:
            for i, strain in enumerate(contrib_strains):
                if strain is None:
                    strain_name = sample['contributing_strains'][i]
                    print(
                        'Calculating diplotypes for sample "{}", chr "{}". '
                        'Failed to find candidate haplotype strain "{}" for platform "{}".'.format(
                            sample['sample_id'],
                            chr_id,
                            strain_name,
                            platform_id),
                        file=sys.stderr)
        else:
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


#####################################################################
# GEMM FUNCTIONS
#####################################################################


@app.route('/sample/<mongo_id>/gemm-probs.json')
def gemm_probs_json(mongo_id):
    """
    :param mongo_id: the mongo ID string
    :return: the GEMM probability dictionary
    """
    user = flask.g.user
    if user is None:
        response = flask.jsonify({'success': False})
        response.status_code = 400

        return response
    else:
        obj_id = ObjectId(mongo_id)
        gemm_probs = gemminf.est_gemm_probs([obj_id])

        # clean it up a bit for JSON. Turn it into a list of tuples
        # sorted from highest probability to lowest
        gemm_probs = [
            (tgt, val if np.isfinite(val) else None)
            for (tgt, [val]) in gemm_probs.items()
        ]
        gemm_probs.sort(key=lambda x: -1 if x[1] is None else x[1], reverse=True)

        return flask.jsonify(gemm_probs=gemm_probs)


@app.route('/sample/<mongo_id>/gemm-intens.json')
def gemm_intens_json(mongo_id):
    """
    :param mongo_id: the mongo ID string
    :return: the GEMM probability dictionary
    """
    user = flask.g.user
    if user is None:
        response = flask.jsonify({'success': False})
        response.status_code = 400

        return response
    else:
        obj_id = ObjectId(mongo_id)
        gemm_intens = gemminf.get_gemm_intens([obj_id])

        return flask.jsonify(gemm_intens=gemm_intens)


@app.route('/sample/<mongo_id>/gemm-intens.html')
def gemm_intens_html(mongo_id):
    """
    :param mongo_id: the mongo ID string
    :return: the GEMM probability dictionary
    """
    user = flask.g.user
    if user is None:
        return None
    else:
        obj_id = ObjectId(mongo_id)
        db = mds.get_db()
        sample = db.samples.find_one(
            {
                # TODO add an index for this
                '_id': obj_id,
            },
            {
                'sample_id': 1,
                'platform_id': 1,
                'sex': 1,
            })
        if sample is None:
            # nothing to do if we can't find the sample (or if the UUID has changed)
            return

        gemm_intens = gemminf.get_gemm_intens([obj_id], db=db)

        return flask.render_template('gemm-intens.html', sample=sample, gemm_intens=gemm_intens)


#####################################################################
# UNIQUE IDs
#####################################################################


@app.route('/generate-unique-ids.html', methods=['GET', 'POST'])
def generate_unique_ids():
    user = flask.g.user
    if user is None:
        return None
    else:
        num_ids = 1
        id_prefix = ''
        unique_ids = []
        if flask.request.method == 'POST':
            db = mds.get_db()
            form = flask.request.form
            num_ids = int(form['num-ids'])
            id_prefix = form['id-prefix']
            unique_ids = [mds.gen_unique_id(db) for _ in range(num_ids)]
            if id_prefix:
                unique_ids = [id_prefix + ':' + x for x in unique_ids]

        return flask.render_template(
            'generate-unique-ids.html',
            num_ids=num_ids,
            id_prefix=id_prefix,
            unique_ids=unique_ids,
        )


#####################################################################
# GENOTYPE PROBABILITIES
#####################################################################


def max_likelihood_genoprobs(sample_id, db=None):

    if db is None:
        db = mds.get_db()

    diplo_prob_platform = db.diplotype_probabilities.find_one({'sample_id': sample_id}, {'platform_id': 1})

    if diplo_prob_platform is not None:
        platform_obj = db.platforms.find_one({'platform_id': diplo_prob_platform['platform_id']})
        if platform_obj is None:
            raise Exception('failed to find a platform named "{}".'.format(diplo_prob_platform['platform_id']))
        platform_chrs = platform_obj['chromosomes']
        for chrom in platform_chrs:
            max_likelihood_chr_genoprobs(sample_id, chrom, db)


def max_likelihood_chr_genoprobs(sample_id, chrom, db):
    print('======', chrom, '=======')
    ml_diplotype_indices = []
    ml_positions_bp = []
    sample_genoprob = db.diplotype_probabilities.find_one({'sample_id': sample_id, 'chromosome': chrom})
    if sample_genoprob:
        snps = list(mds.get_snps(sample_genoprob['platform_id'], sample_genoprob['chromosome']))
        if snps:
            diplo_strains = sample_genoprob['diplotype_strains']
            diplo_genoprobs = sample_genoprob['diplotype_probabilities']
            prev_start_pos_bp = snps[0]['position_bp']
            prev_max_likelihood_diplo = np.argmax(diplo_genoprobs[0])
            ml_diplotype_indices.append(prev_max_likelihood_diplo)
            ml_positions_bp.append(prev_start_pos_bp)
            i = 0

            for i, snp_genoprobs in enumerate(diplo_genoprobs):
                curr_max_likelihood_diplo = np.argmax(snp_genoprobs)
                if curr_max_likelihood_diplo != prev_max_likelihood_diplo and not math.isnan(snp_genoprobs[curr_max_likelihood_diplo]):
                    # since we don't know exactly where the maximum likelihood diplotype has changed we'll choose a
                    # point half way between the previous and current position
                    ml_diplotype_indices.append(curr_max_likelihood_diplo)
                    ml_positions_bp.append((snps[i - 1]['position_bp'] + snps[i]['position_bp']) / 2.0)
                    prev_max_likelihood_diplo = curr_max_likelihood_diplo

            ml_positions_bp.append(snps[i]['position_bp'])
            ml_diplotypes = [diplo_strains[i] for i in ml_diplotype_indices]

            print(ml_positions_bp)
            print(ml_diplotypes)


if __name__ == '__main__':
    # start server (for development use only)
    app.debug = True
    app.run(host='0.0.0.0')
