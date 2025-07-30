from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from app import db
from app.models import User, Part

bp = Blueprint('consigner', __name__, url_prefix='/consigner')

# Render shared HTML for both login and dashboard
@bp.route('/')
def entry():
    if current_user.is_authenticated and not current_user.is_admin:
        return render_template('consigner_dashboard.html', user=current_user)
    return render_template('consigner_dashboard.html', user=None)


# POST route to log in consigner
@bp.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        if user.is_admin:
            return jsonify({'error': 'Admins cannot log in here'}), 403
        login_user(user)
        return jsonify({'success': True}), 200

    return jsonify({'error': 'Invalid email or password'}), 401


# GET route to fetch current consigner's parts
@bp.route('/api/my-parts')
@login_required
def get_my_parts():
    if current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    parts = Part.query.filter_by(user_id=current_user.id).order_by(Part.date_added.desc()).all()
    result = []

    for p in parts:
        result.append({
            'id': p.id,
            'part_number': p.part_number,
            'serial_number': p.serial_number,
            'description': p.description,
            'condition': p.condition,
            'notes': p.notes,
            'status': p.status,
            'price': p.price,
            'commission_percentage': p.commission_percentage,
            'fixed_fee': p.fixed_fee,
            'invoice_number': p.invoice_number,
            'date_added': p.date_added.strftime('%Y-%m-%d') if p.date_added else '',
            'date_sold': p.date_sold.strftime('%Y-%m-%d') if p.date_sold else ''
        })

    return jsonify(result)