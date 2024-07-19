from flask import Blueprint
from flask import render_template_string


bp = Blueprint('main', __name__, template_folder='admin/templates')


@bp.route('/')
def index():
    return render_template_string('''
        <h1>Hello, World!</h1>
        <ul>
            <li>
                <a href="{{ url_for('basicadmin.index') }}">Basic Admin Panel</a>
            </li>
            <li>
                <a href="{{ url_for('superadmin.index') }}">Super Admin Panel</a>
            </li>
        </ul>
    ''')


