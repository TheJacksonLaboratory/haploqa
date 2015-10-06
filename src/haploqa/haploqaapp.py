from bson.objectid import ObjectId
from celery import Celery
import flask
import json
import math
import numpy as np
import os
import tempfile
import uuid

import haploqa.haplohmm as hhmm
import haploqa.mongods as mds
import haploqa.finalreportimport as finalin

app = flask.Flask(__name__)
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
app.config.update(
    CELERY_BROKER_URL=BROKER_URL,
    CELERY_RESULT_BACKEND=BROKER_URL,
)
app.jinja_env.globals.update(isnan=math.isnan)


def _unique_temp_filename():
    return os.path.join(tempfile.tempdir, str(uuid.uuid4()))


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


@app.route('/sample-import-status/<task_id>.html')
def sample_import_status_html(task_id):
    return flask.render_template('import-status.html', task_id=task_id)


@app.route('/sample-import-status/<task_id>.json')
def sample_import_status_json(task_id):
    async_result = sample_data_import_task.AsyncResult(task_id)

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

        # render the status page and perform a 303 redirect to the
        # URL that uniquely identifies this run
        response = flask.make_response(
            flask.render_template('import-status.html', task_id=import_task.task_id))
        response.status_code = 303
        new_location = flask.url_for('sample_import_status_html', task_id=import_task.task_id)
        response.headers['location'] = new_location

        return response
    else:
        return flask.render_template('sample-data-import.html', platform_ids=platform_ids)


def _unescape_forward_slashes(s):
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


def _add_call_percents(sample):
    total_count = sample['heterozygous_count'] + \
                  sample['homozygous_count'] + \
                  sample['no_read_count']
    sample['heterozygous_percent'] = sample['heterozygous_count'] * 100.0 / total_count
    sample['homozygous_percent'] = sample['homozygous_count'] * 100.0 / total_count
    sample['no_read_percent'] = sample['no_read_count'] * 100.0 / total_count
    _add_concordant_percent(sample)


def _add_concordant_percent(sample):
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


@app.route('/tag/<tag_id>.html')
def sample_tag_html(tag_id):
    # this tag_id uses a home-grown forward slash escape.
    tag_id = _unescape_forward_slashes(tag_id)

    # look up all samples with this tag ID. Only return top level information though
    # (snp-level data is too much)
    db = mds.get_db()
    matching_samples = db.samples.find({'tags': tag_id}, {'chromosome_data': 0, 'unannotated_snps': 0})
    matching_samples = list(matching_samples)
    for sample in matching_samples:
        _add_call_percents(sample)

    return flask.render_template('sample-tag.html', matching_samples=matching_samples, tag_id=tag_id)


@app.route('/index.html')
@app.route('/')
def index_html():
    db = mds.get_db()
    tags = db.samples.distinct('tags')
    return flask.render_template('index.html', tags=tags)


@app.route('/sample/<mongo_id>.html')
def sample_html(mongo_id):
    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = db.samples.find_one({'_id': obj_id})
    _add_call_percents(sample)
    other_samples = db.samples.find({'_id': {'$ne': obj_id}}, {'chromosome_data': 0, 'unannotated_snps': 0})
    other_samples = list(other_samples)
    contrib_strain_tokens = [
        {'value': str(x['_id']), 'label': x['sample_id']}
        for x in other_samples
        if x['_id'] in sample['contributing_strains']
    ]

    all_tags = db.samples.distinct('tags')

    return flask.render_template(
        'sample.html',
        sample=sample,
        other_samples=other_samples,
        contrib_strain_tokens=contrib_strain_tokens,
        all_tags=all_tags,
    )


@app.route('/sample/<mongo_id>/contributing-strains.json', methods=['GET', 'POST'])
def contrib_strains_json(mongo_id):
    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    if flask.request.method == 'POST':
        form = flask.request.form
        new_strain_ids = json.loads(form['contributing_strain_ids'])
        new_strain_ids = [ObjectId(x) for x in new_strain_ids]
        haplotype_inference_uuid = str(uuid.uuid4())

        # we need to update the document and invalidate existing haplotypes
        db.samples.update_one(
            {'_id': obj_id},
            {
                '$set': {
                    'contributing_strains': new_strain_ids,
                    'haplotype_inference_uuid': haplotype_inference_uuid,
                },
                '$unset': {
                    'viterbi_haplotypes': '',
                },
            },
        )

        # since we invalidated haplotypes lets kick off tasks to recalculate
        if new_strain_ids:
            sample = db.samples.find_one({'_id': obj_id}, {'platform_id': 1})
            platform = db.platforms.find_one({'platform_id': sample['platform_id']})
            sample_obj_id = str(sample['_id'])
            for chr_id in platform['chromosomes']:
                infer_haplotype_structure_task.delay(
                    sample_obj_id,
                    chr_id,
                    haplotype_inference_uuid,
                )

    sample = db.samples.find_one({'_id': obj_id}, {'contributing_strains': 1})

    return flask.jsonify(contributing_strains=[str(x) for x in sample['contributing_strains']])


