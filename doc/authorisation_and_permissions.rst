Authorisation & Permissions
=================================

HTTP Basic Auth
------------------------
The simplest form of authentication is HTTP Basic Auth. It doesn't interfere
with your database models, and it doesn't require you to write any new view logic or
template code. So it's great for when you're deploying something that's still
under development, when you don't want the whole world to see it just yet.

Have a look at `Flask-BasicAuth <http://flask-basicauth.readthedocs.org/>`_ to see how
easy it is to put your whole application behind HTTP Basic Auth.

Unfortunately, there's no easy way of applying HTTP Basic Auth just to your admin
interface.


Using Flask-Security
--------------------------------


