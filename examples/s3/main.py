import os
from io import BytesIO

import boto3
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin
from flask_babel import Babel
from testcontainers.localstack import LocalStackContainer

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app, name="Example: S3 File Admin")
babel = Babel(app)


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


def create_bucket(s3_client, bucket_name):
    # Create S3 bucket
    s3_client.create_bucket(Bucket=bucket_name)

    s3_client.upload_fileobj(
        BytesIO(b"abcdef"),
        bucket_name,
        "some-file",
        ExtraArgs={"ContentType": "text/plain"},
    )

    s3_client.upload_fileobj(
        BytesIO(b"abcdef"),
        bucket_name,
        "some-directory/some-file",
        ExtraArgs={"ContentType": "text/plain"},
    )

    s3_client.upload_fileobj(
        BytesIO(b"abcdef"),
        bucket_name,
        "some-directory/yy/another-file",
        ExtraArgs={"ContentType": "text/plain"},
    )


# Add Local Directory view
admin.add_view(FileAdmin("localdir", name="Local Dir"))

if __name__ == "__main__":
    with LocalStackContainer(image="localstack/localstack:latest") as localstack:
        s3_endpoint = localstack.get_url()
        os.environ["AWS_ENDPOINT_OVERRIDE"] = s3_endpoint

        print(f"using LocalStack in Docker container {s3_endpoint}")

        # Create S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            endpoint_url=s3_endpoint,
        )

        bucket_name = "bucket"
        create_bucket(s3_client, bucket_name)

        # Add S3FileAdmin view
        admin.add_view(S3FileAdmin(bucket_name=bucket_name, s3_client=s3_client))

        app.run(debug=True)
