import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from config import MyConfig
from models import db_init
from fake import generate_fake_data
from flask import Flask
from admin.basic_admin import admin as basic_admin
from admin.super_admin import admin as super_admin


app = Flask(__name__)

app.config.from_object(MyConfig)
db_init(app)
generate_fake_data(app)

# Init admin instances

basic_admin.init_app(app)
super_admin.init_app(app)

from bp import bp

app.register_blueprint(bp)


if __name__ == '__main__':
    app.run()


