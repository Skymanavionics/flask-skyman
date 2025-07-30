from datetime import datetime, timezone
from flask_login import UserMixin
from app import db  # Ensure this is imported

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(6), unique=True, nullable=False)  # 3-digit consigner code
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    phone_number = db.Column(db.String(20), nullable=True)
    address_line1 = db.Column(db.String(150), nullable=True)
    address_line2 = db.Column(db.String(150), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)

    parts = db.relationship('Part', backref='consigner', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.name} ({'Admin' if self.is_admin else 'Consigner'})>"


class Part(db.Model):
    __tablename__ = 'parts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(50), nullable=True)
    serial_number = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    condition = db.Column(db.String(20), nullable=True)
    price = db.Column(db.Float, nullable=True)
    shipping = db.Column(db.Float, nullable=True)
    date_added = db.Column(db.Date, default=datetime.now(timezone.utc), nullable = True)
    date_sold = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Unsold')  # 'Sold' or 'Unsold'
    commission_percentage = db.Column(db.Float, nullable=True)
    fixed_fee = db.Column(db.Float, nullable=True)
    invoice_number = db.Column(db.String(50), nullable=True)



    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Part {self.part_number} | Status: {self.status}>"

class InvoiceInfo(db.Model):
    __tablename__ = 'invoice_info'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    address_line1 = db.Column(db.String(150), nullable=True)
    address_line2 = db.Column(db.String(150), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<InvoiceInfo {self.company}>"