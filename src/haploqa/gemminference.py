from bson.objectid import ObjectId
import haploqa.mongods as mds
import numpy as np
from scipy.stats import multivariate_normal
from scipy.spatial.distance import mahalanobis

from pprint import pprint


def _get_gemm_snp_intens(gemm_snp, sample):
    # this is a bit convoluted but all we are doing here is extracting
    # the intensity for the target SNP at the informative axis
    snp_chr = gemm_snp['chromosome']
    intens_key = 'xs' if gemm_snp['informative_axis'] == 'X' else 'ys'
    intens_index = gemm_snp['within_chr_index']
    return sample['chromosome_data'][snp_chr][intens_key][intens_index]


def _calc_pd_and_dist(ctrl_intens, sample_intens):
    """
    Calculates per-sample probability densities and mahalanobis distances. The
    densities and distances are with respect to a (multivariate) gaussian
    distribution fit to the control intensities.
    :param ctrl_intens:
            the control intensities that we fit a gaussian to. This is a 2D
            matrix where columns correspond to samples, rows correspond to
            control probes and values are the control intensities
    :param sample_intens:
            the samples for which we are calculating densities and distances.
            Rows correspond to samples and columns correspond to probes
    :return:
            a tuple of vectors composed of (prob_densities, dists) where
            vector index corresponds to sample
    """

    # Note: there's probably a more efficient way to calculate the density and distance together
    #       without using the library functions but I'm not sure it's worth bothering with

    ctrl_cov = np.cov(ctrl_intens)
    ctrl_mean = np.mean(ctrl_intens, axis=1)
    prob_densities = multivariate_normal.pdf(sample_intens, ctrl_mean, ctrl_cov)

    # for some reason the densities become scalar if there is only a single sample. Here
    # we cast them back as numpy arrays of size one
    if not isinstance(prob_densities, np.ndarray):
        prob_densities = np.array([prob_densities])

    # calculate distance
    inv_ctrl_cov = np.linalg.inv(ctrl_cov)
    dists = np.array([
        mahalanobis(sample_row, ctrl_mean, inv_ctrl_cov)
        for sample_row
        in list(sample_intens)
    ])

    return prob_densities, dists


def est_gemm_probs(sample_obj_ids, min_pos_neg_count=4, max_mahalanobis_dist=2, db=None):
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

    # find all pos/neg samples and collect their probe intensities for all of the engineered targets
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
        pos_pdf_densities, neg_mah_dists = _calc_pd_and_dist(pos_ctrls, sample_intens)

        neg_ctrls = np.array([gemm_snp['neg_ctrls'] for gemm_snp in gemm_snps])
        neg_pdf_densities, pos_mah_dists = _calc_pd_and_dist(neg_ctrls, sample_intens)

        # calculate a vector of per-sample probabilities that a sample came from
        # the positive (ie GEMM present) mixture component. Then, if a sample is
        # more than maximum_mahalanobis_dist units from the nearest mixture component
        # we set its probability to NaN
        sum_densities = pos_pdf_densities + neg_pdf_densities
        pos_mixture_component_probs = pos_pdf_densities / sum_densities
        pos_mixture_component_probs[np.logical_not(np.isfinite(pos_mixture_component_probs))] = np.nan
        min_mah_dists = np.minimum(neg_mah_dists, pos_mah_dists)
        pos_mixture_component_probs[min_mah_dists > max_mahalanobis_dist] = np.nan

        mixture_probs[gemm_eng_tgt] = [float(x) for x in pos_mixture_component_probs]

    return mixture_probs


def main():
    # just some quick test code to see that things are working as expected
    print('||||||||||||||||||||||||||||||||||||||||||||')
    print('cHS4 positive:')
    pprint(est_gemm_probs([
        ObjectId('5696762585b062edc4efbed7'), ObjectId('5696761785b062edc4efbecf'),
        ObjectId('569675ff85b062edc4efbebf'), ObjectId('5696760b85b062edc4efbec7')]))
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
