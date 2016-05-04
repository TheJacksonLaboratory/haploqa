from bson.objectid import ObjectId
import haploqa.mongods as mds
import numpy as np
import scipy.stats as stats

from pprint import pprint

# we're not even going to try with any targets that have fewer than this number of samples
min_pos_neg_count = 4

def _get_gemm_snp_intens(gemm_snp, sample):
    # this is a bit convoluted but all we are doing here is extracting
    # the intensity for the target SNP at the informative axis
    snp_chr = gemm_snp['chromosome']
    intens_key = 'xs' if gemm_snp['informative_axis'] == 'X' else 'ys'
    intens_index = gemm_snp['within_chr_index']
    return sample['chromosome_data'][snp_chr][intens_key][intens_index]

def est_gemm_probs(sample_obj_ids, db=None):
    # find all the SNPs that have been labeled for engineered targets
    if db is None:
        db = mds.get_db()

    # organize GEMM snps by target
    gemm_snps = list(db.snps.find({'engineered_target': {'$exists': True}}))
    gemm_snp_dict = {snp['engineered_target']: [] for snp in gemm_snps}
    for snp in gemm_snps:
        snp['pos_ctrls'] = []
        snp['neg_ctrls'] = []
        gemm_snp_dict[snp['engineered_target']].append(snp)

    # find all pos/neg samples
    # TODO this approach is much more expensive than it should be (we're loading
    # all SNP data for the samples even though we only care about a small subset
    # of SNPs) but I'm just going to go with this for now.
    pos_tgt_sample_counts = {k: 0 for k in gemm_snp_dict.keys()}
    for sample in db.samples.find({'pos_ctrl_eng_tgts': {'$exists': True, '$ne': []}}):
        for pos_tgt in set(sample['pos_ctrl_eng_tgts']):
            if pos_tgt not in gemm_snp_dict:
                continue

            pos_tgt_sample_counts[pos_tgt] += 1
            for pos_tgt_snp in gemm_snp_dict[pos_tgt]:
                intens_val = _get_gemm_snp_intens(pos_tgt_snp, sample)
                pos_tgt_snp['pos_ctrls'].append(intens_val)

    # and now the same for the negative samples
    neg_tgt_sample_counts = {k: 0 for k in gemm_snp_dict.keys()}
    for sample in db.samples.find({'neg_ctrl_eng_tgts': {'$exists': True, '$ne': []}}):
        for neg_tgt in set(sample['neg_ctrl_eng_tgts']):
            if neg_tgt not in gemm_snp_dict:
                continue

            neg_tgt_sample_counts[neg_tgt] += 1
            for neg_tgt_snp in gemm_snp_dict[neg_tgt]:
                intens_val = _get_gemm_snp_intens(neg_tgt_snp, sample)
                neg_tgt_snp['neg_ctrls'].append(intens_val)

    # we ignore any targets that don't meet our sample count threshold
    for tgt in pos_tgt_sample_counts.keys():
        if pos_tgt_sample_counts[tgt] < min_pos_neg_count or neg_tgt_sample_counts[tgt] < min_pos_neg_count:
            del gemm_snp_dict[tgt]

    # now we fit a multivariate normal to each GEMM target (where # dimensions == # probes)
    mixture_probs = dict()
    for gemm_eng_tgt, gemm_snps in gemm_snp_dict.items():

        # extract intensities from samples that we want to "GEMM-type"
        sample_intens = np.empty([len(sample_obj_ids), len(gemm_snps)], dtype=np.double)
        for row, sample_obj_id in enumerate(sample_obj_ids):
            sample = db.samples.find_one({'_id': sample_obj_id})
            for col, gemm_snp in enumerate(gemm_snps):
                intens_val = _get_gemm_snp_intens(gemm_snp, sample)
                sample_intens[row, col] = intens_val

        pos_ctrls = np.array([gemm_snp['pos_ctrls'] for gemm_snp in gemm_snps])
        pos_ctrl_cov = np.cov(pos_ctrls)
        pos_ctrl_mean = np.mean(pos_ctrls, axis=1)
        pos_pdf_densities = stats.multivariate_normal.pdf(sample_intens, pos_ctrl_mean, pos_ctrl_cov)

        neg_ctrls = np.array([gemm_snp['neg_ctrls'] for gemm_snp in gemm_snps])
        neg_ctrl_cov = np.cov(neg_ctrls)
        neg_ctrl_mean = np.mean(neg_ctrls, axis=1)
        neg_pdf_densities = stats.multivariate_normal.pdf(sample_intens, neg_ctrl_mean, neg_ctrl_cov)

        # for some reason these are only arrays if you pass in a sample_obj_ids with more than one val
        if len(sample_obj_ids) == 1:
            pos_pdf_densities = np.array([pos_pdf_densities])
            neg_pdf_densities = np.array([neg_pdf_densities])

        sum_densities = pos_pdf_densities + neg_pdf_densities
        mixture_probs[gemm_eng_tgt] = [float(x) for x in pos_pdf_densities / sum_densities]

    return mixture_probs


def main():
    print('||||||||||||||||||||||||||||||||||||||||||||')
    print('cHS4 positive:')
    pprint(est_gemm_probs([ObjectId('5696762585b062edc4efbed7'), ObjectId('5696761785b062edc4efbecf'), ObjectId('569675ff85b062edc4efbebf'), ObjectId('5696760b85b062edc4efbec7')]))
    # print('||||||||||||||||||||||||||||||||||||||||||||')
    # print('first two tomato positive:')
    # pprint(est_gemm_probs([ObjectId('5696769185b062edc4efbf1b'), ObjectId('569676b785b062edc4efbf33'), ObjectId('55e9d18d6606af0e6e5cb6ad')]))
    # print('||||||||||||||||||||||||||||||||||||||||||||')
    # print('first one neo positive:')
    # pprint(est_gemm_probs([ObjectId('5696762885b062edc4efbed9'), ObjectId('55e9d18d6606af0e6e5cb6ad')]))

    print('single item test')
    pprint(est_gemm_probs([ObjectId('5696762585b062edc4efbed7')]))

if __name__ == '__main__':
    main()
