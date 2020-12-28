
from datetime import datetime

try:
    from google.cloud.storage import Client
except ImportError:
    Client = None

from flask import redirect

from . import BaseFileAdmin

import os.path as op


class GoogleStorage(object):
    """
        Storage object representing files on a Google Cloud Storage bucket.

        Usage::

            from flask_admin.contrib.fileadmin import BaseFileAdmin
            from flask_admin.contrib.fileadmin.gcloud import GoogleStorage

            class MyGCPAdmin(BaseFileAdmin):
                # Configure your class however you like
                pass

            fileadmin_view = MyGCPAdmin(storage=GoogleStorage(...))

    """

    separator = '/'

    def __init__(self, bucket_name, project=None, credentials=None):
        """
            Constructor

                :param bucket_name:
                    Name of the bucket that the files are on.

                :param project: the project which the client acts on behalf of. Will be
                                passed when creating a topic.  If not passed,
                                falls back to the default inferred from the environment.

                :param credentials: (Optional) The OAuth2 Credentials to use for this
                                    client. If not passed (and if no ``_http`` object is
                                    passed), falls back to the default inferred from the
                                    environment.

            Make sure the credentials have the correct permissions set up on
            Google Cloud or else GoogleStorage will return a 403 FORBIDDEN error.
        """
        if not Client:
            raise ValueError('Could not import google.cloud.storage. You can install '
                'google.cloud.storage by using pip install google-cloud-storage')

        connection = Client(
            project=project,
            credentials=credentials
        )
        self.bucket = connection.bucket(bucket_name)

    @classmethod
    def _get_blob_last_modified(cls, blob):
        last_modified = blob.updated
        tzinfo = last_modified.tzinfo
        epoch = last_modified - datetime(1970, 1, 1, tzinfo=tzinfo)
        return epoch.total_seconds()

    @classmethod
    def _ensure_blob_path(cls, path):
        if path is None:
            return None

        path_parts = path.split(op.sep)
        return cls.separator.join(path_parts).lstrip(cls.separator)

    def get_files(self, path, directory):
        if directory and path != directory:
            path = op.join(path, directory)

        path = self._ensure_blob_path(path)
        directory = self._ensure_blob_path(directory)

        path_parts = path.split(self.separator) if path else []
        num_path_parts = len(path_parts)
        folders = set()
        files = []

        for blob in self.bucket.list_blobs(prefix=path):
            blob_path_parts = blob.name.split(self.separator)
            name = blob_path_parts.pop()
            blob_is_file_at_current_level = blob_path_parts == path_parts
            blob_is_directory_file = name == ''

            if blob_is_file_at_current_level and not blob_is_directory_file:
                rel_path = blob.name
                is_dir = False
                size = blob.size
                last_modified = self._get_blob_last_modified(blob)
                files.append((name, rel_path, is_dir, size, last_modified))
            else:
                next_level_folder = blob_path_parts[:num_path_parts + 1]
                folder_name = self.separator.join(next_level_folder)
                folders.add(folder_name)

        folders.discard(directory)
        for folder in folders:
            name = folder.split(self.separator)[-1]
            rel_path = folder
            is_dir = True
            size = 0
            last_modified = 0
            files.append((name, rel_path, is_dir, size, last_modified))

        return files

    def is_dir(self, path):
        path = self._ensure_blob_path(path)

        num_blobs = 0
        for blob in self.bucket.list_blobs(prefix=path):
            blob_path_parts = blob.name.split(self.separator)
            is_explicit_directory = blob_path_parts[-1] == ''
            if is_explicit_directory:
                return True

            num_blobs += 1
            path_cannot_be_leaf = num_blobs >= 2
            if path_cannot_be_leaf:
                return True

        return False

    def path_exists(self, path):
        path = self._ensure_blob_path(path)

        if path == self.get_base_path():
            return True

        try:
            next(iter(self.bucket.list_blobs(prefix=path)))
        except StopIteration:
            return False
        else:
            return True

    def get_base_path(self):
        return ''

    def get_breadcrumbs(self, path):
        path = self._ensure_blob_path(path)

        accumulator = []
        breadcrumbs = []
        for folder in path.split(self.separator):
            accumulator.append(folder)
            breadcrumbs.append((folder, self.separator.join(accumulator)))
        return breadcrumbs

    def send_file(self, file_path):
        file_path = self._ensure_blob_path(file_path)
        blob = self.bucket.blob(file_path)
        if blob is None:
            raise ValueError()
        url = blob.generate_signed_url(3600)
        return redirect(url)

    def read_file(self, path):
        path = self._ensure_blob_path(path)
        blob = self.bucket.get_blob(path)
        return blob.download_as_string()

    def write_file(self, path, content):
        path = self._ensure_blob_path(path)
        blob = self.bucket.blob(path)
        blob_path_parts = blob.name.split(self.separator)
        name = blob_path_parts.pop()
        content_type = blob._get_content_type(None, name)
        blob.upload_from_string(content, content_type=content_type)

    def save_file(self, path, file_data):
        self.write_file(path, file_data)

    def delete_tree(self, directory):
        directory = self._ensure_blob_path(directory)
        blobs = self.bucket.list_blobs(prefix=directory)
        self.bucket.delete_blobs(list(blobs))

    def delete_file(self, file_path):
        file_path = self._ensure_blob_path(file_path)
        blob = self.bucket.blob(file_path)
        blob.delete()

    def make_dir(self, path, directory):
        path = self._ensure_blob_path(path)
        directory = self._ensure_blob_path(directory)
        path = self.separator.join([path, directory]).lstrip(self.separator)  \
            + self.separator
        blob = self.bucket.blob(path)
        blob.upload_from_string('')

    def rename_path(self, src, dst):
        src = self._ensure_blob_path(src)
        dst = self._ensure_blob_path(dst)
        blob = self.bucket.blob(src)

        if self.is_dir(src):
            dst = dst.lstrip(self.separator) + self.separator

        self.bucket.rename_blob(blob, dst)


class GcloudFileAdmin(BaseFileAdmin):
    """
        Simple Google Cloud Storage Service file-management interface.

            :param bucket_name:
                Name of the bucket that the files are on.

            :param project: the project which the client acts on behalf of. Will be
                            passed when creating a topic.  If not passed,
                            falls back to the default inferred from the environment.

            :param credentials: (Optional) The OAuth2 Credentials to use for this
                                client. If not passed (and if no ``_http`` object is
                                passed), falls back to the default inferred from the
                                environment.

        Sample usage::

            from flask_admin import Admin
            from flask_admin.contrib.fileadmin.gcloud import GCloudFileAdmin

            admin = Admin()

            admin.add_view(GcloudFileAdmin('files_bucket', 'my-gcloud-project')
    """

    def __init__(self, bucket_name, project, credentials, *args, **kwargs):
        storage = GoogleStorage(bucket_name, project, credentials)
        super(GcloudFileAdmin, self).__init__(*args, storage=storage, **kwargs)
