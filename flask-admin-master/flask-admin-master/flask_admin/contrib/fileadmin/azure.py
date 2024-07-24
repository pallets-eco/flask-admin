from __future__ import absolute_import
from datetime import datetime
from datetime import timedelta
from time import sleep
import os.path as op

try:
    from azure.storage.blob import BlobPermissions
    from azure.storage.blob import BlockBlobService
except ImportError:
    BlobPermissions = BlockBlobService = None

from flask import redirect

from . import BaseFileAdmin


class AzureStorage(object):
    """
        Storage object representing files on an Azure Storage container.

        Usage::

            from flask_admin.contrib.fileadmin import BaseFileAdmin
            from flask_admin.contrib.fileadmin.azure import AzureStorage

            class MyAzureAdmin(BaseFileAdmin):
                # Configure your class however you like
                pass

            fileadmin_view = MyAzureAdmin(storage=AzureStorage(...))

    """
    _fakedir = '.dir'
    _copy_poll_interval_seconds = 1
    _send_file_lookback = timedelta(minutes=15)
    _send_file_validity = timedelta(hours=1)
    separator = '/'

    def __init__(self, container_name, connection_string):
        """
            Constructor

            :param container_name:
                Name of the container that the files are on.

            :param connection_string:
                Azure Blob Storage Connection String
        """

        if not BlockBlobService:
            raise ValueError('Could not import Azure Blob Storage SDK. '
                             'You can install the SDK using '
                             'pip install azure-storage-blob')

        self._container_name = container_name
        self._connection_string = connection_string
        self.__client = None

    @property
    def _client(self):
        if not self.__client:
            self.__client = BlockBlobService(
                connection_string=self._connection_string)
            self.__client.create_container(
                self._container_name, fail_on_exist=False)
        return self.__client

    @classmethod
    def _get_blob_last_modified(cls, blob):
        last_modified = blob.properties.last_modified
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

        for blob in self._client.list_blobs(self._container_name, path):
            blob_path_parts = blob.name.split(self.separator)
            name = blob_path_parts.pop()

            blob_is_file_at_current_level = blob_path_parts == path_parts
            blob_is_directory_file = name == self._fakedir

            if blob_is_file_at_current_level and not blob_is_directory_file:
                rel_path = blob.name
                is_dir = False
                size = blob.properties.content_length
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
        for blob in self._client.list_blobs(self._container_name, path):
            blob_path_parts = blob.name.split(self.separator)
            is_explicit_directory = blob_path_parts[-1] == self._fakedir
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
            next(iter(self._client.list_blobs(self._container_name, path)))
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

        if not self._client.exists(self._container_name, file_path):
            raise ValueError()

        now = datetime.utcnow()
        url = self._client.make_blob_url(self._container_name, file_path)
        sas = self._client.generate_blob_shared_access_signature(
            self._container_name, file_path,
            BlobPermissions.READ,
            expiry=now + self._send_file_validity,
            start=now - self._send_file_lookback)
        return redirect('%s?%s' % (url, sas))

    def read_file(self, path):
        path = self._ensure_blob_path(path)

        blob = self._client.get_blob_to_bytes(self._container_name, path)
        return blob.content

    def write_file(self, path, content):
        path = self._ensure_blob_path(path)

        self._client.create_blob_from_text(self._container_name, path, content)

    def save_file(self, path, file_data):
        path = self._ensure_blob_path(path)

        self._client.create_blob_from_stream(self._container_name, path,
                                             file_data.stream)

    def delete_tree(self, directory):
        directory = self._ensure_blob_path(directory)

        for blob in self._client.list_blobs(self._container_name, directory):
            self._client.delete_blob(self._container_name, blob.name)

    def delete_file(self, file_path):
        file_path = self._ensure_blob_path(file_path)

        self._client.delete_blob(self._container_name, file_path)

    def make_dir(self, path, directory):
        path = self._ensure_blob_path(path)
        directory = self._ensure_blob_path(directory)

        blob = self.separator.join([path, directory, self._fakedir])
        blob = blob.lstrip(self.separator)
        self._client.create_blob_from_text(self._container_name, blob, '')

    def _copy_blob(self, src, dst):
        src_url = self._client.make_blob_url(self._container_name, src)
        copy = self._client.copy_blob(self._container_name, dst, src_url)
        while copy.status != 'success':
            sleep(self._copy_poll_interval_seconds)
            copy = self._client.get_blob_properties(
                self._container_name, dst).properties.copy

    def _rename_file(self, src, dst):
        self._copy_blob(src, dst)
        self.delete_file(src)

    def _rename_directory(self, src, dst):
        for blob in self._client.list_blobs(self._container_name, src):
            self._rename_file(blob.name, blob.name.replace(src, dst, 1))

    def rename_path(self, src, dst):
        src = self._ensure_blob_path(src)
        dst = self._ensure_blob_path(dst)

        if self.is_dir(src):
            self._rename_directory(src, dst)
        else:
            self._rename_file(src, dst)


class AzureFileAdmin(BaseFileAdmin):
    """
        Simple Azure Blob Storage file-management interface.

            :param container_name:
                Name of the container that the files are on.

            :param connection_string:
                Azure Blob Storage Connection String

        Sample usage::

            from flask_admin import Admin
            from flask_admin.contrib.fileadmin.azure import AzureFileAdmin

            admin = Admin()

            admin.add_view(AzureFileAdmin('files_container', 'my-connection-string')
    """

    def __init__(self, container_name, connection_string, *args, **kwargs):
        storage = AzureStorage(container_name, connection_string)
        super(AzureFileAdmin, self).__init__(*args, storage=storage, **kwargs)
