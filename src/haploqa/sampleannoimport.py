import argparse
import csv
import sys
from haploqa.haploqa import connect_db, default_db_path, init_db


def import_sample_anno(sample_anno_file, platform, con):
    def to_canonical_header_name(name):
        # synonyms help us identify special headers when they're not using the canonical column name
        header_synonyms = {
            'gender': 'sex',
            'id': 'sample_id'
        }

        name = name.lower()
        try:
            return header_synonyms[name]
        except KeyError:
            return name

    with open(sample_anno_file, 'r') as sample_anno_file_handle:
        sample_anno_table = csv.reader(sample_anno_file_handle, delimiter='\t')

        header = next(sample_anno_table)
        header_indexes = {to_canonical_header_name(x): i for i, x in enumerate(header)}

        c = con.cursor()
        for row in sample_anno_table:
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

                # these attributes will be imported directly into the sample table.
                # TODO: Any others can be imported into seperate attribute tables.
                special_attributes = ('sample_id', 'sex', 'diet', 'notes', 'platform')
                insert_vals = tuple(map(get_val, special_attributes))
                c.execute('''INSERT INTO sample_data VALUES (?, ?, ?, ?, ?)''', insert_vals)
            except:
                print('failed to import row:', row, file=sys.stderr)
                raise


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import sample annotations')
    parser.add_argument(
        'sqlite3_db_file',
        default=default_db_path,
        help='the SQLite3 DB file that will be written to')
    parser.add_argument(
        'platform',
        help='the platform for the data we are importing. eg: MegaMUGA'
    )
    parser.add_argument(
        'sample_annotation_txt',
        help='the tab-delimited sample annotation file. There should be a header row and one row per file')
    args = parser.parse_args()

    con = connect_db(True, args.sqlite3_db_file)
    init_db(con)
    import_sample_anno(args.sample_annotation_txt, args.platform, con)
    con.commit()


if __name__ == '__main__':
    main()
