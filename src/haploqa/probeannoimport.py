import argparse
import csv
import sys
from haploqa.haploqa import connect_db, default_db_path, init_db

_snp_type_dict = {
    'A': 'biallelic SNP with good performance',
    'A, B': 'Marker with unknown performance'
}

def import_snp_anno(snp_anno_file, con):
    with open(snp_anno_file, 'r') as snp_anno_file_handle:
        snp_anno_csv = csv.reader(snp_anno_file_handle)

        # throw out the header
        next(snp_anno_csv)
        c = con.cursor()
        for row in snp_anno_csv:
            try:
                marker, chr, position_bp, snp_type = [x.strip() for x in row[:4]]
                try:
                    position_bp = int(position_bp)
                except ValueError:
                    fmt_msg = 'position "{}" is not a base-pair value in row {}. Using None value instead.'
                    print(fmt_msg.format(position_bp, row))
                    position_bp = None

                c.execute(
                    '''INSERT INTO snp_anno VALUES (?, ?, ?, ?, ?)''',
                    ('MegaMUGA', marker, chr, position_bp, snp_type)
                )
            except:
                print('failed to import row:', row, file=sys.stderr)
                raise

        # print out some info about values
        c.execute('SELECT DISTINCT chromosome FROM snp_anno')
        print('unique chromosome:', [chr for chr, in c])
        c.execute('SELECT DISTINCT snp_status FROM snp_anno')
        print('unique snp_status:', [ps for ps, in c])


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import probe annotations')
    parser.add_argument(
        'sqlite3_db_file',
        default=default_db_path,
        help='the SQLite3 DB file that will be written to')
    parser.add_argument(
        'snp_anno_csv',
        help='the probe annotations file to import')
    args = parser.parse_args()

    con = connect_db(True, args.sqlite3_db_file)
    init_db(con)
    import_snp_anno(args.snp_anno_csv, con)
    con.commit()


if __name__ == '__main__':
    main()
