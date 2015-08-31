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
        CREATE TABLE IF NOT EXISTS snp_anno (
            platform TEXT,
            snp_id TEXT,
            chromosome TEXT,
            position_bp INTEGER,
            snp_status TEXT,
            x_probe_call TEXT,
            y_probe_call TEXT,
            PRIMARY KEY (platform, snp_id)
        )
    ''')
    c.execute('''CREATE INDEX IF NOT EXISTS snp_anno_chr_index ON snp_anno (platform, chromosome, position_bp)''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sample_data (
          sample_id TEXT PRIMARY KEY,
          sex TEXT,
          diet TEXT,
          notes TEXT,
          platform TEXT --,
          --strain1_id TEXT,
          --strain2_id TEXT
        )
    ''')

    c.execute('''
       CREATE TABLE IF NOT EXISTS snp_read (
          sample_id TEXT,
          snp_id TEXT,
          x_norm REAL, y_norm REAL,
          x_raw REAL, y_raw REAL,
          allele1_forward TEXT, allele2_forward TEXT,
          PRIMARY KEY (sample_id, snp_id)
       )
    ''')
    c.execute('''CREATE INDEX IF NOT EXISTS snp_read_snp_id_index ON snp_read (snp_id)''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS snp_clusters (
           snp_id TEXT,
           -- for F1 clusters strain 1 and 2 will have values (for autosomes
           -- the first strain will be the one that appears first using python's
           -- default string sort).
           --
           -- For a homozygous strain clusters, strain2_id will contain the
           -- empty string because NULL is not permitted for primary key columns
           strain1_id TEXT,
           strain2_id TEXT,
           mean_x REAL, mean_y REAL,
           rot_x_var REAL, rot_y_var REAL,
           PRIMARY KEY (snp_id, strain1_id, strain2_id)
        )
    ''')


def get_platforms(con=None):
    if con is None:
        con = connect_db()

    c = con.cursor()
    c.execute('''SELECT DISTINCT platform FROM snp_anno''')

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
    c.execute('''SELECT DISTINCT chromosome FROM snp_anno WHERE platform = ?''', (platform, ))

    return [x for x, in c]


def get_sample_snp_data(sample_id, chromosome, con=None):
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
                snp_read AS SR
                INNER JOIN
                snp_anno AS PA ON SR.snp_id=PA.snp_id
            WHERE PA.platform=? AND SR.sample_id=? AND chromosome=?
            ORDER BY position_bp ASC
        ''',
        (platform, sample_id, chromosome)
    )

    return [_dictify_row(c, row) for row in c]


# def get_snp_data(snp_id, con=None):
#     # TODO we need a way to limit by project/sample list/platform etc.
#     if con is None:
#         con = connect_db()
#
#     c = con.cursor()
#
#     c.execute('''SELECT * FROM snp_read WHERE snp_id=?''', (snp_id, ))
#
#

def generate_snp_data(con=None):
    """
    Returns a SNP data generator. The results are grouped by SNP ID
    :param con:
    :return:
    """
    # TODO we need a way to limit by project/sample list/platform etc.
    if con is None:
        con = connect_db()

    c = con.cursor()

    c.execute('''SELECT * FROM snp_read ORDER BY snp_id''')
    curr_dict = None
    for row in c:
        row_dict = _dictify_row(c, row)
        if curr_dict is None or curr_dict['snp_id'] != row_dict['snp_id']:
            if curr_dict is not None:
                yield curr_dict

            curr_dict = {
                'snp_id': row_dict['snp_id'],
                'snp_data': [row_dict],
            }
        else:
            curr_dict['snp_data'].append(row_dict)

    if curr_dict is not None:
        yield curr_dict
