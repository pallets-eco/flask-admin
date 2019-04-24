import os.path as op
from os import getenv
from uuid import uuid4

from nose import SkipTest

from flask_admin.contrib.fileadmin import azure

from .test_fileadmin import Base


class AzureFileAdminTests(Base.FileAdminTests):
    _test_storage = getenv('AZURE_STORAGE_CONNECTION_STRING')

    def setUp(self):
        if not azure.BlockBlobService:
            raise SkipTest('AzureFileAdmin dependencies not installed')

        self._container_name = 'fileadmin-tests-%s' % uuid4()

        if not self._test_storage or not self._container_name:
            raise SkipTest('AzureFileAdmin test credentials not set')

        client = azure.BlockBlobService(connection_string=self._test_storage)
        client.create_container(self._container_name)
        dummy = op.join(self._test_files_root, 'dummy.txt')
        client.create_blob_from_path(self._container_name, 'dummy.txt', dummy)

    def tearDown(self):
        client = azure.BlockBlobService(connection_string=self._test_storage)
        client.delete_container(self._container_name)

    def fileadmin_class(self):
        return azure.AzureFileAdmin

    def fileadmin_args(self):
        return (self._container_name, self._test_storage), {}
