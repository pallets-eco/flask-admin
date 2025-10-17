import functools
import posixpath
import typing as t
from pathlib import PureWindowsPath

from botocore.client import BaseClient
from botocore.exceptions import ClientError
from flask import redirect
from werkzeug import Response

from flask_admin._compat import as_unicode
from flask_admin.babel import gettext

from ..._types import T_RESPONSE
from . import BaseFileAdmin


def _strip_leading_slash_from(
    arg_name: str,
) -> t.Callable[[t.Any], t.Callable[[tuple[t.Any, ...], dict[str, t.Any]], t.Any]]:
    """Strips leading slashes from the specified argument of the decorated function.

    This is used to clean S3 object/key names because the base FileAdmin layers passes
    paths with leading slashes, but S3 doesn't want and doesn't handle this.
    """

    def decorator(
        func: t.Callable,
    ) -> t.Callable[[tuple[t.Any, ...], dict[str, t.Any]], t.Any]:
        @functools.wraps(func)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            args: list = list(args)  # type: ignore[no-redef]
            arg_names = func.__code__.co_varnames[: func.__code__.co_argcount]

            if arg_name in arg_names:
                index = arg_names.index(arg_name)

                # Positional argument found
                if index < len(args):
                    args[index] = args[index].lstrip("/")  # type: ignore[index]

                # Keyword argument found
                elif arg_name in kwargs:
                    kwargs[arg_name] = kwargs[arg_name].lstrip("/")

            return func(*args, **kwargs)

        return wrapper

    return decorator


