import argparse
import csv
from haploqa.haploqa import connect_db, default_db_path, init_db

header_tag = '[header]'
data_tag = '[data]'
tags = {header_tag, data_tag}

snp_name_col_hdr = 'SNP Name'
sample_id_col_hdr = 'Sample ID'
x_raw_col_hdr = 'X Raw'
y_raw_col_hdr = 'Y Raw'
x_col_hdr = 'X'
y_col_hdr = 'Y'
allele1_fwd_col_hdr = 'Allele1 - Forward'
allele2_fwd_col_hdr = 'Allele2 - Forward'
data_col_hdrs = {snp_name_col_hdr, sample_id_col_hdr, x_raw_col_hdr,
                 y_raw_col_hdr, x_col_hdr, y_col_hdr, allele1_fwd_col_hdr,
                 allele2_fwd_col_hdr}


def import_final_report(final_report_file, con):
    analyze_at_insert_number = 100000
    insert_count = 0
    with open(final_report_file, 'r') as final_report_handle:

        c = con.cursor()

        final_report_table = csv.reader(final_report_handle, delimiter='\t')

        prev_sample = None
        curr_section = None
        data_header_indexes = None
        for row_index, row in enumerate(final_report_table):
            def fmt_err(msg, cause=None):
                ex = Exception('Format Error in {} line {}: {}'.format(final_report_file, row_index + 1, msg))
                if cause is None:
                    raise ex
                else:
                    raise ex from cause

            def string_val(col_name):
                return row[data_header_indexes[col_name]].strip()

            def int_val(col_name):
                try:
                    return int(string_val(col_name))
                except ValueError as e:
                    fmt_err('TODO', e)

            def float_val(col_name):
                try:
                    return float(string_val(col_name))
                except ValueError as e:
                    fmt_err('TODO', e)

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
                            x_raw = int_val(x_raw_col_hdr)
                            y_raw = int_val(y_raw_col_hdr)
                            x = float_val(x_col_hdr)
                            y = float_val(y_col_hdr)
                            allele1_fwd = string_val(allele1_fwd_col_hdr)
                            allele2_fwd = string_val(allele2_fwd_col_hdr)

                            if prev_sample != sample_id:
                                print('importing sample:', sample_id)
                                prev_sample = sample_id

                            c.execute(
                                '''INSERT OR IGNORE INTO snp_read VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                (sample_id, snp_name, x, y, x_raw, y_raw, allele1_fwd, allele2_fwd),
                            )
                            insert_count += 1

                            if insert_count == analyze_at_insert_number:
                                print('performing ANALYZE to maintain insert performance')
                                c.execute('ANALYZE')
                                analyze_at_insert_number *= 4


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import the final report with probe intensities')
    parser.add_argument(
        'sqlite3_db_file',
        default=default_db_path,
        help='the SQLite3 DB file that will be written to')
    parser.add_argument(
        'final_report',
        help='the final report file as exported by GenomeStudio Genotyping Module. This report must '
             'be tab separated, must be in the "Standard" format and must contain '
             'at least the following columns: '
             'SNP Name, Sample ID, X Raw, Y Raw, X, Y, Allele1 - Forward, Allele2 - Forward')
    args = parser.parse_args()

    con = connect_db(True, args.sqlite3_db_file)
    init_db(con)
    import_final_report(args.final_report, con)
    con.commit()

    con.cursor('ANALYZE')
    con.commit()


if __name__ == '__main__':
    main()
