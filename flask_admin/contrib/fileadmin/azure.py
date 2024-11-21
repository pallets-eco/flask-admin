import os.path as op
from datetime import datetime
from datetime import timedelta

try:
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, BlobProperties
    from azure.core.exceptions import ResourceExistsError
except ImportError:
    BlobServiceClient = None

from flask import redirect

from . import BaseFileAdmin


class AzureStorage:
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

    _fakedir = ".dir"
    _copy_poll_interval_seconds = 1
    _send_file_lookback = timedelta(minutes=15)
    _send_file_validity = timedelta(hours=1)
    separator = "/"

    def __init__(self, container_name, connection_string):
        """
        Constructor

        :param container_name:
            Name of the container that the files are on.

        :param connection_string:
            Azure Blob Storage Connection String
        """

        if not BlobServiceClient:
            raise ValueError(
                "Could not import `azure.storage.blob`. "
                "Enable `azure-blob-storage` integration "
                "by installing `flask-admin[azure-blob-storage]`"
            )

        self._container_name = container_name
        self._connection_string = connection_string
        self.__client = None

    @property
    def _client(self):
        if BlobServiceClient is None:
            raise ValueError(
                "Could not import `azure.storage.blob`. "
                "Enable `azure-blob-storage` integration "
                "by installing `flask-admin[azure-blob-storage]`"
            )
        if not self.__client:
            self.__client = BlobServiceClient.from_connection_string(
                self._connection_string
            )
            try:
                self.__client.create_container(self._container_name)
            except ResourceExistsError:
                pass
        return self.__client

    @property
    def _container_client(self):
        return self._client.get_container_client(self._container_name)

    @classmethod
    def _get_blob_last_modified(cls, blob: BlobProperties):
        last_modified = blob.last_modified
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

        container_client = self._client.get_container_client(self._container_name)

        for blob in container_client.list_blobs(path):
            blob_path_parts = blob.name.split(self.separator)
            name = blob_path_parts.pop()

            blob_is_file_at_current_level = blob_path_parts == path_parts
            blob_is_directory_file = name == self._fakedir

            if blob_is_file_at_current_level and not blob_is_directory_file:
                rel_path = blob.name
                is_dir = False
                size = blob.size
                last_modified = self._get_blob_last_modified(blob)
                files.append((name, rel_path, is_dir, size, last_modified))
            else:
                next_level_folder = blob_path_parts[: num_path_parts + 1]
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

        blobs = self._container_client.list_blobs(name_starts_with=path)
        for blob in blobs:
            if blob.name != path:
                return True
        return False

    def path_exists(self, path):
        path = self._ensure_blob_path(path)

        if path == self.get_base_path():
            return True

        if path is None:
            return False

        # Return true if it exists as either a directory or a file
        for _ in self._container_client.list_blobs(name_starts_with=path):
            return True
        return False

    def get_base_path(self):
        return ""

    def get_breadcrumbs(self, path):
        path = self._ensure_blob_path(path)

        accumulator = []
        breadcrumbs = []
        if path is not None:
            for folder in path.split(self.separator):
                accumulator.append(folder)
                breadcrumbs.append((folder, self.separator.join(accumulator)))
        return breadcrumbs

    def send_file(self, file_path):
        file_path = self._ensure_blob_path(file_path)
        if file_path is None:
            raise ValueError()
        container_client = self._client.get_container_client(self._container_name)
        if len(list(container_client.list_blobs(file_path))) != 1:
            raise ValueError()

        now = datetime.utcnow()

        blob_client = self._client.get_blob_client(container=self._container_name, blob=file_path)
        url = blob_client.url
        account_name = self._connection_string.split(";")[1].split("=")[1]

        delegation_key_start_time = now
        delegation_key_expiry_time = delegation_key_start_time + timedelta(days=1)
        user_delegation_key = self._client.get_user_delegation_key(
            key_start_time=delegation_key_start_time,
            key_expiry_time=delegation_key_expiry_time
        )
        sas = generate_blob_sas(
            account_name=account_name,
            container_name=self._container_name,
            blob_name=file_path,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=now + self._send_file_validity,
            start=now - self._send_file_lookback,
        )

        return redirect(f"{url}?{sas}")

    def read_file(self, path):
        path = self._ensure_blob_path(path)
        if path is None:
            raise ValueError("No path provided")
        blob = self._container_client.get_blob_client(path).download_blob()
        return blob.readall()

    def write_file(self, path, content):
        path = self._ensure_blob_path(path)
        if path is None:
            raise ValueError("No path provided")
        self._container_client.upload_blob(path, content, overwrite=True)

    def save_file(self, path, file_data):
        path = self._ensure_blob_path(path)
        if path is None:
            raise ValueError("No path provided")
        self._container_client.upload_blob(path, file_data.stream)

    def delete_tree(self, directory):
        directory = self._ensure_blob_path(directory)
        
        for blob in self._container_client.list_blobs(directory):
            self._container_client.delete_blob(blob.name)

    def delete_file(self, file_path):
        file_path = self._ensure_blob_path(file_path)
        if file_path is None:
            raise ValueError("No path provided")
        self._container_client.delete_blob(file_path)

    def make_dir(self, path, directory):
        path = self._ensure_blob_path(path)
        directory = self._ensure_blob_path(directory)
        if path is None or directory is None:
            raise ValueError("No path provided")
        blob = self.separator.join([path, directory, self._fakedir])
        blob = blob.lstrip(self.separator)
        self._container_client.upload_blob(blob, b"")

    def _copy_blob(self, src, dst):
        src_client = self._container_client.get_blob_client(src)
        dst_blob = self._container_client.get_blob_client(dst)
        dst_blob.start_copy_from_url(src_client.url, requires_sync=True)

    def _rename_file(self, src, dst):
        self._copy_blob(src, dst)
        self.delete_file(src)

    def _rename_directory(self, src, dst):
        for blob in self._container_client.list_blobs(src):
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
        super().__init__(*args, storage=storage, **kwargs)
