import contextlib
import sqlite3

import path 


def create_schema(db):
    with open(path.relative_file_name('schema.sql'), 'rb') as fh:
        db.executescript(fh.read().decode('utf-8'))


@contextlib.contextmanager
def connect(fname):
    conn = sqlite3.connect(fname)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    yield db

    conn.commit()
    db.close()
    conn.close()


@contextlib.contextmanager
def init(fname):
    with connect(fname) as db:
        create_schema(db)
        yield db
