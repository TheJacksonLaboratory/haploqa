import math
import numpy as np
from scipy.stats import norm

import haploqa.mongods as mds


_n_code = 0
_a_code = 1
_b_code = 2
_h_code = 3


def prob_density(cluster, point_x, point_y):
    """
    Find the probability density of the given cluster at x, y
    :param cluster: the cluster
    :param point_x: the x point
    :param point_y: the y point
    :return: the value of the probability density
    """

    mean_x = cluster['mean_x']
    mean_y = cluster['mean_y']
    rot_x_var = cluster['rot_x_var']
    rot_y_var = cluster['rot_y_var']

    clust_rot_mat = inverse_rot(mean_x, mean_y)

    rot_point_x, rot_point_y = clust_rot_mat.dot([point_x, point_y])

    # y is already centered around zero because of the rotation
    # but we still need to center x
    clust_hyp, _ = clust_rot_mat.dot([mean_x, mean_y])
    prob_density_x = norm.pdf(rot_point_x - clust_hyp, scale=np.sqrt(rot_x_var))
    prob_density_y = norm.pdf(rot_point_y, scale=np.sqrt(rot_y_var))

    # because we rotated for diagonal covariance we can simply multiply the
    # x and y covariances
    return prob_density_x * prob_density_y


def inverse_rot(x, y):
    '''
    Returns a 2D rotation matrix which will invert thetas rotation
    :param theta: the rotation angle to invert
    :return: the rotation matrix which will inverse thetas rotation
    '''

    # a 2D rotation matrix looks like:
    #
    # R = | cos(theta), -sin(theta) |
    #     | sin(theta), cos(theta)  |
    #
    # in order to invert the rotation we can just transpose the matrix giving
    #
    # R = |  cos(theta), sin(theta) |
    #     | -sin(theta), cos(theta) |

    hyp = math.sqrt(x * x + y * y)
    if hyp == 0:
        return np.array([
            [0.0, 0.0],
            [0.0, 0.0],
        ])
    else:
        cos_theta = x / hyp
        sin_theta = y / hyp
        return np.array([
            [cos_theta,  sin_theta],
            [-sin_theta, cos_theta],
        ])


def _scale_vector_to_one(v):
    """
    Scales the given vector in place such that sum(v) == 1
    """
    v /= np.sum(v)


def _scale_matrix_rows_to_one(m):
    """
    Scales the given vector in place such that all np.sum(m, 1) == 1
    """
    # get a column vector of row sums
    row_sums = np.sum(m, 1)
    row_sums = np.reshape(row_sums, (-1, 1))
    m /= row_sums


def sample_ids_to_ab_codes(sample_ids, chromosome, db=None):
    """
    Look up a matrix of AB codes for the given sample IDs.
    :param sample_ids:  the sample IDs
    :param chromosome: the chromosome
    :return: a matrix of AB codes. The numerical genotype codes used are: 0->N, 1->A, 2->B, 3->H
    """
    if db is None:
        db = mds.get_db()

    sample_count = len(sample_ids)

    x_calls = None
    y_calls = None
    ab_codes = None
    snp_count = 0
    for i, sample_id in enumerate(sample_ids):
        curr_sample = db.samples.find_one({'sample_id': sample_id})
        if curr_sample is None:
            raise Exception('failed to find a sample named "{}"'.format(sample_id))

        if i == 0:
            platform_id = curr_sample['platform_id']
            snps = mds.get_snps(platform_id, chromosome)
            x_calls = []
            y_calls = []
            for snp in snps:
                snp_count += 1
                x_calls.append(snp['x_probe_call'])
                y_calls.append(snp['y_probe_call'])
            x_calls = np.array(x_calls)
            y_calls = np.array(y_calls)
            ab_codes = np.empty((snp_count, sample_count), dtype=np.uint8)
            ab_codes.fill(255)

        allele1_fwds = np.array(curr_sample['chromosome_data'][chromosome]['allele1_fwds'])
        allele2_fwds = np.array(curr_sample['chromosome_data'][chromosome]['allele2_fwds'])

        # here we convert nucleotides (GACT and '-' for no call) into AB codes
        allele1_is_a = allele1_fwds == x_calls
        allele2_is_a = allele2_fwds == x_calls
        allele1_is_b = allele1_fwds == y_calls
        allele2_is_b = allele2_fwds == y_calls
        alleles_are_het = np.logical_or(
            np.logical_and(allele1_is_a, allele2_is_b),
            np.logical_and(allele1_is_b, allele2_is_a))
        ab_codes[np.logical_and(allele1_is_a, allele2_is_a), i] = _a_code
        ab_codes[np.logical_and(allele2_is_b, allele2_is_b), i] = _b_code
        ab_codes[alleles_are_het, i] = _h_code
        ab_codes[np.logical_or(allele1_fwds == '-', allele2_fwds == '-'), i] = _n_code

        if np.any(ab_codes[:, i] == 255):
            raise Exception('found unexpected SNP codes in sample: {}'.format(sample_id))

    return ab_codes


