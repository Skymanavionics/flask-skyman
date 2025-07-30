import csv
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Part

def populate_from_csv():
    # Clear tables
    db.session.query(Part).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("✅ Cleared users and parts")

    # Load CSV
    with open('UploadUsers.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row['email'] or not row['name'] or not row['code']:
                continue

            password = row['password_hash']
            if not password or not password.startswith('pbkdf2:'):
                password = generate_password_hash(password or "changeme")

            user = User(
                name=row['name'],
                code=row['code'],
                email=row['email'],
                password_hash=password,
                is_admin=row['is_admin'].strip() == '1',
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(timezone.utc),
                phone_number=row.get('phone_number'),
                address_line1=row.get('address_line1'),
                address_line2=row.get('address_line2'),
                city=row.get('city'),
                state=row.get('state'),
                zip_code=row.get('zip_code')
            )
            db.session.add(user)

    db.session.commit()
    print("✅ CSV import complete")

if __name__ == '__main__':
    app = create_app()
    app.app_context().push()
    populate_from_csv()

