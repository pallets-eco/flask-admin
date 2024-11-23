import os

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin.azure import AzureFileAdmin
from flask_babel import Babel

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app)
babel = Babel(app)
file_admin = AzureFileAdmin(
    container_name="fileadmin-tests",
    connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
)
admin.add_view(file_admin)

if __name__ == "__main__":
    app.run(debug=True)
