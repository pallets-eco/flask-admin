Authorisation & Permissions
=================================
When setting up an admin interface for your application, one of the first problems
you'll want to solve is how to keep unwanted users out. With Flask-Admin there
are a few different ways of approaching this.

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
For a finer-grained solution, Flask-Admin lets you define access control rules
on each of your admin view classes by simply overriding the `is_accessible` method.
How you implement the logic is up to you, but if you were to use a low-level library like
`Flask-Login <https://flask-login.readthedocs.org/>`_, then restricting access to a set of views
could be as simple as::

    class MyModelView(sqla.ModelView):

        def is_accessible(self):
            return login.current_user.is_authenticated()

However, you would still need to implement all of the relevant login /
registration views yourself.

If you like this approach, then have a look at the example at
https://github.com/flask-admin/Flask-Admin/tree/master/examples/auth-flask-login
to get started.

Using Flask-Security
--------------------------------

If you want to get started quicker, you could
use `Flask-Security <https://pythonhosted.org/Flask-Security/>`_,
which is a higher-level library. It comes with lots of builtin views for doing
common things like registration, login, email address confirmation, password resets, etc.

The complicated bit, is making the builtin Flask-Security views work together with the
Flask-Admin templates, to create a consistent experience for your users. To
do this, you will need to override the builtin Flask-Security templates and have them
extend the Flask-Admin base template by adding the following to the top
of each file::

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


