import os
import os.path as op
import platform
import re
import shutil

from datetime import datetime
from operator import itemgetter
from werkzeug import secure_filename

from flask import flash, redirect, abort, request, send_file

from wtforms import fields, validators

from flask_admin import form, helpers
from flask_admin._compat import urljoin, as_unicode
from flask_admin.base import BaseView, expose
from flask_admin.actions import action, ActionsMixin
from flask_admin.babel import gettext, lazy_gettext


class FileAdmin(BaseView, ActionsMixin):
    """
        Simple file-management interface.

        :param path:
            Path to the directory which will be managed
        :param base_url:
            Optional base URL for the directory. Will be used to generate
            static links to the files. If not defined, a route will be created
            to serve uploaded files.

        Sample usage::

            import os.path as op

            from flask_admin import Admin
            from flask_admin.contrib.fileadmin import FileAdmin

            admin = Admin()

            path = op.join(op.dirname(__file__), 'static')
            admin.add_view(FileAdmin(path, '/static/', name='Static Files'))
    """

    can_upload = True
    """
        Is file upload allowed.
    """

    can_download = True
    """
        Is file download allowed.
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

    upload_modal_template = 'admin/file/modals/form.html'
    """
        File upload template for modal dialog
    """

    mkdir_template = 'admin/file/form.html'
    """
        Directory creation (mkdir) template
    """

    mkdir_modal_template = 'admin/file/modals/form.html'
    """
        Directory creation (mkdir) template for modal dialog
    """

    rename_template = 'admin/file/form.html'
    """
        Rename template
    """

    rename_modal_template = 'admin/file/modals/form.html'
    """
        Rename template for modal dialog
    """

    edit_template = 'admin/file/form.html'
    """
        Edit template
    """

    edit_modal_template = 'admin/file/modals/form.html'
    """
        Edit template for modal dialog
    """

    form_base_class = form.BaseForm
    """
        Base form class. Will be used to create the upload, rename, edit, and delete form.

        Allows enabling CSRF validation and useful if you want to have custom
        contructor or override some fields.

        Example::

            class MyBaseForm(Form):
                def do_something(self):
                    pass

            class MyAdmin(FileAdmin):
                form_base_class = MyBaseForm

    """

    # Modals
    rename_modal = False
    """Setting this to true will display the rename view as a modal dialog."""

    upload_modal = False
    """Setting this to true will display the upload view as a modal dialog."""

    mkdir_modal = False
    """Setting this to true will display the mkdir view as a modal dialog."""

    edit_modal = False
    """Setting this to true will display the edit view as a modal dialog."""

    def __init__(self, base_path, base_url=None,
                 name=None, category=None, endpoint=None, url=None,
                 verify_path=True, menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
        """
            Constructor.

            :param base_path:
                Base file storage location
            :param base_url:
                Base URL for the files
            :param name:
                Name of this view. If not provided, will default to the class name.
            :param category:
                View category
            :param endpoint:
                Endpoint name for the view
            :param url:
                URL for view
            :param verify_path:
                Verify if path exists. If set to `True` and path does not exist
                will raise an exception.
        """
        self.base_path = as_unicode(base_path)
        self.base_url = base_url

        self.init_actions()

        self._on_windows = platform.system() == 'Windows'

        # Convert allowed_extensions to set for quick validation
        if (self.allowed_extensions and
            not isinstance(self.allowed_extensions, set)):
            self.allowed_extensions = set(self.allowed_extensions)

        # Convert editable_extensions to set for quick validation
        if (self.editable_extensions and
            not isinstance(self.editable_extensions, set)):
            self.editable_extensions = set(self.editable_extensions)

        # Check if path exists
        if not op.exists(base_path):
            raise IOError('FileAdmin path "%s" does not exist or is not accessible' % base_path)

        super(FileAdmin, self).__init__(name, category, endpoint, url,
                                        menu_class_name=menu_class_name, menu_icon_type=menu_icon_type,
                                        menu_icon_value=menu_icon_value)

    def is_accessible_path(self, path):
        """
            Verify if the provided path is accessible for the current user.

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

    def get_upload_form(self):
        """
            Upload form class for file upload view.

            Override to implement customized behavior.
        """
        class UploadForm(self.form_base_class):
            """
                File upload form. Works with FileAdmin instance to check if it
                is allowed to upload file with given extension.
            """
            upload = fields.FileField(lazy_gettext('File to upload'))

            def __init__(self, *args, **kwargs):
                super(UploadForm, self).__init__(*args, **kwargs)
                self.admin = kwargs['admin']

            def validate_upload(self, field):
                if not self.upload.data:
                    raise validators.ValidationError(gettext('File required.'))

                filename = self.upload.data.filename

                if not self.admin.is_file_allowed(filename):
                    raise validators.ValidationError(gettext('Invalid file type.'))

        return UploadForm

    def get_edit_form(self):
        """
            Create form class for file editing view.

            Override to implement customized behavior.
        """
        class EditForm(self.form_base_class):
            content = fields.TextAreaField(lazy_gettext('Content'),
                                           (validators.required(),))

        return EditForm

    def get_name_form(self):
        """
            Create form class for renaming and mkdir views.

            Override to implement customized behavior.
        """
        def validate_name(self, field):
            regexp = re.compile(r'^(?!^(PRN|AUX|CLOCK\$|NUL|CON|COM\d|LPT\d|\..*)(\..+)?$)[^\x00-\x1f\\?*:\";|/]+$')
            if not regexp.match(field.data):
                raise validators.ValidationError(gettext('Invalid name'))

        class NameForm(self.form_base_class):
            """
                Form with a filename input field.

                Validates if provided name is valid for *nix and Windows systems.
            """
            name = fields.StringField(lazy_gettext('Name'),
                                      validators=[validators.Required(),
                                                  validate_name])
            path = fields.HiddenField()

        return NameForm

    def get_delete_form(self):
        """
            Create form class for model delete view.

            Override to implement customized behavior.
        """
        class DeleteForm(self.form_base_class):
            path = fields.HiddenField(validators=[validators.Required()])

        return DeleteForm

    def upload_form(self):
        """
            Instantiate file upload form and return it.

            Override to implement custom behavior.
        """
        upload_form_class = self.get_upload_form()
        if request.form:
            # Workaround for allowing both CSRF token + FileField to be submitted
            # https://bitbucket.org/danjac/flask-wtf/issue/12/fieldlist-filefield-does-not-follow
            formdata = request.form.copy() # as request.form is immutable
            formdata.update(request.files)

            # admin=self allows the form to use self.is_file_allowed
            return upload_form_class(formdata, admin=self)
        elif request.files:
            return upload_form_class(request.files, admin=self)
        else:
            return upload_form_class(admin=self)

    def name_form(self):
        """
            Instantiate form used in rename and mkdir then return it.

            Override to implement custom behavior.
        """
        name_form_class = self.get_name_form()
        if request.form:
            return name_form_class(request.form)
        elif request.args:
            return name_form_class(request.args)
        else:
            return name_form_class()

    def edit_form(self):
        """
            Instantiate file editing form and return it.

            Override to implement custom behavior.
        """
        edit_form_class = self.get_edit_form()
        if request.form:
            return edit_form_class(request.form)
        else:
            return edit_form_class()

    def delete_form(self):
        """
            Instantiate file delete form and return it.

            Override to implement custom behavior.
        """
        delete_form_class = self.get_delete_form()
        if request.form:
            return delete_form_class(request.form)
        else:
            return delete_form_class()

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
            Determine if the file can be edited.

            Override to customize behavior.

            :param filename:
                Source file name
        """
        ext = op.splitext(filename)[1].lower()

        if ext.startswith('.'):
            ext = ext[1:]

        if not self.editable_extensions or ext not in self.editable_extensions:
            return False

        return True

    def is_in_folder(self, base_path, directory):
        """
            Verify that `directory` is in `base_path` folder

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

    def validate_form(self, form):
        """
            Validate the form on submit.

            :param form:
                Form to validate
        """
        return helpers.validate_form_on_submit(form)

    def _get_dir_url(self, endpoint, path=None, **kwargs):
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
            return self.get_url(endpoint, **kwargs)
        else:
            if self._on_windows:
                path = path.replace('\\', '/')

            kwargs['path'] = path

            return self.get_url(endpoint, **kwargs)

    def _get_file_url(self, path, **kwargs):
        """
            Return static file url

            :param path:
                Static file path
        """
        if self.is_file_editable(path):
            route = '.edit'
        else:
            route = '.download'

        return self.get_url(route, path=path, **kwargs)

    def _normalize_path(self, path):
        """
            Verify and normalize path.

            If the path is not relative to the base directory, will raise a 404 exception.

            If the path does not exist, this will also raise a 404 exception.
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
        elif name == 'edit' and len(self.editable_extensions) == 0:
            return False

        return True

    def on_rename(self, full_path, dir_base, filename):
        """
            Perform some actions after a file or directory has been renamed.

            Called from rename method

            By default do nothing.
        """
        pass

    def on_edit_file(self, full_path, path):
        """
            Perform some actions after a file has been successfully changed.

            Called from edit method

            By default do nothing.
        """
        pass

    def on_file_upload(self, directory, path, filename):
        """
            Perform some actions after a file has been successfully uploaded.

            Called from upload method

            By default do nothing.
        """
        pass

    def on_mkdir(self, parent_dir, dir_name):
        """
            Perform some actions after a directory has successfully been created.

            Called from mkdir method

            By default do nothing.
        """
        pass

    def before_directory_delete(self, full_path, dir_name):
        """
            Perform some actions before a directory has successfully been deleted.

            Called from delete method

            By default do nothing.
        """
        pass

    def before_file_delete(self, full_path, filename):
        """
            Perform some actions before a file has successfully been deleted.

            Called from delete method

            By default do nothing.
        """
        pass

    def on_directory_delete(self, full_path, dir_name):
        """
            Perform some actions after a directory has successfully been deleted.

            Called from delete method

            By default do nothing.
        """
        pass

    def on_file_delete(self, full_path, filename):
        """
            Perform some actions after a file has successfully been deleted.

            Called from delete method

            By default do nothing.
        """
        pass

    def _save_form_files(self, directory, path, form):
        filename = op.join(directory,
                           secure_filename(form.upload.data.filename))

        if op.exists(filename):
            secure_name = op.join(path, secure_filename(form.upload.data.filename))
            raise Exception(gettext('File "%(name)s" already exists.',
                                    name=secure_name))
        else:
            self.save_file(filename, form.upload.data)
            self.on_file_upload(directory, path, filename)

    @expose('/')
    @expose('/b/<path:path>')
    def index(self, path=None):
        """
            Index view method

            :param path:
                Optional directory path. If not provided, will use the base directory
        """
        if self.can_delete:
            delete_form = self.delete_form()
        else:
            delete_form = None

        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index'))

        # Get directory listing
        items = []

        # Parent directory
        if directory != base_path:
            parent_path = op.normpath(op.join(path, '..'))
            if parent_path == '.':
                parent_path = None

            items.append(('..', parent_path, True, 0, 0))

        for f in os.listdir(directory):
            fp = op.join(directory, f)
            rel_path = op.join(path, f)

            if self.is_accessible_path(rel_path):
                items.append((f, rel_path, op.isdir(fp), op.getsize(fp), op.getmtime(fp)))

        # Sort by name
        items.sort(key=itemgetter(0))

        # Sort by type
        items.sort(key=itemgetter(2), reverse=True)

        # Sort by modified date
        items.sort(key=lambda values: (values[0], values[1], values[2], values[3], datetime.fromtimestamp(values[4])), reverse=True)

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
                           actions_confirmation=actions_confirmation,
                           delete_form=delete_form)

    @expose('/upload/', methods=('GET', 'POST'))
    @expose('/upload/<path:path>', methods=('GET', 'POST'))
    def upload(self, path=None):
        """
            Upload view method

            :param path:
                Optional directory path. If not provided, will use the base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        if not self.can_upload:
            flash(gettext('File uploading is disabled.'), 'error')
            return redirect(self._get_dir_url('.index', path))

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index'))

        form = self.upload_form()
        if self.validate_form(form):
            try:
                self._save_form_files(directory, path, form)
                flash(gettext('Successfully saved file: %(name)s',
                              name=form.upload.data.filename))
                return redirect(self._get_dir_url('.index', path))
            except Exception as ex:
                flash(gettext('Failed to save file: %(error)s', error=ex), 'error')

        if self.upload_modal and request.args.get('modal'):
            template = self.upload_modal_template
        else:
            template = self.upload_template

        return self.render(template, form=form,
                           header_text=gettext('Upload File'),
                           modal=request.args.get('modal'))

    @expose('/download/<path:path>')
    def download(self, path=None):
        """
            Download view method.

            :param path:
                File path.
        """
        if not self.can_download:
            abort(404)

        base_path, directory, path = self._normalize_path(path)

        # backward compatibility with base_url
        base_url = self.get_base_url()
        if base_url:
            base_url = urljoin(self.get_url('.index'), base_url)
            return redirect(urljoin(base_url, path))

        return send_file(directory)

    @expose('/mkdir/', methods=('GET', 'POST'))
    @expose('/mkdir/<path:path>', methods=('GET', 'POST'))
    def mkdir(self, path=None):
        """
            Directory creation view method

            :param path:
                Optional directory path. If not provided, will use the base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        dir_url = self._get_dir_url('.index', path)

        if not self.can_mkdir:
            flash(gettext('Directory creation is disabled.'), 'error')
            return redirect(dir_url)

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index'))

        form = self.name_form()

        if self.validate_form(form):
            try:
                os.mkdir(op.join(directory, form.name.data))
                self.on_mkdir(directory, form.name.data)
                flash(gettext('Successfully created directory: %(directory)s',
                              directory=form.name.data))
                return redirect(dir_url)
            except Exception as ex:
                flash(gettext('Failed to create directory: %(error)s', error=ex), 'error')
        else:
            helpers.flash_errors(form, message='Failed to create directory: %(error)s')

        if self.mkdir_modal and request.args.get('modal'):
            template = self.mkdir_modal_template
        else:
            template = self.mkdir_template

        return self.render(template, form=form, dir_url=dir_url,
                           header_text=gettext('Create Directory'))

    @expose('/delete/', methods=('POST',))
    def delete(self):
        """
            Delete view method
        """
        form = self.delete_form()

        path = form.path.data
        if path:
            return_url = self._get_dir_url('.index', op.dirname(path))
        else:
            return_url = self.get_url('.index')

        if self.validate_form(form):
            # Get path and verify if it is valid
            base_path, full_path, path = self._normalize_path(path)

            if not self.can_delete:
                flash(gettext('Deletion is disabled.'), 'error')
                return redirect(return_url)

            if not self.is_accessible_path(path):
                flash(gettext('Permission denied.'), 'error')
                return redirect(self._get_dir_url('.index'))

            if op.isdir(full_path):
                if not self.can_delete_dirs:
                    flash(gettext('Directory deletion is disabled.'), 'error')
                    return redirect(return_url)

                try:
                    self.before_directory_delete(full_path, path)
                    shutil.rmtree(full_path)
                    self.on_directory_delete(full_path, path)
                    flash(gettext('Directory "%(path)s" was successfully deleted.', path=path))
                except Exception as ex:
                    flash(gettext('Failed to delete directory: %(error)s', error=ex), 'error')
            else:
                try:
                    self.before_file_delete(full_path, path)
                    os.remove(full_path)
                    self.on_file_delete(full_path, path)
                    flash(gettext('File "%(name)s" was successfully deleted.', name=path))
                except Exception as ex:
                    flash(gettext('Failed to delete file: %(name)s', name=ex), 'error')
        else:
            helpers.flash_errors(form, message='Failed to delete file. %(error)s')

        return redirect(return_url)

    @expose('/rename/', methods=('GET', 'POST'))
    def rename(self):
        """
            Rename view method
        """
        form = self.name_form()

        path = form.path.data
        if path:
            base_path, full_path, path = self._normalize_path(path)

            return_url = self._get_dir_url('.index', op.dirname(path))
        else:
            return redirect(self.get_url('.index'))

        if not self.can_rename:
            flash(gettext('Renaming is disabled.'), 'error')
            return redirect(return_url)

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index'))

        if not op.exists(full_path):
            flash(gettext('Path does not exist.'), 'error')
            return redirect(return_url)

        if self.validate_form(form):
            try:
                dir_base = op.dirname(full_path)
                filename = secure_filename(form.name.data)

                os.rename(full_path, op.join(dir_base, filename))
                self.on_rename(full_path, dir_base, filename)
                flash(gettext('Successfully renamed "%(src)s" to "%(dst)s"',
                              src=op.basename(path),
                              dst=filename))
            except Exception as ex:
                flash(gettext('Failed to rename: %(error)s', error=ex), 'error')

            return redirect(return_url)
        else:
            helpers.flash_errors(form, message='Failed to rename: %(error)s')

        if self.rename_modal and request.args.get('modal'):
            template = self.rename_modal_template
        else:
            template = self.rename_template

        return self.render(template, form=form, path=op.dirname(path),
                           name=op.basename(path), dir_url=return_url,
                           header_text=gettext('Rename %(name)s',
                                               name=op.basename(path)))

    @expose('/edit/', methods=('GET', 'POST'))
    def edit(self):
        """
            Edit view method
        """
        next_url = None

        path = request.args.getlist('path')
        if not path:
            return redirect(self.get_url('.index'))

        if len(path) > 1:
            next_url = self.get_url('.edit', path=path[1:])

        path = path[0]

        base_path, full_path, path = self._normalize_path(path)

        if not self.is_accessible_path(path) or not self.is_file_editable(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index'))

        dir_url = self._get_dir_url('.index', os.path.dirname(path))
        next_url = next_url or dir_url

        form = self.edit_form()
        error = False

        if self.validate_form(form):
            form.process(request.form, content='')
            if form.validate():
                try:
                    with open(full_path, 'w') as f:
                        f.write(request.form['content'])
                except IOError:
                    flash(gettext("Error saving changes to %(name)s.", name=path), 'error')
                    error = True
                else:
                    self.on_edit_file(full_path, path)
                    flash(gettext("Changes to %(name)s saved successfully.", name=path))
                    return redirect(next_url)
        else:
            helpers.flash_errors(form, message='Failed to edit file. %(error)s')

            try:
                with open(full_path, 'rb') as f:
                    content = f.read()
            except IOError:
                flash(gettext("Error reading %(name)s.", name=path), 'error')
                error = True
            except:
                flash(gettext("Unexpected error while reading from %(name)s", name=path), 'error')
                error = True
            else:
                try:
                    content = content.decode('utf8')
                except UnicodeDecodeError:
                    flash(gettext("Cannot edit %(name)s.", name=path), 'error')
                    error = True
                except:
                    flash(gettext("Unexpected error while reading from %(name)s", name=path), 'error')
                    error = True
                else:
                    form.content.data = content

            if error:
                return redirect(next_url)

        if self.edit_modal and request.args.get('modal'):
            template = self.edit_modal_template
        else:
            template = self.edit_template

        return self.render(template, dir_url=dir_url, path=path,
                           form=form, error=error,
                           header_text=gettext('Editing %(path)s', path=path))

    @expose('/action/', methods=('POST',))
    def action_view(self):
        return self.handle_action()

    # Actions
    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete these files?'))
    def action_delete(self, items):
        if not self.can_delete:
            flash(gettext('File deletion is disabled.'), 'error')
            return

        for path in items:
            base_path, full_path, path = self._normalize_path(path)

            if self.is_accessible_path(path):
                try:
                    os.remove(full_path)
                    flash(gettext('File "%(name)s" was successfully deleted.', name=path))
                except Exception as ex:
                    flash(gettext('Failed to delete file: %(name)s', name=ex), 'error')

    @action('edit', lazy_gettext('Edit'))
    def action_edit(self, items):
        return redirect(self.get_url('.edit', path=items))
