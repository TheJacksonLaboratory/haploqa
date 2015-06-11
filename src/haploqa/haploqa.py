import csv
import os
import sqlite3

# if we're not provided a path we'll use a path that is relative to the source code
default_db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'haploqa.db')

def connect_db(create_if_missing=False, db_path=default_db_path):
    if create_if_missing or os.path.exists(db_path):
        return sqlite3.connect(db_path)
    else:
        raise Exception(db_path + ' not found')


def init_db(db_path=None):
    con = connect_db(True, db_path)
    c = con.cursor()

    c.execute('''
        CREATE TABLE probe_anno (
            platform TEXT,
            probeset_id TEXT,
            chromosome TEXT,
            position_bp INTEGER,
            probe_status TEXT,
            PRIMARY KEY (platform, probeset_id)
        )
    ''')

    c.execute('''
       CREATE TABLE PROBE_INTENSITIES (
          sample_id TEXT,
          probeset_id TEXT,
          probe_a REAL,
          probe_b REAL,
          call TEXT
       )
    ''')
