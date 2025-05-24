
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Comunidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    subdominio = db.Column(db.String(50), unique=True, nullable=False)
    fecha_alta = db.Column(db.Date, default=date.today)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    aprobado = db.Column(db.Boolean, default=False)
    comunidad_id = db.Column(db.Integer, db.ForeignKey('comunidad.id'), nullable=False)
    comunidad = db.relationship('Comunidad', backref='usuarios')

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time, nullable=True)
    hora_salida = db.Column(db.Time, nullable=True)
    usuario = db.relationship('Usuario', backref='registros')

class SolicitudModificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    nueva_entrada = db.Column(db.Time, nullable=True)
    nueva_salida = db.Column(db.Time, nullable=True)
    motivo = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    fecha_solicitud = db.Column(db.DateTime, default=datetime.now)
    fecha_respuesta = db.Column(db.DateTime, nullable=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    usuario = db.relationship('Usuario', foreign_keys=[user_id], backref='solicitudes')
    supervisor = db.relationship('Usuario', foreign_keys=[supervisor_id])
