import argparse
import csv

import haploqa.mongods as mds


SAMPLE_BATCH_SIZE = 20


def import_samples(platform, geno_matrix_csv, x_matrix_csv, y_matrix_csv, sample_tags, db):
    platform_chrs, snp_count_per_chr, snp_chr_indexes = mds.within_chr_snp_indices(platform, db)

    curr_sample_start_index = 0
    while True:
        def get_sample_names(header_row):
            slice = header_row[curr_sample_start_index:curr_sample_start_index + SAMPLE_BATCH_SIZE]
            return [x.strip() for x in slice]

        def get_data(data_row):
            # the '+ 1' is because we need to shift right to accommodate the SNP ID column
            slice = data_row[curr_sample_start_index + 1:curr_sample_start_index + SAMPLE_BATCH_SIZE + 1]
            return [x.strip() for x in slice]

        with open(geno_matrix_csv, 'r', newline='') as geno_matrix_handle, \
             open(x_matrix_csv, 'r', newline='') as x_matrix_handle, \
             open(y_matrix_csv, 'r', newline='') as y_matrix_handle:

            # grab the current sample names
            geno_matrix_table = csv.reader(geno_matrix_handle)
            x_matrix_table = csv.reader(x_matrix_handle)
            y_matrix_table = csv.reader(y_matrix_handle)

            sample_names = get_sample_names(next(geno_matrix_table))
            if not sample_names:
                # we've already imported all of the samples
                return
            x_sample_names = get_sample_names(next(x_matrix_table))
            y_sample_names = get_sample_names(next(y_matrix_table))

            if sample_names != x_sample_names or sample_names != y_sample_names:
                raise Exception('sample IDs do not match in files')

            def make_snp_stream():
                while True:
                    next_geno_row = next(geno_matrix_table)
                    next_x_row = next(x_matrix_table)
                    next_y_row = next(y_matrix_table)

                    snp_id = next_geno_row[0].strip()
                    if snp_id != next_x_row[0].strip() or snp_id != next_y_row[0].strip():
                        raise Exception('snp IDs do not match in files')

                    genos = get_data(next_geno_row)
                    xs = [float(x) for x in get_data(next_x_row)]
                    ys = [float(y) for y in get_data(next_y_row)]

                    yield snp_id, genos, xs, ys

            samples = []
            for sample_name in sample_names:
                chr_dict = dict()
                for chr in platform_chrs:
                    curr_snp_count = snp_count_per_chr[chr]
                    chr_dict[chr] = {
                        'xs': [float('nan')] * curr_snp_count,
                        'ys': [float('nan')] * curr_snp_count,
                        'snps': ['-'] * curr_snp_count,
                    }
                curr_sample = {
                    'sample_id': sample_name,
                    'platform_id': platform,
                    'chromosome_data': chr_dict,
                    'tags': sample_tags,
                    'unannotated_snps': [],
                }
                samples.append(curr_sample)

            for snp_id, genos, xs, ys in make_snp_stream():
                snp_chr_index = snp_chr_indexes.get(snp_id)
                if snp_chr_index is not None:
                    snp_chr = snp_chr_index['chromosome']
                    snp_index = snp_chr_index['index']
                    for i, curr_sample in enumerate(samples):
                        curr_geno = genos[i].upper()
                        if curr_geno == 'N':
                            curr_geno = '-'
                        curr_x = xs[i]
                        curr_y = ys[i]

                        curr_sample_chr = curr_sample['chromosome_data'][snp_chr]
                        curr_sample_chr['xs'][snp_index] = curr_x
                        curr_sample_chr['ys'][snp_index] = curr_y
                        curr_sample_chr['snps'][snp_index] = curr_geno

            for curr_sample in samples:
                mds.post_proc_sample(curr_sample)
                db.samples.replace_one(
                    {'sample_id': curr_sample['sample_id']},
                    curr_sample,
                    upsert=True,
                )
            print('inserted samples:', ', '.join(sample_names))

        curr_sample_start_index += SAMPLE_BATCH_SIZE


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import the final report with probe intensities')
    parser.add_argument(
        'platform',
        help='the platform for the data we are importing. eg: MegaMUGA')
    parser.add_argument(
        'tag',
        help='a tag name that should be associated with all imported samples')
    parser.add_argument(
        'geno_matrix_csv',
        help='comma-separated genotype values matrix')
    parser.add_argument(
        'x_matrix_csv',
        help='comma-separated X intensity values matrix')
    parser.add_argument(
        'y_matrix_csv',
        help='comma-separated Y intensity values matrix')
    args = parser.parse_args()

    import_samples(
            args.platform,
            args.geno_matrix_csv, args.x_matrix_csv, args.y_matrix_csv,
            [args.tag, args.platform],
            mds.init_db())


if __name__ == '__main__':
    main()
