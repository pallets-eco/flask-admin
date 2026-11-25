from bp import bp
from config import MyConfig
from fake import generate_fake_data
from flask import Flask
from models import db_init
from my_admin.basic_admin import admin as basic_admin
from my_admin.pro_admin import admin as pro_admin
from my_admin.super_admin import admin as super_admin

app = Flask(__name__)

app.config.from_object(MyConfig)
db_init(app)
generate_fake_data(app)

# Init admin instances

basic_admin.init_app(app)
super_admin.init_app(app)
pro_admin.init_app(app)


app.register_blueprint(bp)


if __name__ == "__main__":
    app.run(debug=True)
