from peewee import PrimaryKeyField


def get_primary_key(model):
    for n, f in model._meta.get_sorted_fields():
        if type(f) == PrimaryKeyField:
            return n
