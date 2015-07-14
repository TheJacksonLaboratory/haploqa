import argparse
import csv
import sys
from haploqa.haploqa import connect_db, default_db_path, init_db

_probe_type_dict = {
    'A': 'biallelic SNP with good performance',
    'A, B': 'Marker with unknown performance'
}

def import_probe_anno(probe_anno_file, con):
    with open(probe_anno_file, 'r') as probe_anno_file_handle:
        probe_anno_csv = csv.reader(probe_anno_file_handle)

        # throw out the header
        next(probe_anno_csv)
        c = con.cursor()
        for row in probe_anno_csv:
            try:
                marker, chr, position_bp, probe_type = [x.strip() for x in row[:4]]
                try:
                    position_bp = int(position_bp)
                except ValueError:
                    fmt_msg = 'position "{}" is not a base-pair value in row {}. Using None value instead.'
                    print(fmt_msg.format(position_bp, row))
                    position_bp = None

                c.execute(
                    '''INSERT INTO probe_anno VALUES (?, ?, ?, ?, ?)''',
                    ('MegaMUGA', marker, chr, position_bp, probe_type)
                )
            except:
                print('failed to import row:', row, file=sys.stderr)
                raise

        # print out some info about values
        c.execute('SELECT DISTINCT chromosome FROM probe_anno')
        print('unique chromosome:', [chr for chr, in c])
        c.execute('SELECT DISTINCT probe_status FROM probe_anno')
        print('unique probe_status:', [ps for ps, in c])


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import probe annotations')
    parser.add_argument(
        'sqlite3_db_file',
        default=default_db_path,
        help='the SQLite3 DB file that will be written to')
    parser.add_argument(
        'probe_anno_csv',
        help='the probe annotations file to import')
    args = parser.parse_args()

    con = connect_db(True, args.sqlite3_db_file)
    init_db(con)
    import_probe_anno(args.probe_anno_csv, con)
    con.commit()


if __name__ == '__main__':
    main()
