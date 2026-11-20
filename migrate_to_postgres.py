"""Copy the local CRM database into an empty PostgreSQL database."""

import argparse
from contextlib import closing
from getpass import getpass
from pathlib import Path
import sqlite3

import database as db

TABLES = ('products', 'contacts', 'projects', 'movements')


def migrate(source):
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as sqlite:
        sqlite.execute('BEGIN')
        source_data = {}
        for table in TABLES:
            cursor = sqlite.execute(f'SELECT * FROM {table} ORDER BY id')
            source_data[table] = ([column[0] for column in cursor.description], cursor.fetchall())

    db.init()
    with db.connect() as postgres, postgres.cursor() as cursor:
        from psycopg import sql

        tables = sql.SQL(', ').join(map(sql.Identifier, TABLES))
        cursor.execute(sql.SQL('LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE').format(tables))
        for table in TABLES:
            cursor.execute(sql.SQL('SELECT 1 FROM {} LIMIT 1').format(sql.Identifier(table)))
            if cursor.fetchone():
                raise SystemExit('Destination already has CRM records. No data was copied.')
        for table, (columns, records) in source_data.items():
            if not records:
                continue
            insert = sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(
                sql.Identifier(table),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() for _ in columns),
            )
            cursor.executemany(insert, records)
            next_id = max(record[columns.index('id')] for record in records) + 1
            cursor.execute(sql.SQL('ALTER TABLE {} ALTER COLUMN id RESTART WITH {}').format(
                sql.Identifier(table), sql.Literal(max(1, next_id)),
            ))

    return {table: len(records) for table, (_, records) in source_data.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=db.DB_PATH)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f'SQLite file not found: {args.source}')
    db.DATABASE_URL = db.DATABASE_URL or getpass('PostgreSQL connection URL: ').strip()
    if not db.DATABASE_URL:
        parser.error('A PostgreSQL connection URL is required.')
    for table, count in migrate(args.source).items():
        print(f'{table}: {count} records copied')
