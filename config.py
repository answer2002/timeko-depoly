import os

MAIL_SERVER = 'smtp.strato.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = os.environ.get("EMAIL_ADDRESS")
MAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("EMAIL_ADDRESS")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# EMAIL_ADDRESS = "nachogalanmoreno@gmail.com"
# EMAIL_PASSWORD = "wuer jfan kuzq csv lv"

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///instance/registros.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get("SECRET_KEY", "timeko_key")
