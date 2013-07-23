def make_gridfs_args(value):
    args = {
        'id': value.grid_id,
        'coll': value.collection_name
    }

    if value.db_alias != 'default':
        args['db'] = value.db_alias

    return args


def make_thumb_args(value):
    if getattr(value, 'thumbnail', None):
        args = {
            'id': value.thumbnail._id,
            'coll': value.collection_name
        }

        if value.db_alias != 'default':
            args['db'] = value.db_alias

        return args
    else:
        return make_gridfs_args(value)
