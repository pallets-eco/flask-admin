# Azure Blob Storage Example

Flask-Admin example for an Azure Blob Storage account.

If you opened this repository in GitHub Codespaces or a Dev Container with the ["flask-admin tests" configuration](/.devcontainer/tests/devcontainer.json), you can jump straight to step 4.

To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin/examples/azure-blob-storage

2. Create and activate a virtual environment::

    python -m venv venv
    source venv/bin/activate

3. Configure a connection to an Azure Blob storage account or local emulator.

    To connect to the Azurite Blob Storage Emulator, install Azurite and set the following environment variable:

    export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"

    To connect to an Azure Blob Storage account, set the `AZURE_STORAGE_ACCOUNT_URL`. If you set that, the example assumes you are using keyless authentication, so you will need to be logged in via the Azure CLI.

4. Install requirements::

    pip install -r requirements.txt

5. Run the application::

    python app.py
