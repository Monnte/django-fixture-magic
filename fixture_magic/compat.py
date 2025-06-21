def get_all_related_objects(model, exclude_fields=None):
    if exclude_fields is None:
        exclude_fields = {}
    key = model._meta.label.lower()
    to_exclude = exclude_fields.get(key, [])

    return [
        f for f in model._meta.get_fields() if
        (f.one_to_many or f.one_to_one) and
        f.auto_created and not f.concrete and f.name not in to_exclude
    ]
