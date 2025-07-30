from flask import Flask
from app.extensions import db
from flask_login import LoginManager
from app.models import db, User
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask_migrate import Migrate

login_manager = LoginManager()
login_manager.login_view = 'login'  # Redirect here if user not logged in

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)

    # Import and register blueprints
    from app.routes import admin_routes, consigner_routes, auth_routes
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(consigner_routes.bp)
    app.register_blueprint(auth_routes.bp)

    return app

# Load user from session for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
