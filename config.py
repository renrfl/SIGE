import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")

# SQLite cannot create its parent directory. Ensure it exists before the
# application initializes the database connection.
os.makedirs(DATABASE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sige-desenvolvimento")

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" + os.path.join(DATABASE_DIR, "sige.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
