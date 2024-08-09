import os
import sys
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../')
))


class MyConfig:
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(16))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sqlite3-multi-theming.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SWATCH_THEMES = [
        'default',   'cerulean',  'cosmo',   'cyborg',     'darkly',
        'flatly',    'journal',   'litera',  'lumen',      'lux',
        'materia',   'minty',     'pulse',   'sandstone',  'simplex',
        'sketchy',   'slate',     'solar',   'spacelab',   'superhero',
        'united',    'yeti'
    ]

    BASIC_ADMIN_BOOTSWATCH_THEME = 'Cosmo'
    SUPER_ADMIN_BOOTSWATCH_THEME = 'United'
