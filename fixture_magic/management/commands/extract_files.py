try:
    import json
except ImportError:
    from django.utils import simplejson as json

import ijson
from django.core.management.base import BaseCommand

from fixture_magic.utils import extract_files_from_fixture


class Command(BaseCommand):
    """
    Extract all files from a fixture and move them to a temporary folder.
    """
    help = 'Extract all files from a fixture and move them to a temporary folder.'

    def add_arguments(self, parser):
        parser.add_argument('fixture', metavar='fixture',
                            help='The fixture to process.')
        parser.add_argument('--exclude-fields', '-e',
                            default='{}',
                            help='JSON object of excluded fields per model: '
                                 '\'{"app_label.model_name": ["field1", ...]}\'')

    def handle(self, *args, **options):
        fixture_path = options['fixture']
        exclude_fields = json.loads(options['exclude_fields'])
        with open(fixture_path, 'r') as f:
            fixture_data = ijson.items(f, 'item')
            tmp_dir = extract_files_from_fixture(fixture_data, exclude_fields)

        self.stdout.write(tmp_dir)
