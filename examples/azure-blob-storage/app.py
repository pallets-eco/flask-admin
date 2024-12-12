import logging
import os

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin.azure import AzureFileAdmin
from flask_babel import Babel

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


admin = Admin(app)
babel = Babel(app)

if account_name := os.getenv("AZURE_STORAGE_ACCOUNT_URL"):
    # https://learn.microsoft.com/azure/storage/blobs/storage-blob-python-get-started?tabs=azure-ad#authorize-access-and-connect-to-blob-storage
    logging.info("Connecting to Azure Blob storage with keyless auth")
    client = BlobServiceClient(account_name, credential=DefaultAzureCredential())
elif conn_str := os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
    logging.info("Connecting to Azure Blob storage with connection string.")
    client = BlobServiceClient.from_connection_string(conn_str)

file_admin = AzureFileAdmin(
    blob_service_client=client,
    container_name="fileadmin-tests",
)
admin.add_view(file_admin)

if __name__ == "__main__":
    app.run(debug=True)
