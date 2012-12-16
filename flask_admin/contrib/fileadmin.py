import os
import os.path as op
import platform
import urlparse
import re
import shutil

from operator import itemgetter

from werkzeug import secure_filename

from flask import flash, url_for, redirect, abort, request

from flask.ext.admin.base import BaseView, expose
from flask.ext.admin.actions import action, ActionsMixin
from flask.ext.admin.babel import gettext, lazy_gettext
from flask.ext.admin import form
from flask.ext import wtf


class NameForm(form.BaseForm):
    """
        Form with a filename input field.

        Validates if provided name is valid for *nix and Windows systems.
    """
    name = wtf.TextField()

    regexp = re.compile(r'^(?!^(PRN|AUX|CLOCK\$|NUL|CON|COM\d|LPT\d|\..*)(\..+)?$)[^\x00-\x1f\\?*:\";|/]+$')

    def validate_name(self, field):
        if not self.regexp.match(field.data):
            raise wtf.ValidationError(gettext('Invalid directory name'))


class UploadForm(form.BaseForm):
    """
        File upload form. Works with FileAdmin instance to check if it is allowed
        to upload file with given extension.
    """
    upload = wtf.FileField(lazy_gettext('File to upload'))

    def __init__(self, admin):
        self.admin = admin

        super(UploadForm, self).__init__()

    def validate_upload(self, field):
        if not self.upload.has_file():
            raise wtf.ValidationError(gettext('File required.'))

        filename = self.upload.data.filename

        if not self.admin.is_file_allowed(filename):
            raise wtf.ValidationError(gettext('Invalid file type.'))


class EditForm(form.BaseForm):
    content = wtf.TextAreaField(lazy_gettext('Content'),
                                [wtf.validators.required()])


