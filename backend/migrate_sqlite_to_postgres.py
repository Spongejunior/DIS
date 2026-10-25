"""Copy all data from the SQLite database into PostgreSQL.

Usage (from the backend/ folder):

    python migrate_sqlite_to_postgres.py                 # target = DATABASE_URL from .env
    python migrate_sqlite_to_postgres.py --target postgresql://user:pass@host:5432/db
    python migrate_sqlite_to_postgres.py --replace       # empty the target tables first

What it does:
1. Creates the tables in PostgreSQL from models.py (if they do not exist).
2. Checks every row first, because PostgreSQL is stricter than SQLite: text
   longer than its column allows, or an empty required field, stops the
   migration with a list of the problem rows. Nothing is written in that case.
   Rows that point at a deleted record (SQLite never enforced these links)
   keep the row and lose the link when the link is optional, such as the user
   on an old log entry.
3. Copies every table (users first, then the rows that refer to them) in one
   transaction: either everything is copied or nothing is.
4. Moves each table's id counter past the copied ids, so new rows get new ids.
5. Compares row counts between the two databases.

The SQLite file is only read, never changed.
"""
import argparse
import os
import sys

from sqlalchemy import String, create_engine, func, inspect, select, text

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

from config import Config  # noqa: E402  (loads backend/.env)
from models import db  # noqa: E402

DEFAULT_SOURCE = 'sqlite:///' + os.path.join(BACKEND_DIR, 'instance', 'database.db').replace('\\', '/')


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--source', default=DEFAULT_SOURCE, help='SQLite URL (default: instance/database.db)')
    parser.add_argument('--target', default=Config.SQLALCHEMY_DATABASE_URI, help='PostgreSQL URL (default: DATABASE_URL)')
    parser.add_argument('--replace', action='store_true', help='delete existing rows in the target tables first')
    return parser.parse_args()


def safe_url(engine):
    return engine.url.render_as_string(hide_password=True)


def read_rows(source, table):
    """All rows of a table, using only the columns both the model and the SQLite table have."""
    source_columns = {column['name'] for column in inspect(source).get_columns(table.name)}
    columns = [column for column in table.columns if column.name in source_columns]
    with source.connect() as connection:
        rows = [dict(row) for row in connection.execute(select(*columns)).mappings()]
    missing = [column.name for column in table.columns if column.name not in source_columns]
    return rows, missing


def check_rows(table, rows):
    """Problems PostgreSQL would reject. Fills in defaults for empty required fields where the model has one."""
    problems = []
    for row in rows:
        row_id = row.get('id', '?')
        for column in table.columns:
            value = row.get(column.name)
            if value is None and not column.nullable and not column.primary_key:
                default = column.default.arg if column.default is not None and column.default.is_scalar else None
                if default is not None:
                    row[column.name] = default
                else:
                    problems.append(f'{table.name} id={row_id}: "{column.name}" is empty but required')
            if isinstance(column.type, String) and column.type.length and isinstance(value, str) \
                    and len(value) > column.type.length:
                problems.append(f'{table.name} id={row_id}: "{column.name}" has {len(value)} characters '
                                f'(limit {column.type.length})')
    return problems


def fix_broken_links(tables, data):
    """SQLite does not enforce foreign keys, so rows can point at deleted records
    (e.g. a log entry of a deleted user). Optional links are cleared; a broken
    required link is reported as a problem."""
    notes, problems = [], []
    for table in tables:
        for foreign_key in table.foreign_keys:
            column, referenced = foreign_key.parent, foreign_key.column
            known_ids = {row[referenced.name] for row in data.get(referenced.table.name, [])}
            broken = [row for row in data[table.name]
                      if row.get(column.name) is not None and row[column.name] not in known_ids]
            if not broken:
                continue
            missing = sorted({row[column.name] for row in broken})
            if column.nullable:
                for row in broken:
                    row[column.name] = None
                notes.append(f'{table.name}.{column.name}: {len(broken)} rows pointed at deleted '
                             f'{referenced.table.name} ids {missing}; link cleared, rows kept')
            else:
                problems.append(f'{table.name}.{column.name}: {len(broken)} rows point at deleted '
                                f'{referenced.table.name} ids {missing} (required link)')
    return notes, problems


def reset_sequences(connection, tables):
    """Point each serial id counter at the highest copied id."""
    for table in tables:
        if 'id' not in table.columns or not table.columns['id'].primary_key:
            continue
        quoted = connection.dialect.identifier_preparer.quote(table.name)
        sequence = connection.execute(text('SELECT pg_get_serial_sequence(:t, :c)'),
                                      {'t': quoted, 'c': 'id'}).scalar()
        if not sequence:
            continue
        max_id = connection.execute(select(func.max(table.columns['id']))).scalar()
        if max_id:
            connection.execute(text('SELECT setval(:s, :v, true)'), {'s': sequence, 'v': max_id})
        else:
            connection.execute(text('SELECT setval(:s, 1, false)'), {'s': sequence})


def main():
    args = parse_args()
    if not args.target.startswith('postgresql'):
        sys.exit('Target is not PostgreSQL. Set DATABASE_URL in backend/.env or pass --target.')

    source = create_engine(args.source)
    target = create_engine(args.target)
    print(f'From: {safe_url(source)}')
    print(f'To:   {safe_url(target)}')

    source_tables = set(inspect(source).get_table_names())
    tables = [table for table in db.metadata.sorted_tables if table.name in source_tables]
    skipped = sorted(source_tables - {table.name for table in tables})
    if skipped:
        print(f'Not in models.py, not copied: {", ".join(skipped)}')

    db.metadata.create_all(target)

    with target.connect() as connection:
        existing = {table.name: connection.execute(select(func.count()).select_from(table)).scalar()
                    for table in tables}
    if any(existing.values()) and not args.replace:
        filled = ', '.join(f'{name} ({count})' for name, count in existing.items() if count)
        sys.exit(f'The target already has data in: {filled}.\n'
                 'Nothing was copied. Run again with --replace to empty those tables first.')

    data, problems = {}, []
    for table in tables:
        rows, missing = read_rows(source, table)
        if missing:
            print(f'  {table.name}: not in SQLite, left empty/default: {", ".join(missing)}')
        problems += check_rows(table, rows)
        data[table.name] = rows
    notes, link_problems = fix_broken_links(tables, data)
    problems += link_problems
    for note in notes:
        print('  ' + note)
    if problems:
        print('\nPostgreSQL would reject these rows. Fix them in SQLite, then run again:')
        for problem in problems:
            print('  - ' + problem)
        sys.exit(1)

    with target.begin() as connection:
        if args.replace:
            for table in reversed(tables):
                connection.execute(table.delete())
        for table in tables:
            if data[table.name]:
                connection.execute(table.insert(), data[table.name])
        reset_sequences(connection, tables)

    print('\nRows copied:')
    all_match = True
    with target.connect() as connection:
        for table in tables:
            copied = connection.execute(select(func.count()).select_from(table)).scalar()
            expected = len(data[table.name])
            all_match &= copied == expected
            print(f'  {table.name:22} {copied:6}  {"ok" if copied == expected else f"EXPECTED {expected}"}')
    print('\nDone: all tables match.' if all_match else '\nSome tables do not match; see above.')
    sys.exit(0 if all_match else 1)


if __name__ == '__main__':
    main()
