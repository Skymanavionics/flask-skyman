import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SQLALCHEMY_TRACK_MODIFICATIONS = False

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your_email@gmail.com'        # replace with your sender email
MAIL_PASSWORD = 'your_app_password'           # use Gmail App Password
MAIL_DEFAULT_SENDER = 'your_email@gmail.com'  # same as MAIL_USERNAME or custom