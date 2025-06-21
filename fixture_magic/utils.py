import os
import shutil
import tempfile

from django.conf import settings
from django.db import models

try:
    from django.apps import apps
except ImportError:
    # fallback for old django
    from django.db.models import loading as apps

serialize_me = []
seen = {}


def reorder_json(data, models, ordering_cond=None):
    """Reorders JSON (actually a list of model dicts).

    This is useful if you need fixtures for one model to be loaded before
    another.

    :param data: the input JSON to sort
    :param models: the desired order for each model type
    :param ordering_cond: a key to sort within a model
    :return: the ordered JSON
    """
    if ordering_cond is None:
        ordering_cond = {}
    output = []
    bucket = {}
    others = []

    for model in models:
        bucket[model] = []

    for object in data:
        if object['model'] in bucket.keys():
            bucket[object['model']].append(object)
        else:
            others.append(object)
    for model in models:
        if model in ordering_cond:
            bucket[model].sort(key=ordering_cond[model])
        output.extend(bucket[model])

    output.extend(others)
    return output


def get_fields(obj, exclude_fields=None):
    if exclude_fields is None:
        exclude_fields = {}
    try:
        key = obj._meta.label.lower()
        to_exclude = exclude_fields.get(key, [])
        return [f for f in obj._meta.fields if f.name not in to_exclude]
    except AttributeError:
        return []


def get_m2m(obj, exclude_fields=None):
    if exclude_fields is None:
        exclude_fields = {}
    try:
        key = obj._meta.label.lower()
        to_exclude = exclude_fields.get(key, [])
        return [f for f in obj._meta.many_to_many if f.name not in to_exclude]
    except AttributeError:
        return []


def serialize_fully(exclude_fields):
    index = 0
    exclude_fields = exclude_fields or {}

    while index < len(serialize_me):
        for field in get_fields(serialize_me[index], exclude_fields):
            if isinstance(field, models.ForeignKey):
                try:
                    add_to_serialize_list(
                        [serialize_me[index].__getattribute__(field.name)])
                except Exception:
                    pass
        for field in get_m2m(serialize_me[index], exclude_fields):
            add_to_serialize_list(
                serialize_me[index].__getattribute__(field.name).all())

        index += 1

    serialize_me.reverse()


def add_to_serialize_list(objs):
    for obj in objs:
        if obj is None:
            continue
        if not hasattr(obj, '_meta'):
            add_to_serialize_list(obj)
            continue

        meta = obj._meta.proxy_for_model._meta if obj._meta.proxy else obj._meta
        model_name = getattr(meta, 'model_name',
                             getattr(meta, 'module_name', None))
        key = "%s:%s:%s" % (obj._meta.app_label, model_name, obj.pk)

        if key not in seen:
            serialize_me.append(obj)
            seen[key] = 1


def extract_files_from_fixture(fixture_data, exclude_fields=None):
    """
    Extracts all files from a fixture, copies them to a temporary directory,
    and returns the path to that directory.
    """
    if exclude_fields is None:
        exclude_fields = {}

    tmp_dir = tempfile.mkdtemp()
    model_file_fields = {}

    for obj in fixture_data:
        try:
            model_class = apps.get_model(obj['model'])
            model_label = model_class._meta.label.lower()
        except (LookupError, AttributeError):
            continue

        if model_label not in model_file_fields:
            file_fields = []
            for field in model_class._meta.fields:
                if isinstance(field, models.FileField):
                    to_exclude = exclude_fields.get(model_label, [])
                    if field.name not in to_exclude:
                        file_fields.append(field.name)
            model_file_fields[model_label] = file_fields

        if not model_file_fields.get(model_label):
            continue

        for field_name in model_file_fields[model_label]:
            file_path = obj.get('fields', {}).get(field_name)

            if file_path:
                media_root = getattr(settings, 'MEDIA_ROOT', '')
                source_path = os.path.join(media_root, file_path)

                if os.path.exists(source_path) and os.path.isfile(source_path):
                    try:
                        destination_path = os.path.join(tmp_dir, file_path)
                        destination_dir = os.path.dirname(destination_path)
                        if not os.path.exists(destination_dir):
                            os.makedirs(destination_dir)

                        shutil.copy(source_path, destination_path)
                    except (IOError, os.error):
                        pass
    return tmp_dir
