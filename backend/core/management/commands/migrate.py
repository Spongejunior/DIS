from django.core.management.base import CommandError
from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import connections


def clear_broken_sqlite_links(connection):
    """SQLite never enforced foreign keys under Flask, so old rows can point at
    deleted records (e.g. the user of an old log entry). Django checks every
    link when it changes a SQLite schema, so those optional links are cleared
    first. Returns notes; raises for a broken required link."""
    with connection.cursor() as cursor:
        broken = cursor.execute('PRAGMA foreign_key_check').fetchall()
        notes, problems, cleared = [], [], {}
        for table, rowid, parent, fk_id in broken:
            fk = next(row for row in cursor.execute(f'PRAGMA foreign_key_list("{table}")') if row[0] == fk_id)
            column = fk[3]
            not_null = {row[1]: row[3] for row in cursor.execute(f'PRAGMA table_info("{table}")')}
            if not_null.get(column):
                problems.append(f'{table} row {rowid}: "{column}" points at a deleted {parent} (required link)')
                continue
            cursor.execute(f'UPDATE "{table}" SET "{column}" = NULL WHERE rowid = %s', [rowid])
            cleared[(table, column, parent)] = cleared.get((table, column, parent), 0) + 1
    if problems:
        raise CommandError('These rows point at deleted records. Fix them, then run migrate again:\n  '
                           + '\n  '.join(problems))
    for (table, column, parent), count in cleared.items():
        notes.append(f'{table}.{column}: {count} rows pointed at deleted {parent} records; link cleared, rows kept')
    return notes


class Command(MigrateCommand):
    def handle(self, *args, **options):
        connection = connections[options['database']]
        if connection.vendor == 'sqlite':
            for note in clear_broken_sqlite_links(connection):
                self.stdout.write(note)
        return super().handle(*args, **options)
