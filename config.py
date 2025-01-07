import os
import secrets

class Config:
    SECRET_KEY = secrets.token_hex(16)
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 3600
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.abspath('app/database/app.db')}"