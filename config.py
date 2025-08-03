import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SQLALCHEMY_TRACK_MODIFICATIONS = False

MAIL_SERVER = 'smtp.mailgun.org'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'postmaster@mg.skymanavionicsparts.com'
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = 'noreply@mg.skymanavionicsparts.com'