from app import app, db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(120), unique=True, nullable=False)
    saldo = db.Column(db.Integer)
    dolares = db.Column(db.Integer, nullable=False, default=0)

class Transferencias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_usuario_remitente = db.Column(db.Integer, nullable=False)
    id_usuario_beneficiario = db.Column(db.Integer, nullable=False)
    transaccion = db.Column(db.Integer, nullable=False)

class Prestamos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, nullable=False)
    cuotas = db.Column(db.Integer, nullable=False)
    cuotas_pagadas = db.Column(db.Integer, nullable=True)
    cuota_mensual = db.Column(db.Integer)
    interes_anual = db.Column(db.Integer, nullable=False)
    monto = db.Column(db.Integer, nullable=False)
    monto_total = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()