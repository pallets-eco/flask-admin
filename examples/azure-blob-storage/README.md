# Azure Blob Storage Example

Flask-Admin example for an Azure Blob Storage account.

To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin/examples/azure-storage

2. Create and activate a virtual environment::

    python -m venv venv
    source venv/bin/activate

3. Install requirements::

    pip install -r requirements.txt

4. Either run the Azurite Blob Storage emulator or create an actual Azure Blob Storage account. Set this environment variable:

    export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"

    The value below is the default for the Azurite emulator.

4. Run the application::

    python app.py
