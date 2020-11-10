import time

try:
    from boto import s3
    from boto.s3.prefix import Prefix
    from boto.s3.key import Key
except ImportError:
    s3 = None

from flask import redirect
from flask_admin.babel import gettext

from . import BaseFileAdmin


class S3Storage(object):
    """
        Storage object representing files on an Amazon S3 bucket.

        Usage::

            from flask_admin.contrib.fileadmin import BaseFileAdmin
            from flask_admin.contrib.fileadmin.s3 import S3Storage

            class MyS3Admin(BaseFileAdmin):
                # Configure your class however you like
                pass

            fileadmin_view = MyS3Admin(storage=S3Storage(...))

    """

    def __init__(self, bucket_name, region, aws_access_key_id,
                 aws_secret_access_key):
        """
            Constructor

                :param bucket_name:
                    Name of the bucket that the files are on.

                :param region:
                    Region that the bucket is located

                :param aws_access_key_id:
                    AWS Access Key ID

                :param aws_secret_access_key:
                    AWS Secret Access Key

            Make sure the credentials have the correct permissions set up on
            Amazon or else S3 will return a 403 FORBIDDEN error.
        """

        if not s3:
            raise ValueError('Could not import boto. You can install boto by '
                             'using pip install boto')

        connection = s3.connect_to_region(
            region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.bucket = connection.get_bucket(bucket_name)
        self.separator = '/'

    def get_files(self, path, directory):
        def _strip_path(name, path):
            if name.startswith(path):
                return name.replace(path, '', 1)
            return name

        def _remove_trailing_slash(name):
            return name[:-1]

        def _iso_to_epoch(timestamp):
            dt = time.strptime(timestamp.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            return int(time.mktime(dt))

        files = []
        directories = []
        if path and not path.endswith(self.separator):
            path += self.separator
        for key in self.bucket.list(path, self.separator):
            if key.name == path:
                continue
            if isinstance(key, Prefix):
                name = _remove_trailing_slash(_strip_path(key.name, path))
                key_name = _remove_trailing_slash(key.name)
                directories.append((name, key_name, True, 0, 0))
            else:
                last_modified = _iso_to_epoch(key.last_modified)
                name = _strip_path(key.name, path)
                files.append((name, key.name, False, key.size, last_modified))
        return directories + files

    def _get_bucket_list_prefix(self, path):
        parts = path.split(self.separator)
        if len(parts) == 1:
            search = ''
        else:
            search = self.separator.join(parts[:-1]) + self.separator
        return search

    def _get_path_keys(self, path):
        search = self._get_bucket_list_prefix(path)
        return {key.name for key in self.bucket.list(search, self.separator)}

    def is_dir(self, path):
        keys = self._get_path_keys(path)
        return path + self.separator in keys

    def path_exists(self, path):
        if path == '':
            return True
        keys = self._get_path_keys(path)
        return path in keys or (path + self.separator) in keys

    def get_base_path(self):
        return ''

    def get_breadcrumbs(self, path):
        accumulator = []
        breadcrumbs = []
        for n in path.split(self.separator):
            accumulator.append(n)
            breadcrumbs.append((n, self.separator.join(accumulator)))
        return breadcrumbs

    def send_file(self, file_path):
        key = self.bucket.get_key(file_path)
        if key is None:
            raise ValueError()
        return redirect(key.generate_url(3600))

    def save_file(self, path, file_data):
        key = Key(self.bucket, path)
        headers = {
            'Content-Type' : file_data.content_type,
        }
        key.set_contents_from_file(file_data.stream, headers=headers)

    def delete_tree(self, directory):
        self._check_empty_directory(directory)
        self.bucket.delete_key(directory + self.separator)

    def delete_file(self, file_path):
        self.bucket.delete_key(file_path)

    def make_dir(self, path, directory):
        dir_path = self.separator.join([path, (directory + self.separator)])
        key = Key(self.bucket, dir_path)
        key.set_contents_from_string('')

    def _check_empty_directory(self, path):
        if not self._is_directory_empty(path):
            raise ValueError(gettext('Cannot operate on non empty '
                                     'directories'))
        return True

    def rename_path(self, src, dst):
        if self.is_dir(src):
            self._check_empty_directory(src)
            src += self.separator
            dst += self.separator
        self.bucket.copy_key(dst, self.bucket.name, src)
        self.delete_file(src)

    def _is_directory_empty(self, path):
        keys = self._get_path_keys(path + self.separator)
        return len(keys) == 1

    def read_file(self, path):
        key = Key(self.bucket, path)
        return key.get_contents_as_string()

    def write_file(self, path, content):
        key = Key(self.bucket, path)
        key.set_contents_from_file(content)


class S3FileAdmin(BaseFileAdmin):
    """
        Simple Amazon Simple Storage Service file-management interface.

            :param bucket_name:
                Name of the bucket that the files are on.

            :param region:
                Region that the bucket is located

            :param aws_access_key_id:
                AWS Access Key ID

            :param aws_secret_access_key:
                AWS Secret Access Key

        Sample usage::

            from flask_admin import Admin
            from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

            admin = Admin()

            admin.add_view(S3FileAdmin('files_bucket', 'us-east-1', 'key_id', 'secret_key')
    """

    def __init__(self, bucket_name, region, aws_access_key_id,
                 aws_secret_access_key, *args, **kwargs):
        storage = S3Storage(bucket_name, region, aws_access_key_id,
                            aws_secret_access_key)
        super(S3FileAdmin, self).__init__(*args, storage=storage, **kwargs)
