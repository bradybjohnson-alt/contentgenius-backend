import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.order import Order
from src.models.content import Content
from src.models.payment import Payment
from src.models.content_template import ContentTemplate
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.order import order_bp
from src.routes.content import content_bp
from src.routes.payment import payment_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app, origins=[
    "http://localhost:5173",  # Development frontend
    "https://contentgenius.app",  # Production domain
    "https://www.contentgenius.app",  # Production domain with www
    "https://contentgenius-frontend.onrender.com"  # Render frontend URL
])

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(order_bp, url_prefix='/api')
app.register_blueprint(content_bp, url_prefix='/api')
app.register_blueprint(payment_bp, url_prefix='/api/payment')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Production database (PostgreSQL on Render)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development database (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/app.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    # Initialize default content templates
    from src.utils.init_data import initialize_content_templates, create_admin_user
    initialize_content_templates()
    create_admin_user()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')
