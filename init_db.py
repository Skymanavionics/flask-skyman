from app import create_app
from app.models import db, User, Part
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import random

app = create_app()

with app.app_context():
    print("Inserting dummy data into database...")

    # Clear non-admin data
    db.session.query(Part).delete()
    db.session.query(User).filter_by(is_admin=False).delete()

    # Create admin (only if not already created)
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(
            name="Admin",
            code="ADM",
            email="admin@example.com",
            password_hash=generate_password_hash("yourpassword"),
            is_admin=True
        )
        db.session.add(admin)

    # Create 80 consigners with 25 parts each
    conditions = ['AR', 'SV', 'YT']
    descriptions = ['Altimeter', 'Gyro Horizon', 'Transponder', 'Magneto', 'Carburetor']
    cities = ['Dallas', 'Miami', 'Chicago', 'Denver', 'Phoenix']
    states = ['TX', 'FL', 'IL', 'CO', 'AZ']

    for i in range(1, 81):
        consigner = User(
            name=f"Consigner {i}",
            code=f"C{i:02}",
            email=f"consigner{i}@example.com",
            password_hash=generate_password_hash("test123"),
            is_admin=False,
            phone_number=f"555-000-{1000+i}",
            address_line1=f"{100+i} Sample St",
            address_line2=f"Apt {i}" if i % 5 == 0 else None,
            city=random.choice(cities),
            state=random.choice(states),
            zip_code=f"750{i:02}"
        )
        db.session.add(consigner)
        db.session.flush()

        for j in range(1, 51):
            part = Part(
                part_number=f"PN-{i}{j}{random.randint(100, 999)}",
                serial_number=f"SN-{i}{j}{random.randint(1000, 9999)}",
                description=random.choice(descriptions),
                notes=f"Test part {j} for Consigner {i}",
                condition=random.choice(conditions),
                price=round(random.uniform(50, 500), 2),
                shipping=None,
                fixed_fee=None,
                invoice_number=None,
                date_added=datetime.now(timezone.utc),
                status="Unsold",
                commission_percentage=random.randint(0, 100),
                user_id=consigner.id
            )
            db.session.add(part)

    db.session.commit()
    print("Dummy data inserted successfully.")