import argparse
import csv
from os.path import splitext, basename
import time

import haploqa.mongods as mds
import haploqa.sampleannoimport as sai

header_tag = '[header]'
data_tag = '[data]'
tags = {header_tag, data_tag}

snp_name_col_hdr = 'SNP Name'
sample_id_col_hdr = 'Sample ID'
x_col_hdr = 'X'
y_col_hdr = 'Y'
allele1_fwd_col_hdr = 'Allele1 - Forward'
allele2_fwd_col_hdr = 'Allele2 - Forward'
data_col_hdrs = {
    snp_name_col_hdr, sample_id_col_hdr,
    x_col_hdr, y_col_hdr,
    allele1_fwd_col_hdr, allele2_fwd_col_hdr
}


def import_final_report(final_report_file, sample_anno_dicts, platform_id, sample_tags, db):
    platform_chrs, snp_count_per_chr, snp_chr_indexes = mds.within_chr_snp_indices(platform_id, db)

    prev_time = time.time()
    all_sample_ids = set()
    with open(final_report_file, 'r') as final_report_handle:

        final_report_table = csv.reader(final_report_handle, delimiter='\t')

        samples = db.samples
        curr_section = data_tag
        data_header_indexes = None
        curr_sample = None

        for row_index, row in enumerate(final_report_table):
            def fmt_err(msg, cause=None):
                ex = Exception('Format Error in {} line {}: {}'.format(final_report_file, row_index + 1, msg))
                if cause is None:
                    raise ex
                else:
                    raise ex from cause

            def string_val(col_name):
                return row[data_header_indexes[col_name]].strip()

            def float_val(col_name):
                str_val = string_val(col_name)
                try:
                    return float(str_val)
                except ValueError as e:
                    if str_val.upper() == 'NA':
                        return float('nan')
                    else:
                        fmt_err('failed to convert "' + str_val + '" into a float', e)

            # just ignore empty lines
            if row:
                if len(row) == 1 and row[0].lower() in tags:
                    curr_section = row[0].lower()
                else:
                    if curr_section == header_tag:
                        # TODO do something with the header data
                        pass
                    elif curr_section == data_tag:
                        if data_header_indexes is None:
                            # this is the header. we'll just make note of the indices
                            data_header_indexes = {
                                col_hdr: i
                                for i, col_hdr in enumerate(row)
                                if col_hdr in data_col_hdrs
                            }

                            # confirm that all are represented
                            for col_hdr in data_col_hdrs:
                                if col_hdr not in data_header_indexes:
                                    fmt_err('failed to find required header "{}" in data header'.format(col_hdr))
                        else:
                            snp_name = string_val(snp_name_col_hdr)
                            sample_id = string_val(sample_id_col_hdr)
                            x = float_val(x_col_hdr)
                            y = float_val(y_col_hdr)
                            allele1_fwd = string_val(allele1_fwd_col_hdr)
                            allele2_fwd = string_val(allele2_fwd_col_hdr)

                            if curr_sample is None or sample_id != curr_sample['sample_id']:
                                if sample_id in all_sample_ids:
                                    raise Exception('Final report must be grouped by sample ID but it is not')

                                all_sample_ids.add(sample_id)

                                if curr_sample is not None:
                                    mds.post_proc_sample(curr_sample)
                                    samples.replace_one(
                                        {'sample_id': curr_sample['sample_id']},
                                        curr_sample,
                                        upsert=True,
                                    )

                                curr_time = time.time()
                                print('took {:.1f} sec. importing sample: {}'.format(curr_time - prev_time, sample_id))
                                prev_time = curr_time

                                # curr_sample = samples.find_one({'sample_id': sample_id})
                                # if curr_sample is None:
                                chr_dict = dict()
                                for chr in platform_chrs:
                                    curr_snp_count = snp_count_per_chr[chr]
                                    chr_dict[chr] = {
                                        'xs': [float('nan')] * curr_snp_count,
                                        'ys': [float('nan')] * curr_snp_count,
                                        'allele1_fwds': ['-'] * curr_snp_count,
                                        'allele2_fwds': ['-'] * curr_snp_count,
                                    }

                                curr_sample = {
                                    'sample_id': sample_id,
                                    'platform_id': platform_id,
                                    'chromosome_data': chr_dict,
                                    'tags': sample_tags,
                                    'unannotated_snps': [],
                                }

                            try:
                                snp_chr_index = snp_chr_indexes[snp_name]
                            except KeyError:
                                snp_chr_index = None
                            if snp_chr_index is not None:
                                snp_chr = snp_chr_index['chromosome']
                                snp_index = snp_chr_index['index']

                                curr_sample_chr = curr_sample['chromosome_data'][snp_chr]
                                curr_sample_chr['xs'][snp_index] = x
                                curr_sample_chr['ys'][snp_index] = y
                                curr_sample_chr['allele1_fwds'][snp_index] = allele1_fwd
                                curr_sample_chr['allele2_fwds'][snp_index] = allele2_fwd
                            else:
                                curr_sample['unannotated_snps'].append({
                                    'snp_name': snp_name,
                                    'x': x,
                                    'y': y,
                                    'allele1_fwd': allele1_fwd,
                                    'allele2_fwd': allele2_fwd,
                                })

        if curr_sample is not None:
            try:
                curr_sample = sai.merge_dicts(curr_sample, sample_anno_dicts[curr_sample['sample_id']])
            except KeyError:
                pass
            mds.post_proc_sample(curr_sample)
            samples.insert_one(curr_sample)


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import the final report with probe intensities')
    parser.add_argument(
        'platform',
        help='the platform for the data we are importing. eg: MegaMUGA')
    parser.add_argument(
        'final_report',
        help='the final report file as exported by GenomeStudio Genotyping Module. This report must '
             'be tab separated, must be in the "Standard" format and must contain '
             'at least the following columns: '
             'SNP Name, Sample ID, X, Y, Allele1 - Forward, Allele2 - Forward')
    parser.add_argument(
        'sample_annotation_txt',
        nargs='*',
        help='an (optional) tab-delimited sample annotation file. There should be a header row and one row per sample')
    args = parser.parse_args()

    sample_anno_dicts = dict()
    for sample_anno_filename in args.sample_annotation_txt:
        curr_dicts = sai.sample_anno_dicts(sample_anno_filename)
        sample_anno_dicts = sai.merge_dicts(sample_anno_dicts, curr_dicts)

    report_name = splitext(basename(args.final_report))[0]
    import_final_report(args.final_report, sample_anno_dicts, args.platform, [report_name, args.platform], mds.init_db())


if __name__ == '__main__':
    main()
