Authorisation & Permissions
=================================

HTTP Basic Auth
------------------------
The simplest form of authentication is HTTP Basic Auth. It doesn't interfere
with your database models, and it doesn't require you to write any new view logic or
template code. So it's great for when you're deploying something that's still
under development, before you want the whole world to see it.

Have a look at `Flask-BasicAuth <http://flask-basicauth.readthedocs.org/>`_ to see how
easy it is to put your whole application behind HTTP Basic Auth.

Unfortunately, there's no easy way of applying HTTP Basic Auth just to your admin
interface.


Rolling your own
--------------------------------
For a more polished access control & permission handling experience, you could
write it yourself if you need to have total control over the functionality. Here,
a low-level library like
`Flask-Login <https://flask-login.readthedocs.org/>`_ could make your life
a bit easier.

If you like this approach, have a look at the example at
https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth-flask-login
to get started.

Using Flask-Security
--------------------------------

If you want a lot of functionality for little effort: you could
use `Flask-Security <https://pythonhosted.org/Flask-Security/>`_,
which is a higher-level library. It comes with lots of builtin views for doing common things like confirming
email addresses, resetting passwords, etc.

The complicated bit, is making the builtin Flask-Security views work together with the
Flask-Admin templates, to create a consistent experience for your users. In order to
do this, you will need to override the builtin Flask Security templates and have them
extend the Flask-Admin base template. To do this, just add the following to the top
of each template::

    {% extends 'admin/master.html' %}

Now, you'll need to manually pass in some context variables for the Flask Admin
templates to render correctly when they're being called from the Flask-Security views.
This could look something like::

    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
        )

For a working example of using Flask-Security with Flask-Admin, have a look at
https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth.

The example only uses the builtin `register` and `login` views, but you could follow the same
approach for including the other views, like `forgot_password`, `send_confirmation`, etc.


