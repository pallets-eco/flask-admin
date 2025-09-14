import os
from io import BytesIO

import boto3
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin
from flask_babel import Babel
from testcontainers.localstack import LocalStackContainer

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app, name="Example: S3 File Admin")
babel = Babel(app)


if __name__ == "__main__":
    with LocalStackContainer(image="localstack/localstack:latest") as localstack:
        s3_endpoint = localstack.get_url()
        os.environ["AWS_ENDPOINT_OVERRIDE"] = s3_endpoint

        # Create S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            endpoint_url=s3_endpoint,
        )

        # Create S3 bucket
        bucket_name = "bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        s3_client.upload_fileobj(BytesIO(b""), "bucket", "some-directory/")

        s3_client.upload_fileobj(
            BytesIO(b"abcdef"),
            "bucket",
            "some-file",
            ExtraArgs={"ContentType": "text/plain"},
        )

        s3_client.upload_fileobj(
            BytesIO(b"abcdef"),
            "bucket",
            "some-directory/some-file",
            ExtraArgs={"ContentType": "text/plain"},
        )

        # Add S3FileAdmin view
        admin.add_view(
            S3FileAdmin(
                bucket_name=bucket_name,
                s3_client=s3_client,
                # explicitly set the OS based on the platform of s3-cloud
                on_windows=False,
            )
        )

        app.run(debug=True)