class SnpHaploHMM:

    def __init__(self, init_probs, trans_probs, hom_obs_probs, het_obs_probs, n_obs_probs):
        """
        construct a SNP Haplotype HMM. Note that the observation probabilities have a different structure
        than you would see in a standard HMM. This is because the valid observations change on
        a per SNP basis. We define N to be the number of haplotypes

        :param init_probs:
            the initial haplotype probs. must satisfy: len(init_probs) == N. The values
            of init_probs will be scaled such that sum(init_probs) == 1
        :param trans_probs:
            the haplotype transition probabilities. This must be an NxN matrix.
            All of the cells are the probability of
            P(transition to column_index haplotype | currently in row_index haplotype)
            The rows of this matrix will be scaled such that each row sums to 1.
        :param hom_obs_probs:
            a categorical distribution describing P(obs | homozygous read from hidden state).
            The values in this array will be scaled such that sum(hom_obs_probs) == 1.
            hom_obs_probs should be a numerical array where the indexes mean:

            0) observation is homozygous matching the hidden state (either A->A or B->B). For a
               well behaved HMM this should be by far the most probable. The other observations
               would be considered genotyping errors
            1) observation is homozygous not matching the hidden state (either A->B or B->A)
            2) observation is heterozygous (either A->H or B->H)
            3) observation is no read (either A->N or B->N)
        :param het_obs_probs:
            a categorical distribution describing P(obs | heterozygous read from hidden state).
            The values in this array will be scaled such that sum(het_obs_probs) == 1.
            het_obs_probs should be a numerical array where the indexes mean:

            0) observation is heterozygous (H->H). For a well behaved HMM this should be by far
               the most probable. The other observations would be considered genotyping errors
            1) observation is homozygous (either H->A or H->B)
            2) obs is no read (H->N)
        :param n_obs_probs:
            a categorical distribution describing P(obs | no read from hidden state). We'll call
            any of NN, NH, NA or NB an 'N' hidden state (that is to say that only one of the two
            contributing genotypes needs to be N for us to call the hidden state N)
            The values in this array will be scaled such that sum(n_obs_probs) == 1.
            n_obs_probs should be a numerical array where the indexes mean:

            0) observation is no read (N->N)
            1) observation is homozygous (N->A or N-B)
            2) observation is heterozygous (N->H)
        """

        self.hidden_state_count = init_probs.size

        # scale and assign initial probs
        _scale_vector_to_one(init_probs)
        self.init_probs = init_probs

        # scale and assign transition probs
        _scale_matrix_rows_to_one(trans_probs)
        self.trans_probs = trans_probs

        # scale and assign observation probs
        _scale_vector_to_one(hom_obs_probs)
        self.hom_obs_probs = hom_obs_probs
        _scale_vector_to_one(het_obs_probs)
        self.het_obs_probs = het_obs_probs
        _scale_vector_to_one(n_obs_probs)
        self.n_obs_probs = n_obs_probs

        # pack the sparse observation probs into a dense matrix for quick lookup
        # using codes where row is hidden state encoded as 0->N, 1->A, 2->B, 3->H and column
        # is observation encoded as 0->N, 1->A, 2->B, 3->H
        self.obs_prob_matrix = np.zeros((4, 4), dtype=np.float64)
        for i in range(4):
            for j in range(4):
                # if no read from hidden state
                if i == 0:
                    # if N from observation
                    if j == 0:
                        self.obs_prob_matrix[i, j] = self.n_obs_probs[0]
                    # if hom from observation
                    elif j == 1 or j == 2:
                        self.obs_prob_matrix[i, j] = self.n_obs_probs[1]
                    # else het from observation
                    else:
                        self.obs_prob_matrix[i, j] = self.n_obs_probs[2]
                # if hom from hidden state
                elif i == 1 or i == 2:
                    # if N from observation
                    if j == 0:
                        self.obs_prob_matrix[i, j] = self.hom_obs_probs[3]
                    # if het from observation
                    elif j == 3:
                        self.obs_prob_matrix[i, j] = self.hom_obs_probs[2]
                    # if matching hom from observation
                    elif j == i:
                        self.obs_prob_matrix[i, j] = self.hom_obs_probs[0]
                    # else non-matching hom from observation
                    else:
                        self.obs_prob_matrix[i, j] = self.hom_obs_probs[1]
                # else het from hidden state
                else:
                    # if N from observation
                    if j == 0:
                        self.obs_prob_matrix[i, j] = self.het_obs_probs[2]
                    # if het from observation
                    elif j == 3:
                        self.obs_prob_matrix[i, j] = self.het_obs_probs[0]
                    # else hom from observation (A or B)
                    else:
                        self.obs_prob_matrix[i, j] = self.het_obs_probs[1]
        print(self.obs_prob_matrix)


    def viterbi(self, haplotype_ab_codes, observation_ab_codes):
        """
        Run the viterbi algorithm to find the haplotype state sequence (S) that maximizes
        P(S|O, HMM) where O is the observation sequence and HMM is this parameterized HMM

        :param haplotype_ab_codes:
            a 2D matrix where row_index == snp_index and col_index == haplotype_index (which must
            match the haplotype indices used in the transition probs).
            The numerical genotype codes used should be: 0->N, 1->A, 2->B, 3->H

        :param observation_ab_codes:
            a vector of genotype observations the length of observation_ab_codes should match
            the row count of haplotype_ab_codes
            The numerical genotype codes used should be: 0->N, 1->A, 2->B, 3->H
        :return:
            the tuple (max_likelihood_states, log_likelihood) where,

            * max_likelihood_states is the most likely sequence of states given the HMM and the observations.
              This will be a numeric vector where indices match observation_ab_codes and values represent
              haplotype indices
            * log_likelihood is the log likelihood of this hidden state sequence
        """
        obs_count = observation_ab_codes.size

        log_init_probs = np.log(self.init_probs)
        log_trans_probs = np.log(self.trans_probs)
        log_obs_prob_matrix = np.log(self.obs_prob_matrix)

        # initialize viterbi using first observations and the init_probs
        curr_log_obs_probs = log_obs_prob_matrix[haplotype_ab_codes[0, :], observation_ab_codes[0]]
        curr_log_likelihoods = log_init_probs + curr_log_obs_probs

        from_state_lattice = np.zeros((obs_count - 1, self.hidden_state_count), dtype=np.uint16)
        for t in range(1, obs_count):
            prev_log_likelihoods = curr_log_likelihoods
            curr_log_likelihoods = np.zeros(self.hidden_state_count, dtype=np.float64)
            #curr_from_states = from_state_lattice[t - 1, :]

            for to_state in range(self.hidden_state_count):
                from_log_likelihoods = prev_log_likelihoods + log_trans_probs[:, to_state]
                #print(from_log_likelihoods)
                max_from_state = np.argmax(from_log_likelihoods)
                #print(max_from_state)
                #curr_from_states[to_state] = max_from_state
                from_state_lattice[t - 1, to_state] = max_from_state
                curr_log_likelihoods[to_state] = from_log_likelihoods[max_from_state]

            curr_log_obs_probs = log_obs_prob_matrix[haplotype_ab_codes[t, :], observation_ab_codes[t]]
            if len(set(curr_log_obs_probs.tolist())) > 1:
                print('obs code')
                print(np.array(['N', 'A', 'B', 'H'])[observation_ab_codes[t]])
                print('hap codes')
                print(np.array(['N', 'A', 'B', 'H'])[haplotype_ab_codes[t, :]])
                print(curr_log_obs_probs)
            curr_log_likelihoods += curr_log_obs_probs

        # backtrace through the most likely path starting with the final state
        #print(from_state_lattice)
        max_final_state = np.argmax(curr_log_likelihoods)
        max_final_likelihood = np.argmax(curr_log_likelihoods)
        max_likelihood_states = np.zeros(obs_count, dtype=np.uint16)
        max_likelihood_states[obs_count - 1] = max_final_state
        for t in reversed(range(obs_count - 1)):
            max_likelihood_states[t] = from_state_lattice[t, max_likelihood_states[t + 1]]

        return max_likelihood_states, max_final_likelihood

    def log_likelihood(self, haplotype_ab_codes, observation_ab_codes):
        """

        :param haplotype_ab_codes:
        :param observation_ab_codes:
        :return:
        """
        pass

    def forward_scan(self, haplotype_ab_codes, observation_ab_codes):
        """

        :param haplotype_ab_codes:
        :param observation_ab_codes:
        :return:
        """

        forward_likelihoods = None
        forward_scaling_factors = None

        return forward_likelihoods, forward_scaling_factors


def main():
    #print(sample_ids_to_ab_codes(['UM-001', 'JAX-002', 'JAX-005', 'JAX-007', 'JAX-008', 'NIH_TVD_YS-B1'], '19'))

    # flat initial probs
    init_probs = np.ones(3, dtype=np.float64)

    # 100 times more likely to stay in current state than to transition to any other specific haplotype
    trans_probs = np.array([
        [100, 1,   1],
        [1,   100, 1],
        [1,   1,   100],
    ], dtype=np.float64)
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

    test_hmm = SnpHaploHMM(init_probs, trans_probs, hom_obs_probs, het_obs_probs, n_obs_probs)

    print('getting AB Codes')
    ab_codes = sample_ids_to_ab_codes(['UM-001', 'JAX-002', 'JAX-007', 'JAX-005'], '19')
    print('performing viterbi')
    np.set_printoptions(threshold=np.nan)
    best_path = test_hmm.viterbi(haplotype_ab_codes=ab_codes[:, 1:], observation_ab_codes=ab_codes[:, 1])
    #print(best_path)
    print('done with viterbi')

if __name__ == '__main__':
    main()
