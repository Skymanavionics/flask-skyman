from flask import Blueprint, render_template
from flask_login import login_required, current_user
from functools import wraps
from app.models import Part, User, InvoiceInfo
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from datetime import datetime
from app import db
# import pdfkit
from flask import send_file
from jinja2 import Template
from io import BytesIO
from app.extensions import mail
from flask_mail import Message
from weasyprint import HTML
import os
from flask import current_app

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Only allow access if current user is admin
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return "Access denied", 403
        return f(*args, **kwargs)
    return wrapper

@bp.route('/parts')
@login_required
@admin_required
def parts():
    all_parts = Part.query.filter(Part.status == 'Unsold').join(User).add_columns(
        Part.id,
        Part.part_number,
        Part.serial_number,
        Part.description,
        Part.condition,
        Part.date_added,
        Part.price,
        User.code.label('consigner_code')
    ).all()

    return render_template('admin_parts.html', parts=all_parts)

@bp.route('/consigners')
@login_required
@admin_required
def consigners():
    consigners = User.query.filter_by(is_admin=False).order_by(User.created_at.asc()).all()
    return render_template('admin_consigners.html', consigners=consigners)

@bp.route('/api/consigners')
@login_required
@admin_required
def api_consigners():
    name = request.args.get('name', '').strip().lower()
    code = request.args.get('code', '').strip().lower()
    date = request.args.get('date', '').strip()

    query = User.query.filter_by(is_admin=False)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if code:
        query = query.filter(User.code.ilike(f"%{code}%"))
    if date:
        query = query.filter(func.date(User.created_at) == date)

    consigners = query.order_by(User.created_at.desc()).all()

    return jsonify([
        {
            'id': consigner.id,
            'name': consigner.name,
            'code': consigner.code,
            'created_at': consigner.created_at.strftime('%Y-%m-%d')
        }
        for consigner in consigners
    ])


@bp.route('/api/consigners/new', methods=['POST'])
@login_required
@admin_required
def add_consigner():
    data = request.get_json()

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 400

    if User.query.filter_by(code=data['code']).first():
        return jsonify({'success': False, 'message': 'Code already exists'}), 400

    new_user = User(
        name=data['name'],
        code=data['code'],
        email=data['email'],
        password_hash=generate_password_hash(data['password_hash']),
        is_admin=False,
        created_at=datetime.strptime(data['created_at'], '%Y-%m-%d'),
        phone_number=data.get('phone_number'),
        address_line1=data.get('address_line1'),
        address_line2=data.get('address_line2'),
        city=data.get('city'),
        state=data.get('state'),
        zip_code=data.get('zip_code')
    )
    db.session.add(new_user)
    db.session.commit()

    # Render the HTML welcome email
    welcome_html = render_template(
        'welcome_email.html',
        name=new_user.name,
        email=new_user.email,
        temp_password=data['password_hash']
    )

    # Plain text version
    welcome_text = f"""
    Hi {new_user.name},

    Welcome to Skyman Avionics! We're excited to have you onboard as a consigner.

    Your account has been created with the email: {new_user.email}
    Your account currently has a temporary password which must be changed.

    To reset your password, click the link below:
    https://skymanavionicsparts.com/forgot-password
    Enter your account email to be sent a link to reset your password.
    
    Once completed, you can log in with your account email and new password.

    If you have any questions, feel free to reach out.

    Best regards,
    Skyman Avionics Team
    """

    # Construct Flask-Mail message
    msg = Message(
        subject="Welcome to Skyman Avionics!",
        #sender="Skyman Avionics <noreply@mg.skymanavionicsparts.com>",
        recipients=[new_user.email]
    )
    msg.body = welcome_text
    msg.html = welcome_html

    # Send the email
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

    return jsonify({'success': True, 'message': 'Consigner added successfully'}), 201

@bp.route('/api/consigners/<int:consigner_id>/parts')
@login_required
@admin_required
def get_consigner_parts(consigner_id):
    status = request.args.get('status')  # Optional filter for 'Sold', 'Unsold', etc.

    consigner = User.query.get_or_404(consigner_id)

    # Apply filter (if status is provided)
    query = Part.query.filter(Part.user_id == consigner_id)
    if status:
        query = query.filter(Part.status == status)

    parts = query.order_by(Part.date_added.desc()).all()

    return jsonify({
        'consigner': {
            'id': consigner.id,
            'name': consigner.name,
            'code': consigner.code,
            'email': consigner.email,
            'created_at': consigner.created_at.strftime('%Y-%m-%d'),
            'phone_number': consigner.phone_number,
            'address_line1': consigner.address_line1,
            'address_line2': consigner.address_line2,
            'city': consigner.city,
            'state': consigner.state,
            'zip_code': consigner.zip_code
        },
        'parts': [
            {
                'id': part.id,
                'part_number': part.part_number,
                'serial_number': part.serial_number,
                'description': part.description,
                'condition': part.condition,
                'commission_percentage': part.commission_percentage,
                'fixed_fee': part.fixed_fee,
                'price': part.price,
                'shipping': part.shipping,
                'date_added': part.date_added.strftime('%Y-%m-%d'),
                'date_sold': part.date_sold.strftime('%Y-%m-%d') if part.date_sold else None,
                'notes': part.notes,
                'status': part.status,
                'invoice_number': part.invoice_number  # Include if needed
            }
            for part in parts
        ]
    })



