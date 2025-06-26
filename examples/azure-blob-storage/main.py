import logging

from azure.storage.blob import BlobServiceClient
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin.azure import AzureFileAdmin
from flask_babel import Babel
from testcontainers.azurite import AzuriteContainer

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app, name="Example: Azure Blob Storage File Admin")
babel = Babel(app)


if __name__ == "__main__":
    with AzuriteContainer() as azurite_container:
        connection_string = azurite_container.get_connection_string()
        client = BlobServiceClient.from_connection_string(
            connection_string, api_version="2019-12-12"
        )
        admin.add_view(
            AzureFileAdmin(
                blob_service_client=client,
                container_name="fileadmin-tests",
            )
        )

        app.run(debug=True)
