# Create dummy secret key so we can use sessions
SECRET_KEY = "123456790"

# Create in-memory database
DATABASE_FILE = "db.sqlite"
SQLALCHEMY_DATABASE_URI = "sqlite:///" + DATABASE_FILE
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
