import argparse
import csv
import re
import sys
from haploqa.haploqa import connect_db, default_db_path, init_db


def import_snp_anno(snp_anno_file, platform, con):
    with open(snp_anno_file, 'r') as snp_anno_file_handle:
        snp_anno_table = csv.reader(snp_anno_file_handle, delimiter='\t')

        header = next(snp_anno_table)
        header_indexes = {x.lower(): i for i, x in enumerate(header)}

        snp_pattern = re.compile('''^\[(.)/(.)\]$''')
        c = con.cursor()
        for row in snp_anno_table:
            try:
                def get_val(column_name):
                    try:
                        val = row[header_indexes[column_name]]
                    except KeyError:
                        val = None

                    if val == "Unknown":
                        val = None
                    if val is None and column_name == 'platform':
                        val = platform

                    return val

                snp_calls = get_val('snp')
                x_probe_call = snp_calls[0]
                y_probe_call = snp_calls[1]

                c.execute('''
                        INSERT INTO snp_anno (
                            platform,
                            snp_id,
                            chromosome,
                            position_bp,
                            x_probe_call,
                            y_probe_call
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        get_val('platform'),
                        get_val('name'),
                        get_val('chromosome'),
                        int(get_val('position')),
                        x_probe_call,
                        y_probe_call,
                ))
            except:
                print('failed to import row:', row, file=sys.stderr)
                raise


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import SNP annotations')
    parser.add_argument(
        'sqlite3_db_file',
        default=default_db_path,
        help='the SQLite3 DB file that will be written to')
    parser.add_argument(
        'platform',
        help='the platform for the data we are importing. eg: MegaMUGA'
    )
    parser.add_argument(
        'snp_annotation_txt',
        help='the tab-delimited snp annotation file. There should be a header row and one row per SNP')
    args = parser.parse_args()

    con = connect_db(True, args.sqlite3_db_file)
    init_db(con)
    import_snp_anno(args.snp_annotation_txt, args.platform, con)
    con.commit()


if __name__ == '__main__':
    main()
