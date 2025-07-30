from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset')

def verify_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt='password-reset', max_age=expiration)
    except Exception:
        return None