@bp.route('/api/parts/<int:part_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_part(part_id):
    part = Part.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    return jsonify({'message': 'Part deleted successfully'}), 200

@bp.route('/api/parts/<int:part_id>', methods=['PUT'])
@login_required
def update_part_field(part_id):
    if not current_user.is_admin:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    date_sold_input = data.get('date_sold')  # Optional
    shipping = data.get('shipping')  # Optional
    notes = data.get('notes')        # Optional

    allowed_fields = {
        'part_number': str,
        'serial_number': str,
        'description': str,
        'condition': str,
        'commission_percentage': float,
        'fixed_fee': float,
        'price': float,
        'shipping': float,
        'date_added': str,  # assuming YYYY-MM-DD
        'date_sold': str,
        'notes': str,
        'status': str
    }

    part = Part.query.get_or_404(part_id)

    # Regular single field update (non-status)
    if field != 'status':
        if field not in allowed_fields:
            return jsonify({"message": "Invalid field."}), 400

        try:
            casted_value = allowed_fields[field](value)
        except Exception:
            return jsonify({"message": f"Invalid value for {field}."}), 400

        if field == 'commission_percentage':
            if not (0 <= casted_value <= 100):
                return jsonify({"message": "Commission must be between 0 and 100."}), 400

        if field == 'date_added':
            try:
                casted_value = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

        if field == 'date_sold':
            try:
                casted_value = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

        setattr(part, field, casted_value)

    # Special handling for status = Sold with extra fields
    else:
        part.status = value

        if value == 'Sold':
            # Set date_sold
            if date_sold_input:
                try:
                    part.date_sold = datetime.strptime(date_sold_input, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({"message": "Invalid date_sold format. Use YYYY-MM-DD."}), 400
            else:
                part.date_sold = datetime.utcnow().date()

            # Set shipping if provided
            if shipping is not None:
                try:
                    part.shipping = float(shipping)
                except ValueError:
                    return jsonify({"message": "Invalid shipping value."}), 400

            # Set notes if provided
            if notes is not None:
                part.notes = notes

        elif value == 'Unsold':
            part.date_sold = None
            part.shipping = None
            part.invoice_number = None

        if value == 'Sold':
            # Existing date_sold, shipping, notes logic...

            # Send email
            user = User.query.get(part.user_id)
            if user:
                msg = Message(
                    subject=f"Part Sold — {user.code}",
                    recipients=["kelsey@skymanavionics.com"]
                )
                msg.body = (
                    f"A part has been marked as sold.\n\n"
                    f"Consigner Code: {user.code}\n"
                    f"Part Number: {part.part_number}\n"
                    f"Serial Number: {part.serial_number}\n"
                    f"Description: {part.description}\n"
                    f"Condition: {part.condition}\n"
                    f"Price: ${part.price:.2f}"
                )
                mail.send(msg)

    db.session.commit()
    return jsonify({"message": "Part updated successfully."}), 200

@bp.route('/api/parts/new', methods=['POST'])
@login_required
@admin_required
def create_new_part():
    data = request.get_json()

    try:
        commission = data.get('commission_percentage')
        fixed_fee = data.get('fixed_fee')

        if commission and fixed_fee:
            return jsonify({'message': 'Provide only one of commission percentage or fixed fee.'}), 400

        if commission:
            commission = float(commission)
        if fixed_fee:
            fixed_fee = float(fixed_fee)

        part = Part(
            part_number=data['part_number'],
            serial_number=data['serial_number'],
            description=data['description'],
            condition=data['condition'],
            date_added=datetime.strptime(data['date_added'], '%Y-%m-%d'),
            price=float(data['price']),
            notes=data.get('notes', ''),
            commission_percentage=commission if commission else None,
            fixed_fee=fixed_fee if fixed_fee else None,
            user_id=data['consigner_id']
        )
        db.session.add(part)
        db.session.commit()

        return jsonify({'message': 'Part added successfully'}), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 400

@bp.route('/api/consigners/<int:consigner_id>', methods=['PUT'])
@login_required
@admin_required
def update_consigner_field(consigner_id):
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')

    allowed_fields = {
        'name': str,
        'email': str,
        'code': str,
        'created_at': str,
        'phone_number': str,
        'address_line1': str,
        'address_line2': str,
        'city': str,
        'state': str,
        'zip_code': str
    }

    if field not in allowed_fields:
        return jsonify({"message": "Invalid field"}), 400

    consigner = User.query.get_or_404(consigner_id)

    try:
        if field == 'created_at':
            value = datetime.strptime(value, '%Y-%m-%d')
        else:
            value = allowed_fields[field](value)
    except Exception:
        return jsonify({"message": "Invalid value."}), 400

    # Check for uniqueness (excluding the current consigner)
    if field == 'email':
        existing = User.query.filter(User.email == value, User.id != consigner_id).first()
        if existing:
            return jsonify({"message": "This email is already in use."}), 400

    if field == 'code':
        existing = User.query.filter(User.code == value, User.id != consigner_id).first()
        if existing:
            return jsonify({"message": "This code is already in use."}), 400

    setattr(consigner, field, value)
    db.session.commit()

    return jsonify({"message": f"{field} updated successfully"}), 200

@bp.route('/api/consigners/<int:consigner_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_consigner(consigner_id):
    consigner = User.query.get_or_404(consigner_id)

    # Delete all parts associated with the consigner
    Part.query.filter_by(user_id=consigner_id).delete()

    # Then delete the consigner
    db.session.delete(consigner)
    db.session.commit()

    return jsonify({"message": "Consigner and associated parts deleted."}), 200

from flask import jsonify, request
from sqlalchemy import asc, desc

@bp.route('/api/parts')
@login_required
@admin_required
def api_parts():
    query = Part.query.join(User).filter(Part.status == 'Unsold')
    #query = Part.query.join(User)

    # Filters
    part_number = request.args.get('part_number', '').strip().lower()
    serial = request.args.get('serial', '').strip().lower()
    description = request.args.get('description', '').strip().lower()
    condition = request.args.get('condition', '').strip()
    date = request.args.get('date', '').strip()
    code = request.args.get('code', '').strip().lower()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 40))

    if part_number:
        query = query.filter(Part.part_number.ilike(f"%{part_number}%"))
    if serial:
        query = query.filter(Part.serial_number.ilike(f"%{serial}%"))
    if description:
        query = query.filter(Part.description.ilike(f"%{description}%"))
    if condition:
        query = query.filter(Part.condition == condition)
    if date:
        query = query.filter(Part.date_added == date)
    if code:
        query = query.filter(User.code.ilike(f"%{code}%"))

    total = query.count()
    parts = query.add_columns(
        Part.part_number,
        Part.serial_number,
        Part.description,
        Part.condition,
        Part.date_added,
        Part.price,
        Part.notes,
        User.code.label('consigner_code')
    ).offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for row in parts:
        _, part_number, serial_number, description, condition, date_added, price, notes, consigner_code = row
        results.append({
            'part_number': part_number,
            'serial_number': serial_number,
            'description': description,
            'condition': condition,
            'date_added': date_added.strftime('%Y-%m-%d'),
            'price': price,
            'consigner_code': consigner_code,
            'notes': notes or ""
        })

    return jsonify({
        'parts': results,
        'total': total
    })


@bp.route('/api/generate-invoice', methods=['POST'])
@login_required
@admin_required
def generate_invoice():
    data = request.get_json()
    part_ids = data['part_ids']
    quantities = data['quantities']  # { part_id: qty }
    invoice_number = data['invoice_number']
    invoice_numbers = data['invoice_numbers']
    payment_method = data['payment_method']

    invoice_date_str = data.get('invoice_date')
    try:
        invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid invoice date format."}), 400

    # ❗ If shipping_fee is no longer passed from the form, default to 0
    shipping_fee = float(data.get('shipping_fee', 0.0))
    misc_fee = float(data['misc_fee'])

    parts = Part.query.filter(Part.id.in_(part_ids)).all()
    if not parts:
        return jsonify({'message': 'No parts found'}), 400

    consigner = User.query.get(parts[0].user_id)
    billing_info = InvoiceInfo.query.first()

    # Calculate totals and structure the data
    invoice_parts = []
    subtotal = 0
    for part in parts:
        qty = quantities[str(part.id)]

        # Use fixed_fee if it exists; otherwise use commission_percentage
        if part.fixed_fee is not None:
            total = qty * (part.price - part.fixed_fee - part.shipping)
        elif part.commission_percentage is not None:
            total = qty * (part.price - part.shipping) * (1 - (part.commission_percentage / 100))
        else:
            total = qty * (part.price - part.shipping)

        subtotal += total

        part_invoice_number = invoice_numbers.get(str(part.id)) or invoice_number
        part.invoice_number = part_invoice_number

        invoice_parts.append({
            'description': part.description,
            'qty': qty,
            'price': part.price,
            'commission': part.commission_percentage,
            'shipping': part.shipping,
            'fixed_fee': part.fixed_fee,
            'total': total,
            'invoice_number': part_invoice_number
        })

    db.session.commit()

    grand_total = subtotal - shipping_fee - misc_fee

    logo_path = os.path.join(current_app.root_path, 'static', 'logo.png')

    rendered_html = render_template(
        'invoice_template.html',
        consigner=consigner,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        billing=billing_info,
        items=invoice_parts,
        shipping=shipping_fee,
        misc=misc_fee,
        grand_total=grand_total,
        payment_method=payment_method,  # ✅ make sure this was passed too
        logo_path = logo_path
    )

    # Generate PDF
    pdf = HTML(string=rendered_html, base_url=request.base_url).write_pdf()

    return send_file(
        BytesIO(pdf),
        as_attachment=True,
        download_name=f"Invoice_{invoice_number}.pdf",
        mimetype='application/pdf'
    )




