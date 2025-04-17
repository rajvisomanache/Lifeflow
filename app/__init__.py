from flask import Flask,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config.from_object('app.config.Config')

    db.init_app(app)
    CORS(app)  # Enable CORS if you want frontend-backend communication

    @app.route('/')
    def home():
        return redirect(url_for('routes.login_page'))  # assuming login_page is the function name

    # Register routes after db is initialized
    from app.routes import routes_bp
    app.register_blueprint(routes_bp)

    return app
