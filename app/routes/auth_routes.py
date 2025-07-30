from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from app.models import User
from sqlalchemy import func
from app.models import db
from app.utils.token import generate_reset_token, verify_reset_token
from flask import current_app


bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.parts') if current_user.is_admin else url_for('consigner.entry'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter(func.lower(User.email) == email.strip().lower()).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin.parts') if user.is_admin else url_for('consigner.entry'))
        else:
            flash('Invalid email or password.')

    return render_template('login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter(func.lower(User.email) == email).first()

        if user:
            token = generate_reset_token(email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            # TODO: Send this via email in production
            print(f"🔗 Reset URL: {reset_url}")
            flash('A password reset link has been sent to your email.')
        else:
            flash('Email not found.')

    return render_template('forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset link.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password has been updated. You may now log in.')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)