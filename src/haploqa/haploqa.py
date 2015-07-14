import csv
import os
import sqlite3

# if we're not provided a path we'll use a path that is relative to the source code
default_db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'haploqa.db')


def connect_db(create_if_missing=False, db_path=default_db_path):
    if create_if_missing or os.path.exists(db_path):
        return sqlite3.connect(db_path)
    else:
        raise Exception(db_path + ' not found')


def _dictify_row(cursor, row):
    """Turns the given row into a dictionary where the keys are the column names"""
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


def init_db(con):
    c = con.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS probe_anno (
            platform TEXT,
            probeset_id TEXT,
            chromosome TEXT,
            position_bp INTEGER,
            probe_status TEXT,
            PRIMARY KEY (platform, probeset_id)
        )
    ''')
    c.execute('''CREATE INDEX IF NOT EXISTS probe_anno_chr_index ON probe_anno (platform, chromosome, position_bp)''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sample_data (
          sample_id TEXT PRIMARY KEY,
          sex TEXT,
          diet TEXT,
          notes TEXT,
          platform TEXT
        )
    ''')

    c.execute('''
       CREATE TABLE IF NOT EXISTS probe_intensities (
          sample_id TEXT,
          probeset_id TEXT,
          probe_a_norm REAL, probe_b_norm REAL,
          probe_a_raw REAL, probe_b_raw REAL,
          call_a TEXT, call_b TEXT
       )
    ''')
    # TODO we'll probably need to index by sample_id x probeset_id
    c.execute('''CREATE INDEX IF NOT EXISTS probe_intensities_probe_id_index ON probe_intensities (probeset_id)''')


def get_platforms(con=None):
    if con is None:
        con = connect_db()

    c = con.cursor()
    c.execute('''SELECT DISTINCT platform FROM probe_anno''')

    return [x for x, in c]


def get_sample(sample_id, con=None):
    if con is None:
        con = connect_db()

    c = con.cursor()
    c.execute('''SELECT * FROM sample_data WHERE sample_id=?''', (sample_id, ))

    row = c.fetchone()
    if row is None:
        return None
    else:
        return _dictify_row(c, row)


def get_sample_ids(con=None):
    if con is None:
        con = connect_db()

    c = con.cursor()
    c.execute('''SELECT sample_id FROM sample_data''')

    return [x for x, in c]


def get_valid_chromosomes(platform, con=None):
    if con is None:
        con = connect_db()

    c = con.cursor()
    c.execute('''SELECT DISTINCT chromosome FROM probe_anno WHERE platform = ?''', (platform, ))

    return [x for x, in c]


def get_sample_probe_data(sample_id, chromosome, con=None):
    if con is None:
        con = connect_db()

    c = con.cursor()

    sample = get_sample(sample_id, con)
    if sample_id is None:
        raise Exception('unknown sample ID: ' + sample_id)
    platform = sample['platform']

    c.execute(
        '''
            SELECT * FROM
                probe_intensities AS PI
                INNER JOIN
                probe_anno AS PA ON PI.probeset_id=PA.probeset_id
            WHERE PA.platform=? AND PI.sample_id=? AND chromosome=?
            ORDER BY position_bp ASC
        ''',
        (platform, sample_id, chromosome)
    )

    return [_dictify_row(c, row) for row in c]


# def get_probe_data(probeset_id, con=None):
#     # TODO we need a way to limit by project/sample list/platform etc.
#     if con is None:
#         con = connect_db()
#
#     c = con.cursor()
#
#     c.execute('''SELECT * FROM probe_intensities WHERE probeset_id=?''', (probeset_id, ))
#
#

def generate_probe_data_by_probeset(con=None):
    # TODO we need a way to limit by project/sample list/platform etc.
    if con is None:
        con = connect_db()

    c = con.cursor()

    c.execute('''SELECT * FROM probe_intensities ORDER BY probeset_id''')
    curr_dict = None
    for row in c:
        row_dict = _dictify_row(c, row)
        if curr_dict is None or curr_dict['probeset_id'] != row_dict['probeset_id']:
            if curr_dict is not None:
                yield curr_dict

            curr_dict = {
                'probeset_id': row_dict['probeset_id'],
                'probe_data': [row_dict],
            }
        else:
            curr_dict['probe_data'].append(row_dict)

    if curr_dict is not None:
        yield curr_dict
