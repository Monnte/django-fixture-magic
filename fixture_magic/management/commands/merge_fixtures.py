import sys

import ijson
from django.core.serializers.json import DjangoJSONEncoder

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.core.management.base import BaseCommand

from fixture_magic.utils import get_proxy_children_map


def write_json(output):
    try:
        # check our json import supports sorting keys
        json.dumps([1], sort_keys=True)
    except TypeError:
        print(json.dumps(output, indent=0, cls=DjangoJSONEncoder), file=sys.stdout)
    else:
        print(json.dumps(output, sort_keys=True, indent=0, cls=DjangoJSONEncoder), file=sys.stdout)


class Command(BaseCommand):
    help = "Merge a series of fixtures and remove duplicates."

    def add_arguments(self, parser):
        parser.add_argument(
            "args", metavar="files", nargs="+", help="One or more fixture."
        )

    def handle(self, *files, **options):
        """
        Load multiple Django-style JSON fixture files. Deduplicate objects based on their
        primary key and base model (resolving proxy models).

        Proxy models are handled using a proxy-to-base map. When multiple objects with the same
        PK are found across proxy and base models, proxy models take precedence.
        """
        proxy_children_map = get_proxy_children_map()
        proxy_parents = {
            child: parent
            for parent, children in proxy_children_map.items()
            for child in children
        }

        final_objs = {}
        for f in files:
            with open(f, "r") as f_handle:
                for obj in ijson.items(f_handle, "item"):
                    model = obj['model']
                    pk = obj['pk']
                    base_model = proxy_parents.get(model, model)
                    key = (base_model, pk)

                    if (key not in final_objs) or (model in proxy_parents):
                        final_objs[key] = obj

        output = list(final_objs.values())
        write_json(output)
