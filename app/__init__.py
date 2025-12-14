import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'dev_key_secret' 

    db.init_app(app)

    with app.app_context():
        from . import models
        
        intentos = 0
        while intentos < 10:
            try:
                db.create_all()
                print(">>> Base de datos conectada y tablas creadas exitosamente.")
                break
            except OperationalError:
                print(">>> Esperando a MySQL...")
                time.sleep(3)
                intentos += 1
        
        from .routes import main_bp
        app.register_blueprint(main_bp)

    return app