class FileAdmin(BaseView, ActionsMixin):
    """
        Simple file-management interface.

        Requires two parameters:

        :param path:
            Path to the directory which will be managed
        :param url:
            Base URL for the directory. Will be used to generate
            static links to the files.

        Sample usage::

            admin = Admin()

            path = op.join(op.dirname(__file__), 'static')
            admin.add_view(FileAdmin(path, '/static/', name='Static Files'))
            admin.setup_app(app)
    """

    can_upload = True
    """
        Is file upload allowed.
    """

    can_delete = True
    """
        Is file deletion allowed.
    """

    can_delete_dirs = True
    """
        Is recursive directory deletion is allowed.
    """

    can_mkdir = True
    """
        Is directory creation allowed.
    """

    can_rename = True
    """
        Is file and directory renaming allowed.
    """

    allowed_extensions = None
    """
        List of allowed extensions for uploads, in lower case.

        Example::

            class MyAdmin(FileAdmin):
                allowed_extensions = ('swf', 'jpg', 'gif', 'png')
    """

    editable_extensions = tuple()
    """
        List of editable extensions, in lower case.

        Example::

            class MyAdmin(FileAdmin):
                editable_extensions = ('md', 'html', 'txt')
    """

    list_template = 'admin/file/list.html'
    """
        File list template
    """

    upload_template = 'admin/file/form.html'
    """
        File upload template
    """

    mkdir_template = 'admin/file/form.html'
    """
        Directory creation (mkdir) template
    """

    rename_template = 'admin/file/rename.html'
    """
        Rename template
    """

    edit_template = 'admin/file/edit.html'
    """
        Edit template
    """

    def __init__(self, base_path, base_url,
                 name=None, category=None, endpoint=None, url=None,
                 verify_path=True):
        """
            Constructor.

            :param base_path:
                Base file storage location
            :param base_url:
                Base URL for the files
            :param name:
                Name of this view. If not provided, will be defaulted to the class name.
            :param category:
                View category
            :param endpoint:
                Endpoint name for the view
            :param url:
                URL for view
            :param verify_path:
                Verify if path exists. If set to `True` and path does not exist
                will throw exception.
        """
        self.base_path = base_path
        self.base_url = base_url

        self.init_actions()

        self._on_windows = platform.system() == 'Windows'

        # Convert allowed_extensions to set for quick validation
        if (self.allowed_extensions
            and not isinstance(self.allowed_extensions, set)):
            self.allowed_extensions = set(self.allowed_extensions)

        # Convert editable_extensions to set for quick validation
        if (self.editable_extensions
            and not isinstance(self.editable_extensions, set)):
            self.editable_extensions = set(self.editable_extensions)

        # Check if path exists
        if not op.exists(base_path):
            raise IOError('FileAdmin path "%s" does not exist or is not accessible' % base_path)

        super(FileAdmin, self).__init__(name, category, endpoint, url)

    def is_accessible_path(self, path):
        """
            Verify if path is accessible for current user.

            Override to customize behavior.

            :param path:
                Relative path to the root
        """
        return True

    def get_base_path(self):
        """
            Return base path. Override to customize behavior (per-user
            directories, etc)
        """
        return op.normpath(self.base_path)

    def get_base_url(self):
        """
            Return base URL. Override to customize behavior (per-user
            directories, etc)
        """
        return self.base_url

    def is_file_allowed(self, filename):
        """
            Verify if file can be uploaded.

            Override to customize behavior.

            :param filename:
                Source file name
        """
        ext = op.splitext(filename)[1].lower()

        if ext.startswith('.'):
            ext = ext[1:]

        if self.allowed_extensions and ext not in self.allowed_extensions:
            return False

        return True

    def is_file_editable(self, filename):
        """
            Verify if file can be edited.

            Override to customize behavior.

            :param filename:
                Source file name
        """
        ext = op.splitext(filename)[1].lower()

        if ext.startswith('.'):
            ext = ext[1:]

        if self.editable_extensions and ext not in self.editable_extensions:
            return False

        return True

    def is_in_folder(self, base_path, directory):
        """
            Verify if `directory` is in `base_path` folder

            :param base_path:
                Base directory path
            :param directory:
                Directory path to check
        """
        return op.normpath(directory).startswith(base_path)

    def save_file(self, path, file_data):
        """
            Save uploaded file to the disk

            :param path:
                Path to save to
            :param file_data:
                Werkzeug `FileStorage` object
        """
        file_data.save(path)

    def _get_dir_url(self, endpoint, path, **kwargs):
        """
            Return prettified URL

            :param endpoint:
                Endpoint name
            :param path:
                Directory path
            :param kwargs:
                Additional arguments
        """
        if not path:
            return url_for(endpoint)
        else:
            if self._on_windows:
                path = path.replace('\\', '/')

            kwargs['path'] = path

            return url_for(endpoint, **kwargs)

    def _get_file_url(self, path):
        """
            Return static file url

            :param path:
                Static file path
        """
        if self.is_file_editable(path):
            return url_for(".edit", path=path)
        else:
            base_url = self.get_base_url()
            return urlparse.urljoin(base_url, path)

    def _normalize_path(self, path):
        """
            Verify and normalize path.

            If path is not relative to the base directory, will throw 404 exception.

            If path does not exist, will also throw 404 exception.
        """
        base_path = self.get_base_path()

        if path is None:
            directory = base_path
            path = ''
        else:
            path = op.normpath(path)
            directory = op.normpath(op.join(base_path, path))

            if not self.is_in_folder(base_path, directory):
                abort(404)

        if not op.exists(directory):
            abort(404)

        return base_path, directory, path

    def is_action_allowed(self, name):
        if name == 'delete' and not self.can_delete:
            return False

        return True

    @expose('/')
    @expose('/b/<path:path>')
    def index(self, path=None):
        """
            Index view method

            :param path:
                Optional directory path. If not provided, will use base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        # Get directory listing
        items = []

        # Parent directory
        if directory != base_path:
            parent_path = op.normpath(op.join(path, '..'))
            if parent_path == '.':
                parent_path = None

            items.append(('..', parent_path, True, 0))

        for f in os.listdir(directory):
            fp = op.join(directory, f)

            items.append((f, op.join(path, f), op.isdir(fp), op.getsize(fp)))

        # Sort by type
        items.sort(key=itemgetter(2), reverse=True)

        # Generate breadcrumbs
        accumulator = []
        breadcrumbs = []
        for n in path.split(os.sep):
            accumulator.append(n)
            breadcrumbs.append((n, op.join(*accumulator)))

        # Actions
        actions, actions_confirmation = self.get_actions_list()

        return self.render(self.list_template,
                           dir_path=path,
                           breadcrumbs=breadcrumbs,
                           get_dir_url=self._get_dir_url,
                           get_file_url=self._get_file_url,
                           items=items,
                           actions=actions,
                           actions_confirmation=actions_confirmation)

    @expose('/upload/', methods=('GET', 'POST'))
    @expose('/upload/<path:path>', methods=('GET', 'POST'))
    def upload(self, path=None):
        """
            Upload view method

            :param path:
                Optional directory path. If not provided, will use base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        if not self.can_upload:
            flash(gettext('File uploading is disabled.'), 'error')
            return redirect(self._get_dir_url('.index', path))

        form = UploadForm(self)
        if form.validate_on_submit():
            filename = op.join(directory,
                               secure_filename(form.upload.data.filename))

            if op.exists(filename):
                flash(gettext('File "%(name)s" already exists.', name=form.upload.data.filename),
                      'error')
            else:
                try:
                    self.save_file(filename, form.upload.data)
                    return redirect(self._get_dir_url('.index', path))
                except Exception, ex:
                    flash(gettext('Failed to save file: %(error)s', error=ex))

        return self.render(self.upload_template, form=form)

    @expose('/mkdir/', methods=('GET', 'POST'))
    @expose('/mkdir/<path:path>', methods=('GET', 'POST'))
    def mkdir(self, path=None):
        """
            Directory creation view method

            :param path:
                Optional directory path. If not provided, will use base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        dir_url = self._get_dir_url('.index', path)

        if not self.can_mkdir:
            flash(gettext('Directory creation is disabled.'), 'error')
            return redirect(dir_url)

        form = NameForm(request.form)

        if form.validate_on_submit():
            try:
                os.mkdir(op.join(directory, form.name.data))
                return redirect(dir_url)
            except Exception, ex:
                flash(gettext('Failed to create directory: %(error)s', ex), 'error')

        return self.render(self.mkdir_template,
                           form=form,
                           dir_url=dir_url)

    @expose('/delete/', methods=('POST',))
    def delete(self):
        """
            Delete view method
        """
        path = request.form.get('path')

        if not path:
            return redirect(url_for('.index'))

        # Get path and verify if it is valid
        base_path, full_path, path = self._normalize_path(path)

        return_url = self._get_dir_url('.index', op.dirname(path))

        if not self.can_delete:
            flash(gettext('Deletion is disabled.'))
            return redirect(return_url)

        if op.isdir(full_path):
            if not self.can_delete_dirs:
                flash(gettext('Directory deletion is disabled.'))
                return redirect(return_url)

            try:
                shutil.rmtree(full_path)
                flash(gettext('Directory "%s" was successfully deleted.' % path))
            except Exception, ex:
                flash(gettext('Failed to delete directory: %(error)s', error=ex), 'error')
        else:
            try:
                os.remove(full_path)
                flash(gettext('File "%(name)s" was successfully deleted.', name=path))
            except Exception, ex:
                flash(gettext('Failed to delete file: %(name)s', name=ex), 'error')

        return redirect(return_url)

    @expose('/rename/', methods=('GET', 'POST'))
    def rename(self):
        """
            Rename view method
        """
        path = request.args.get('path')

        if not path:
            return redirect(url_for('.index'))

        base_path, full_path, path = self._normalize_path(path)

        return_url = self._get_dir_url('.index', op.dirname(path))

        if not self.can_rename:
            flash(gettext('Renaming is disabled.'))
            return redirect(return_url)

        if not op.exists(full_path):
            flash(gettext('Path does not exist.'))
            return redirect(return_url)

        form = NameForm(request.form, name=op.basename(path))
        if form.validate_on_submit():
            try:
                dir_base = op.dirname(full_path)
                filename = secure_filename(form.name.data)

                os.rename(full_path, op.join(dir_base, filename))
                flash(gettext('Successfully renamed "%(src)s" to "%(dst)s"',
                      src=op.basename(path),
                      dst=filename))
            except Exception, ex:
                flash(gettext('Failed to rename: %(error)s', error=ex), 'error')

            return redirect(return_url)

        return self.render(self.rename_template,
                           form=form,
                           path=op.dirname(path),
                           name=op.basename(path),
                           dir_url=return_url)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit(self):
        """
            Edit view method
        """
        path = request.args.getlist('path')
        next_url = None
        if not path:
            return redirect(url_for('.index'))

        if len(path) > 1:
            next_url = url_for('.edit', path=path[1:])
        path = path[0]

        base_path, full_path, path = self._normalize_path(path)
        dir_url = self._get_dir_url('.index', os.path.dirname(path))
        next_url = next_url or dir_url

        form = EditForm()
        error = False

        if request.method == 'POST':
            form.process(request.form, content='')
            if form.validate():
                try:
                    with open(full_path, 'w') as f:
                        f.write(request.form['content'])
                except IOError:
                    flash(gettext("Error saving changes to %(name)s.", name=path), 'error')
                    error = True
                else:
                    flash(gettext("Changes to %(name)s saved successfully.", name=path))
                    return redirect(next_url)
        else:
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
            except IOError:
                flash(gettext("Error reading %(name)s.", name=path), 'error')
                error = True
            except:
                flash(gettext("Unexpected error while reading from %(name)s", name=path), 'error')
                error = True
            else:
                try:
                    content.decode('utf8')
                except UnicodeDecodeError:
                    flash(gettext("Cannot edit %(name)s.", name=path), 'error')
                    error = True
                except:
                    flash(gettext("Unexpected error while reading from %(name)s", name=path), 'error')
                    error = True
                else:
                    form.content.data = content

        return self.render(self.edit_template, dir_url=dir_url, path=path,
                        form=form, error=error)

    @expose('/action/', methods=('POST',))
    def action_view(self):
        return self.handle_action()

    # Actions
    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete these files?'))
    def action_delete(self, items):
        for path in items:
            base_path, full_path, path = self._normalize_path(path)

            try:
                os.remove(full_path)
                flash(gettext('File "%(name)s" was successfully deleted.', name=path))
            except Exception, ex:
                flash(gettext('Failed to delete file: %(name)s', name=ex), 'error')

    @action('edit', lazy_gettext('Edit'))
    def action_edit(self, items):
        return redirect(url_for('.edit', path=items))
