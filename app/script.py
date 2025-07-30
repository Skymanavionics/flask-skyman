from sqlalchemy import text
from app import create_app, db

app = create_app()

with app.app_context():
    # Clear tables
    db.session.execute(text('DELETE FROM parts'))
    db.session.execute(text('DELETE FROM users'))

    # Reset ID sequences
    db.session.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
    db.session.execute(text("ALTER SEQUENCE parts_id_seq RESTART WITH 1"))

    db.session.commit()
    print("✅ Tables cleared and sequences reset")


