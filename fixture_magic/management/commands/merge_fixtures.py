import sys

import ijson

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.core.management.base import BaseCommand


def write_json(output):
    try:
        # check our json import supports sorting keys
        json.dumps([1], sort_keys=True)
    except TypeError:
        print(json.dumps(output, indent=0), file=sys.stdout)
    else:
        print(json.dumps(output, sort_keys=True, indent=0), file=sys.stdout)


class Command(BaseCommand):
    help = "Merge a series of fixtures and remove duplicates."

    def add_arguments(self, parser):
        parser.add_argument(
            "args", metavar="files", nargs="+", help="One or more fixture."
        )

    def handle(self, *files, **options):
        """
        Load a bunch of json files.  Store the pk/model in a seen dictionary.
        Add all the unseen objects into output.
        """
        output = []
        seen = {}

        for f in files:
            with open(f, "r") as f_handle:
                for obj in ijson.items(f_handle, "item"):
                    key = "%s|%s" % (obj["model"], obj["pk"])
                    if key not in seen:
                        seen[key] = 1
                        output.append(obj)

        write_json(output)