class S3Storage:
    """
    Storage object representing files on an Amazon S3 bucket.

    Usage::

        from flask_admin.contrib.fileadmin import BaseFileAdmin
        from flask_admin.contrib.fileadmin.s3 import S3Storage

        class MyS3Admin(BaseFileAdmin):
            # Configure your class however you like
            pass

        fileadmin_view = MyS3Admin(storage=S3Storage(...))
    """

    def __init__(
        self, s3_client: BaseClient, bucket_name: str, prefix: t.Union[str, bytes] = ""
    ) -> None:
        """
        Constructor

            :param s3_client:
                An instance of boto3 S3 client.

            :param bucket_name:
                Name of the bucket that the files are on.

        Make sure the credentials have the correct permissions set up on
        Amazon or else S3 will return a 403 FORBIDDEN error.
        """

        self.s3_client = s3_client
        self.bucket_name = bucket_name
        self.separator = "/"
        prefix = PureWindowsPath(as_unicode(prefix)).as_posix()
        prefix = posixpath.normpath(prefix).lstrip("/")
        self.prefix = "" if prefix in [".", "./"] else prefix

    @_strip_leading_slash_from("path")
    def get_files(self, path: str, directory: str) -> list:
        files = []
        directories = []

        if path and not path.endswith(self.separator):
            path += self.separator

        if directory and not directory.endswith(self.separator):
            directory += self.separator

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            # paginator = self.s3_client.get_paginator("list_objects")
            for page in paginator.paginate(
                Bucket=self.bucket_name, Prefix=directory, Delimiter=self.separator
            ):
                for common_prefix in page.get("CommonPrefixes", []):
                    name = posixpath.basename(
                        common_prefix["Prefix"].strip(self.separator)
                    )
                    rel_path = common_prefix["Prefix"].replace(self.prefix, "", 1)

                    directories.append((name, rel_path, True, 0, 0))

                for obj in page.get("Contents", []):
                    if obj["Key"] == directory:
                        continue

                    last_modified = int(obj["LastModified"].timestamp())
                    name = posixpath.basename(obj["Key"])
                    rel_path = obj["Key"].replace(self.prefix, "", 1)

                    files.append((name, rel_path, False, obj["Size"], last_modified))

        except ClientError as e:
            raise ValueError(f"Failed to list files: {e}") from e

        return directories + files

    def _get_bucket_list_prefix(self, path: str) -> str:
        parts = path.split(self.separator)
        if len(parts) == 1:
            search = ""
        else:
            search = self.separator.join(parts[:-1]) + self.separator
        return search

    def _get_path_keys(self, path: str) -> set[str]:
        prefix = self._get_bucket_list_prefix(path)
        try:
            path_keys = set()

            paginator = self.s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(
                Bucket=self.bucket_name, Prefix=prefix, Delimiter=self.separator
            ):
                for common_prefix in page.get("CommonPrefixes", []):
                    path_keys.add(common_prefix["Prefix"])

                for obj in page.get("Contents", []):
                    if obj["Key"] == prefix:
                        continue
                    path_keys.add(obj["Key"])

            return path_keys

        except ClientError as e:
            raise ValueError(f"Failed to get path keys: {e}") from e

    @_strip_leading_slash_from("path")
    def is_dir(self, path: str) -> bool:
        keys = self._get_path_keys(path)
        return path + self.separator in keys

    @_strip_leading_slash_from("path")
    def path_exists(self, path: str) -> bool:
        if path == "":
            return True
        keys = self._get_path_keys(path)
        return path in keys or (path + self.separator) in keys

    def get_base_path(self) -> str:
        return self.prefix

    @_strip_leading_slash_from("path")
    def get_breadcrumbs(self, path: str) -> list[tuple[str, str]]:
        accumulator = []
        breadcrumbs = []
        for n in path.split(self.separator):
            accumulator.append(n)
            breadcrumbs.append((n, self.separator.join(accumulator)))
        return breadcrumbs

    @_strip_leading_slash_from("file_path")
    def send_file(self, file_path: str) -> Response:
        try:
            response = self.s3_client.generate_presigned_url(  # type: ignore[attr-defined]
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_path},
                ExpiresIn=3600,
            )
            return redirect(response)
        except ClientError as e:
            raise ValueError(f"Failed to generate presigned URL: {e}") from e

    @_strip_leading_slash_from("path")
    def save_file(self, path: str, file_data: t.Any) -> None:
        try:
            self.s3_client.upload_fileobj(  # type: ignore[attr-defined]
                file_data.stream,
                self.bucket_name,
                path,
                ExtraArgs={"ContentType": file_data.content_type},
            )
        except ClientError as e:
            raise ValueError(f"Failed to upload file: {e}") from e

    @_strip_leading_slash_from("directory")
    def delete_tree(self, directory: str) -> None:
        self._check_empty_directory(directory)
        self.delete_file(directory + self.separator)  # type: ignore[misc, arg-type]

    @_strip_leading_slash_from("file_path")
    def delete_file(self, file_path: str) -> None:
        try:
            self.s3_client.delete_object(  # type: ignore[attr-defined]
                Bucket=self.bucket_name, Key=file_path
            )
        except ClientError as e:
            raise ValueError(f"Failed to delete file: {e}") from e

    @_strip_leading_slash_from("path")
    @_strip_leading_slash_from("directory")
    def make_dir(self, path: str, directory: str) -> None:
        if path:
            dir_path = self.separator.join([path, (directory + self.separator)])
        else:
            dir_path = directory + self.separator

        try:
            self.s3_client.put_object(  # type: ignore[attr-defined]
                Bucket=self.bucket_name, Key=dir_path, Body=""
            )
        except ClientError as e:
            raise ValueError(f"Failed to create directory: {e}") from e

    def _check_empty_directory(self, path: str) -> bool:
        if not self._is_directory_empty(path):
            raise ValueError(gettext("Cannot operate on non empty directories"))
        return True

    @_strip_leading_slash_from("src")
    @_strip_leading_slash_from("dst")
    def rename_path(self, src: str, dst: str) -> None:
        if self.is_dir(src):  # type: ignore[misc, arg-type]
            self._check_empty_directory(src)
            src += self.separator
            dst += self.separator
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": src}
            self.s3_client.copy_object(  # type: ignore[attr-defined]
                CopySource=copy_source, Bucket=self.bucket_name, Key=dst
            )
            self.delete_file(src)  # type: ignore[misc, arg-type]
        except ClientError as e:
            raise ValueError(f"Failed to rename path: {e}") from e

    def _is_directory_empty(self, path: str) -> bool:
        keys = self._get_path_keys(path + self.separator)
        return len(keys) == 0

    @_strip_leading_slash_from("path")
    def read_file(self, path: str) -> T_RESPONSE:
        try:
            response = self.s3_client.get_object(  # type: ignore[attr-defined]
                Bucket=self.bucket_name, Key=path
            )
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            raise ValueError(f"Failed to read file: {e}") from e

    @_strip_leading_slash_from("path")
    def write_file(self, path: str, content: str) -> None:
        try:
            self.s3_client.put_object(  # type: ignore[attr-defined]
                Bucket=self.bucket_name, Key=path, Body=content
            )
        except ClientError as e:
            raise ValueError(f"Failed to write file: {e}") from e


class S3FileAdmin(BaseFileAdmin):
    """
    Simple Amazon Simple Storage Service file-management interface.

        :param s3_client:
            An instance of boto3 S3 client.

        :param bucket_name:
            Name of the bucket that the files are on.

    Sample usage::

        from flask_admin import Admin
        from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

        import boto3
        s3_client = boto3.client('s3')

        admin = Admin()

        admin.add_view(S3FileAdmin(s3_client, 'files_bucket'))
    """

    def __init__(
        self,
        s3_client: BaseClient,
        bucket_name: str,
        prefix: t.Union[str, bytes] = "",
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        storage = S3Storage(s3_client, bucket_name, prefix=prefix)
        super().__init__(*args, storage=storage, on_windows=False, **kwargs)  # type: ignore[misc, arg-type]
