import csv
from datetime import datetime
from sqlalchemy import text
from app import create_app, db
from app.models import Part

def clean(value, allow_na=False):
    value = value.strip() if isinstance(value, str) else value
    if not value or value in ('-', 'NA', 'N/A'):
        return value if allow_na else None
    return value

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

def consigner_parts():

    with open('ConsignerParts.csv', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            part_number = clean(row['part_number'])
            serial_number = clean(row['serial_number'])
            description = clean(row['description'])
            notes = clean(row['notes'])
            condition = clean(row['condition'], allow_na=True)

            try:
                price = float(clean(row['price']) or 0)
            except ValueError:
                price = 0

            try:
                shipping = float(clean(row['shipping']) or 0)
            except ValueError:
                shipping = 0

            date_added = parse_date(row['date_added'])
            date_sold = parse_date(row['date_sold'])
            invoice_number = clean(row['invoice_number'])

            try:
                commission_percentage = float(clean(row['commission_percentage']) or 0)
            except ValueError:
                commission_percentage = None

            try:
                fixed_fee = float(clean(row['fixed_fee']) or 0)
            except ValueError:
                fixed_fee = None

            try:
                user_id = int(row['user_id'])
            except ValueError:
                user_id = None

            raw_status = clean(row['status'], allow_na=True)
            if raw_status in ['Sold', 'Unsold']:
                status = raw_status
            elif invoice_number:
                status = 'Sold'
            else:
                status = 'Unsold'

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

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    consigner_parts()