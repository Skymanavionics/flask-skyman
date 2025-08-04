from app import create_app, db
from app.models import InvoiceInfo

app = create_app()
app.app_context().push()

# Optional: Clear existing if needed
db.session.query(InvoiceInfo).delete()

info = InvoiceInfo(
    company="Skyman Avionics, LLC",
    email="Info@skymanavionics.com",
    phone_number="541-604-9573",
    address_line1="527 NW Elm Ave",
    address_line2="Ste: 3 #523",
    city="Redmond",
    state="OR",
    zip_code="97756"
)

db.session.add(info)
db.session.commit()
print("✅ Invoice info inserted.")