@app.route('/sample/<mongo_id>/tags.json', methods=['GET', 'POST'])
def tags_json(mongo_id):
    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    tags = []
    if flask.request.method == 'POST':
        form = flask.request.form
        tags = json.loads(form['tags'])
        db.samples.update_one({'_id': obj_id}, {'$set': {'tags': tags}})
    else:
        sample = db.samples.find_one({'_id': obj_id}, {'tags': 1})
        if sample is not None and 'tags' in sample:
            tags = sample['tags']

    return flask.jsonify(tags=tags)


@app.route('/sample/<mongo_id>/viterbi-haplotypes.json')
def viterbi_haplotypes_json(mongo_id):
    db = mds.get_db()
    obj_id = ObjectId(mongo_id)
    sample = db.samples.find_one({'_id': obj_id}, {'viterbi_haplotypes': 1, 'contributing_strains': 1})
    _add_concordant_percent(sample)
    haplotype_samples = [
        db.samples.find_one({'_id': x}, {'sample_id': 1})
        for x in sample['contributing_strains']
    ]
    haplotype_samples = [
        {'obj_id': str(x['_id']), 'sample_id': x['sample_id']}
        for x in haplotype_samples
    ]

    return flask.jsonify(
        viterbi_haplotypes=sample['viterbi_haplotypes'],
        haplotype_samples=haplotype_samples
    )


@celery.task(name='sample_data_import_task')
def sample_data_import_task(platform_id, sample_map_filename, final_report_filename, sample_group_name):
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


'''
def _haplo_call_concordance(sample, db):
    # This needs to be done on a per-chromosome basis. All of ther per-chr values should then
    # be summed at the end of each call to infer_haplotype_structure_task. We should also add
    # "discordant SNPs" to return dict

    total_informative = 0
    total_concordant = 0

    if 'viterbi_haplotypes' in sample:
        platform_id = sample['platform_id']
        #chrs = db.platforms.find_one({'platform_id': platform_id}, {'chromosomes': 1})
        for chr, chr_haplos in sample['viterbi_haplotypes'].items():
            contrib_strains_alleles = [
                db.samples.find_one(
                    {'_id': samp_id},
                    {
                        'chromosome_data.' + chr + '.allele1_fwds': 1,
                        'chromosome_data.' + chr + '.allele2_fwds': 1,
                    }
                )['chromosome_data'][chr]
                for samp_id in sample['contributing_strains']
            ]
            sample_alleles = sample['chromosome_data'][chr]

            snps = list(mds.get_snps(platform_id, chr, db))
            snp_index = 0
            for haplo in chr_haplos:
                print(haplo)
                print(len(contrib_strains_alleles))
                while snp_index < len(snps) and snps[snp_index]['position_bp'] < haplo['start_position_bp']:
                    snp_index += 1

                while snp_index < len(snps) and snps[snp_index]['position_bp'] <= haplo['end_position_bp']:
                    hap_strain1_alleles = contrib_strains_alleles[haplo['haplotype_index_1']]
                    hap_strain1_allele1 = hap_strain1_alleles['allele1_fwds'][snp_index]
                    hap_strain1_allele2 = hap_strain1_alleles['allele2_fwds'][snp_index]

                    hap_strain2_alleles = contrib_strains_alleles[haplo['haplotype_index_2']]
                    hap_strain2_allele1 = hap_strain2_alleles['allele1_fwds'][snp_index]
                    hap_strain2_allele2 = hap_strain2_alleles['allele2_fwds'][snp_index]

                    # only consider homozygous haplotype locations
                    if hap_strain1_allele1 == hap_strain1_allele2 and hap_strain1_allele1 != '-' and \
                       hap_strain2_allele1 == hap_strain2_allele2 and hap_strain2_allele1 != '-':

                        # we can now make a comparison. We call this SNP concordant if it has a SNP from
                        # each haplotype strain
                        haplo_call_set = {hap_strain1_allele1, hap_strain2_allele1}
                        sample_call_set = {
                            sample_alleles['allele1_fwds'][snp_index],
                            sample_alleles['allele2_fwds'][snp_index],
                        }

                        if haplo_call_set == sample_call_set:
                            total_concordant += 1
                        total_informative += 1

                    snp_index += 1

    return {
        'total_informative': total_informative,
        'total_concordant': total_concordant,
    }
'''


CONCORDANCE_BIN_SIZE = 200


def _call_concordance(max_likelihood_states, sample_ab_codes, contrib_ab_codes, snps):
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


@celery.task(name='infer_haplotype_structure_task')
def infer_haplotype_structure_task(sample_obj_id_str, chr_id, haplotype_inference_uuid):
    """

    :param sample_obj_id_str:
    :param chr_id:
    :param haplotype_inference_uuid:
        this tag is just used to make sure that haplotypes are
        inferred with the latest HMM settings (we need to prevent older inference
        tasks from overwriting the results from newer inference tasks since we're
        doing inference asynchronously)
    :return:
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
        haplotype_dict['haplotype_blocks'] = haplotype_blocks

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


if __name__ == '__main__':
    app.debug = True
    app.run()
