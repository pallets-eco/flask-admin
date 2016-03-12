# coding:utf-8
'''
Created on 2016年3月12日

@author: likaiguo
'''
from __future__ import unicode_literals

import os

from django.core.wsgi import get_wsgi_application
from flask import Flask

import flask_admin as admin
from flask_admin.contrib.django.view import ModelView


try:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    from django.contrib.auth.models import User
    print 'import django User model ok'
except Exception, e:
    print 'error !', e
from polls.models import Question, Choice

application = get_wsgi_application()
print User.objects.count()

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'


class UserView(ModelView):

    page_size = 10

# Flask views


@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, name='Example: Django Model')
    admin.add_view(UserView(User))
    admin.add_view(ModelView(Choice))
    admin.add_view(ModelView(Question))

    # Start app
    app.run(debug=True)
