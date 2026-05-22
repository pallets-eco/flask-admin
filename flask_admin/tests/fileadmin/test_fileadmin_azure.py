import os
import typing as t
from uuid import uuid4

import pytest
from azure.storage.blob import BlobServiceClient

from flask_admin.contrib.fileadmin import azure
from flask_admin.contrib.fileadmin.azure import AzureFileAdmin

from .test_fileadmin import Base


class TestAzureFileAdmin(Base.FileAdminTests):
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self) -> t.Generator[None, t.Any, None]:
        azure_connection_string = os.getenv(
            "AZURE_STORAGE_CONNECTION_STRING",
            "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://localhost:10000/devstoreaccount1;",
        )
        self._container_name = f"fileadmin-tests-{uuid4()}"

        if not azure_connection_string or not self._container_name:
            raise ValueError("AzureFileAdmin test credentials not set, tests will fail")

        self._client = azure.BlobServiceClient.from_connection_string(
            azure_connection_string
        )
        self._client.create_container(self._container_name)
        file_name = "dummy.txt"
        file_path = os.path.join(self._test_files_root, file_name)
        blob_client = self._client.get_blob_client(self._container_name, file_name)
        with open(file_path, "rb") as file:
            blob_client.upload_blob(file)

        yield

        self._client.delete_container(self._container_name)

    def fileadmin_class(self) -> type[AzureFileAdmin]:
        return azure.AzureFileAdmin

    def fileadmin_args(
        self,
    ) -> tuple[tuple[BlobServiceClient, str], dict[t.Any, t.Any]]:
        return (self._client, self._container_name), {}
