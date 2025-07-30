import csv
from datetime import datetime
from sqlalchemy import text
from app import create_app, db
from app.models import Part

app = create_app()
app.app_context().push()

# Path to your CSV file
csv_path = r'C:\Users\seth0\Downloads\UploadParts.csv'

# Clean and normalize value
def clean(value, allow_na=False):
    value = value.strip() if isinstance(value, str) else value
    if not value or value in ('-', 'NA', 'N/A'):
        return value if allow_na else None
    return value

# Parse date safely
def parse_date(value):
    value = clean(value)
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, '%m/%d/%Y')
        except ValueError:
            print(f"⚠️ Invalid date: {value}")
            return None

# Clear existing parts if needed
db.session.execute(text('DELETE FROM parts'))
db.session.commit()
print("✅ Cleared parts table")

# Load and insert parts
with open(csv_path, newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Extract values with cleaning
        part_number = clean(row['part_number'])
        serial_number = clean(row['serial_number'])
        description = clean(row['description'])
        notes = clean(row['notes'])
        condition = clean(row['condition'], allow_na=True)
        price = float(clean(row['price']) or 0)
        shipping = float(clean(row['shipping']) or 0)
        date_added = parse_date(row['date_added'])
        date_sold = parse_date(row['date_sold'])
        invoice_number = clean(row['invoice_number'])
        commission_percentage = float(clean(row['commission_percentage']) or 0) or None
        fixed_fee = float(clean(row['fixed_fee']) or 0) or None
        user_id = int(row['user_id'])

        # Status logic
        raw_status = clean(row['status'], allow_na=True)
        if raw_status in ['Sold', 'Unsold']:
            status = raw_status
        elif invoice_number:
            status = 'Sold'
        else:
            status = 'Unsold'

        # Create part object
        part = Part(
            part_number=part_number,
            serial_number=serial_number,
            description=description,
            notes=notes,
            condition=condition,
            price=price,
            shipping=shipping,
            date_added=date_added,
            date_sold=date_sold,
            status=status,
            commission_percentage=commission_percentage,
            fixed_fee=fixed_fee,
            invoice_number=invoice_number,
            user_id=user_id
        )
        db.session.add(part)

db.session.commit()
print("✅ Parts import complete")
