import argparse
import h5py
import numpy as np
import sys

import haploqa.mongods as mds


def as_utf8(s):
    if isinstance(s, bytes):
        return s.decode()
    else:
        return s


def merge_h5(h5_filename, match_other_ids):
    """
    Merge data from the given HDF5 file into the database

    :param h5_filename: the name of the HDF5 file containing the data to merge
    :param match_other_ids:
        this indicates that the IDs present are not canonical and should be matched against
        a sample's "other_ids" attribute rather than the canonical "sample_id" attribute
    """
    db = mds.get_db()
    samples = db.samples
    h5_file = h5py.File(h5_filename, 'r')

    platform_tuple_cache = dict()
    def get_platform_tuple(platform_id):
        if platform_id in platform_tuple_cache:
            return platform_tuple_cache[platform_id]
        else:
            tup = mds.within_chr_snp_indices(platform_id, db)
            platform_tuple_cache[platform_id] = tup
            return tup

    samples_grp = h5_file['samples']
    for sample_grp_name in samples_grp:
        sample_grp = samples_grp[sample_grp_name]

        # for attr_name in sample_grp:
        #     print('\t' + attr_name)

        if 'sample_id' in sample_grp:
            h5_sample_id = as_utf8(sample_grp['sample_id'][0])
            matching_samples = list(samples.find(
                {'other_ids': h5_sample_id},
                {'_id': 1, 'sample_id': 1, 'platform_id': 1}))
            matching_sample_count = len(matching_samples)
            if matching_sample_count == 1:
                print('processing:', h5_sample_id)
                mds_matching_sample = matching_samples[0]

                mds_sample_id = mds_matching_sample['sample_id']
                mds_sample_platform = mds_matching_sample['platform_id']
                h5_sample_platform = as_utf8(sample_grp['platform'][0])
                if h5_sample_platform != mds_sample_platform:
                    print('skipping', h5_sample_id, 'due to platform mismatch', file=sys.stderr)
                    continue

                h5_probeset_ids = [as_utf8(x) for x in np.array(sample_grp['probeset_ids'])]
                h5_diplotype_probabilities = np.array(sample_grp['diplotype_probabilities']).transpose().tolist()
                h5_diplotype_strains = list(map(lambda x: list(map(as_utf8, x)), sample_grp['diplotype_strains']))

                platform_chrs, snp_count_per_chr, snp_chr_indexes = get_platform_tuple(h5_sample_platform)

                # create a per-chromosome 2D list with shape (# platform SNPs, # diplotype strains) for probabilities
                chr_probs = {
                    chrom: [[float('nan')] * len(h5_diplotype_strains) for _ in range(count)]
                    for chrom, count
                    in snp_count_per_chr.items()
                }
                for h5_idx, probeset_id in enumerate(h5_probeset_ids):
                    if probeset_id in snp_chr_indexes:
                        chr_idx = snp_chr_indexes[probeset_id]
                        chr_probs[chr_idx['chromosome']][chr_idx['index']] = h5_diplotype_probabilities[h5_idx]

                for chr, probs in chr_probs.items():
                    db.diplotype_probabilities.update_one(
                        {'sample_id': mds_sample_id, 'chromosome': chr},
                        {'$set': {
                            'sample_id': mds_sample_id,
                            'chromosome': chr,
                            'platform_id': h5_sample_platform,
                            'diplotype_probabilities': probs,
                            'diplotype_strains': h5_diplotype_strains,
                        }},
                        upsert=True,
                    )
            else:
                print('skipping:', h5_sample_id)


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import data from an HDF5 file')
    parser.add_argument(
        'h5_file',
        help='the HDF file to import')
    args = parser.parse_args()

    merge_h5(args.h5_file, True)


if __name__ == '__main__':
    main()
