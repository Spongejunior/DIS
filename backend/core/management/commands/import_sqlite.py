"""Copy all data from the old SQLite database into PostgreSQL.

Usage (from the backend/ folder, after ``python manage.py migrate``):

    python manage.py import_sqlite                 # target = DATABASE_URL from .env
    python manage.py import_sqlite --source path/to/database.db
    python manage.py import_sqlite --replace       # empty the target tables first

What it does:
1. Checks every row first, because PostgreSQL is stricter than SQLite: text
   longer than its column allows, or an empty required field, stops the copy
   with a list of the problem rows. Nothing is written in that case.
   Rows that point at a deleted record (SQLite never enforced these links)
   keep the row and lose the link when the link is optional, such as the user
   on an old log entry.
2. Copies every table (users first, then the rows that refer to them) in one
   transaction: either everything is copied or nothing is.
3. Moves each table's id counter past the copied ids, so new rows get new ids.
4. Compares row counts between the two databases.

The SQLite file is only read, never changed.
"""
import sqlite3
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, models, transaction

from core.models import (
    BreedingRecord, Configuration, DiseaseLibrary, FarmerVeterinarian, ModelVersion, MortalityReport,
    Notification, PerformanceMetric, Prediction, Report, SymptomReport, SystemLog, Treatment, User,
    as_malawi_time,
)

# Referenced tables before the tables that point at them.
MODELS = [
    User, DiseaseLibrary, PerformanceMetric, ModelVersion, Configuration, FarmerVeterinarian,
    SymptomReport, MortalityReport, BreedingRecord, SystemLog, Report, Notification, Prediction, Treatment,
]


def stored_fields(model):
    return [field for field in model._meta.concrete_fields if field.column]


def convert(field, value):
    """A SQLite value as the Python value the field holds."""
    if value is None or field.is_relation:
        return value
    value = field.to_python(value)
    if isinstance(value, datetime):
        value = as_malawi_time(value)
    return value


class Command(BaseCommand):
    help = 'Copy all data from the old SQLite database (instance/database.db) into PostgreSQL.'

    def add_arguments(self, parser):
        parser.add_argument('--source', default=str(settings.BASE_DIR / 'instance' / 'database.db'),
                            help='SQLite file (default: instance/database.db)')
        parser.add_argument('--replace', action='store_true',
                            help='delete existing rows in the target tables first')

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            raise CommandError('Target is not PostgreSQL. Set DATABASE_URL in backend/.env.')
        target = connection.settings_dict
        self.stdout.write(f"From: {options['source']}")
        self.stdout.write(f"To:   postgresql://{target['HOST']}:{target['PORT'] or 5432}/{target['NAME']}")

        try:
            source = sqlite3.connect(f"file:{options['source']}?mode=ro", uri=True)
        except sqlite3.Error as exc:
            raise CommandError(f'Cannot open the SQLite file: {exc}')
        source.row_factory = sqlite3.Row
        source_tables = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        models_to_copy = [model for model in MODELS if model._meta.db_table in source_tables]

        existing = {model._meta.db_table: model.objects.count() for model in models_to_copy}
        if any(existing.values()) and not options['replace']:
            filled = ', '.join(f'{name} ({count})' for name, count in existing.items() if count)
            raise CommandError(f'The target already has data in: {filled}.\n'
                               'Nothing was copied. Run again with --replace to empty those tables first.')

        data, problems = {}, []
        for model in models_to_copy:
            rows, missing = self.read_rows(source, model)
            if missing:
                self.stdout.write(f'  {model._meta.db_table}: not in SQLite, left empty/default: {", ".join(missing)}')
            problems += self.check_rows(model, rows)
            data[model] = rows
        notes, link_problems = self.fix_broken_links(data)
        problems += link_problems
        for note in notes:
            self.stdout.write('  ' + note)
        if problems:
            self.stdout.write('\nPostgreSQL would reject these rows. Fix them in SQLite, then run again:')
            for problem in problems:
                self.stdout.write('  - ' + problem)
            raise CommandError('Nothing was copied.')

        with transaction.atomic():
            if options['replace']:
                with connection.cursor() as cursor:
                    for model in reversed(MODELS):
                        cursor.execute(f'DELETE FROM {connection.ops.quote_name(model._meta.db_table)}')
            for model in models_to_copy:
                objects = [model(**{field.attname: row[field.column] for field in stored_fields(model)
                                    if field.column in row}) for row in data[model]]
                model.objects.bulk_create(objects, batch_size=500)
            with connection.cursor() as cursor:
                for statement in connection.ops.sequence_reset_sql(no_style(), models_to_copy):
                    cursor.execute(statement)

        self.stdout.write('\nRows copied:')
        all_match = True
        for model in models_to_copy:
            copied, expected = model.objects.count(), len(data[model])
            all_match &= copied == expected
            status = 'ok' if copied == expected else f'EXPECTED {expected}'
            self.stdout.write(f'  {model._meta.db_table:22} {copied:6}  {status}')
        if not all_match:
            raise CommandError('Some tables do not match; see above.')
        self.stdout.write(self.style.SUCCESS('\nDone: all tables match.'))

    def read_rows(self, source, model):
        """All rows of a table, using only the columns both the model and the SQLite table have."""
        table = model._meta.db_table
        source_columns = {row[1] for row in source.execute(f'PRAGMA table_info("{table}")')}
        fields = [field for field in stored_fields(model) if field.column in source_columns]
        columns = ', '.join(f'"{field.column}"' for field in fields)
        rows = [
            {field.column: convert(field, row[field.column]) for field in fields}
            for row in source.execute(f'SELECT {columns} FROM "{table}"')
        ]
        missing = [field.column for field in stored_fields(model) if field.column not in source_columns]
        return rows, missing

    def check_rows(self, model, rows):
        """Problems PostgreSQL would reject. Fills in defaults for empty required fields where the model has one."""
        problems = []
        table = model._meta.db_table
        for row in rows:
            row_id = row.get('id', '?')
            for field in stored_fields(model):
                value = row.get(field.column)
                if value is None and not field.null and not field.primary_key and field.column in row:
                    if field.has_default() and not callable(field.default):
                        row[field.column] = field.default
                    else:
                        problems.append(f'{table} id={row_id}: "{field.column}" is empty but required')
                if isinstance(field, models.CharField) and field.max_length and isinstance(value, str) \
                        and len(value) > field.max_length:
                    problems.append(f'{table} id={row_id}: "{field.column}" has {len(value)} characters '
                                    f'(limit {field.max_length})')
        return problems

    def fix_broken_links(self, data):
        """SQLite does not enforce foreign keys, so rows can point at deleted records
        (e.g. a log entry of a deleted user). Optional links are cleared; a broken
        required link is reported as a problem."""
        notes, problems = [], []
        for model, rows in data.items():
            for field in stored_fields(model):
                if not isinstance(field, models.ForeignKey):
                    continue
                referenced = field.related_model
                known_ids = {row['id'] for row in data.get(referenced, [])}
                broken = [row for row in rows
                          if row.get(field.column) is not None and row[field.column] not in known_ids]
                if not broken:
                    continue
                missing = sorted({row[field.column] for row in broken})
                where = f'{model._meta.db_table}.{field.column}'
                if field.null:
                    for row in broken:
                        row[field.column] = None
                    notes.append(f'{where}: {len(broken)} rows pointed at deleted '
                                 f'{referenced._meta.db_table} ids {missing}; link cleared, rows kept')
                else:
                    problems.append(f'{where}: {len(broken)} rows point at deleted '
                                    f'{referenced._meta.db_table} ids {missing} (required link)')
        return notes, problems
