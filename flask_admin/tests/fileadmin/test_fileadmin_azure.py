import os
from uuid import uuid4

import pytest

from flask_admin.contrib.fileadmin import azure

from .test_fileadmin import Base


class TestAzureFileAdmin(Base.FileAdminTests):
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        TEST_STORAGE = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self._container_name = f"fileadmin-tests-{uuid4()}"

        if not TEST_STORAGE or not self._container_name:
            raise ValueError("AzureFileAdmin test credentials not set, tests will fail")

        self._client = azure.BlobServiceClient.from_connection_string(TEST_STORAGE)
        self._client.create_container(self._container_name)
        file_name = "dummy.txt"
        file_path = os.path.join(self._test_files_root, file_name)
        blob_client = self._client.get_blob_client(self._container_name, file_name)
        with open(file_path, "rb") as file:
            blob_client.upload_blob(file)

        yield

        self._client.delete_container(self._container_name)

    def fileadmin_class(self):
        return azure.AzureFileAdmin

    def fileadmin_args(self):
        return (self._client, self._container_name), {}
