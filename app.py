
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from sqlalchemy import extract
from models import db, Usuario, Registro, SolicitudModificacion, Comunidad
from config import (
    MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USE_SSL,
    MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER,
    EMAIL_ADDRESS, EMAIL_PASSWORD,
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY
)

def enviar_correo(destino, asunto, cuerpo):
    msg = Message(subject=asunto, sender=EMAIL_ADDRESS, recipients=[destino])
    msg.body = cuerpo
    mail.send(msg)

def get_comunidad_actual():
    return Comunidad.query.first()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

db.init_app(app)
mail = Mail(app)

with app.app_context():
    db.create_all()
    if Comunidad.query.count() == 0:
        db.session.add(Comunidad(nombre='Comunidad por defecto', subdominio='localhost'))
        db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_env = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_env, use_reloader=debug_env)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        comunidad_actual = get_comunidad_actual()
        if not comunidad_actual:
            return "Comunidad no reconocida"

        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        rol = request.form.get('rol', 'empleado')
        aprobado = 0 if rol == 'supervisor' else 1

        if Usuario.query.filter_by(nombre=nombre).first():
            return "El usuario ya existe"

        hash_pw = generate_password_hash(password)

        nuevo = Usuario(
            nombre=nombre,
            correo=email,
            contrasena=hash_pw,
            rol=rol,
            aprobado=aprobado,
            comunidad_id=comunidad_actual.id
        )

        if rol == 'supervisor':
            total_supervisores = Usuario.query.filter_by(rol='supervisor').count()
            if total_supervisores == 0:
                nuevo.aprobado = True

        db.session.add(nuevo)
        db.session.commit()

        if rol == 'supervisor':
            enviar_correo(EMAIL_ADDRESS, "Nuevo registro como SUPERVISOR",
                          f"El usuario '{nombre}' se ha registrado como SUPERVISOR y requiere aprobación.")
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario and check_password_hash(usuario.contrasena, password):
            if not usuario.aprobado:
                flash('Usuario no aprobado todavía.')
                return redirect(url_for('login'))
            session['user_id'] = usuario.id
            session['nombre'] = usuario.nombre
            session['rol'] = usuario.rol
            return redirect(url_for('index'))
        flash('Credenciales inválidas.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@login_required
def index():
    usuario = Usuario.query.get(session['user_id'])
    hoy = date.today()
    registro = Registro.query.filter_by(usuario_id=usuario.id, fecha=hoy).first()
    entrada = registro.hora_entrada if registro else None
    salida = registro.hora_salida if registro else None
    return render_template('index.html', usuario=usuario.nombre, rol=usuario.rol, entrada=entrada, salida=salida)

@app.route('/entrada', methods=['POST'])
@login_required
def entrada():
    usuario = Usuario.query.get(session['user_id'])
    hoy = date.today()
    registro = Registro.query.filter_by(usuario_id=usuario.id, fecha=hoy).first()
    if not registro:
        registro = Registro(usuario_id=usuario.id, fecha=hoy)
        db.session.add(registro)
    registro.hora_entrada = datetime.now().time()
    db.session.commit()
    flash('Entrada registrada.')
    return redirect(url_for('index'))

@app.route('/salida', methods=['POST'])
@login_required
def salida():
    usuario = Usuario.query.get(session['user_id'])
    hoy = date.today()
    registro = Registro.query.filter_by(usuario_id=usuario.id, fecha=hoy).first()
    if registro and not registro.hora_salida:
        registro.hora_salida = datetime.now().time()
        db.session.commit()
        flash('Salida registrada.')
    else:
        flash('No hay entrada registrada o ya se registró la salida.')
    return redirect(url_for('index'))

@app.route('/solicitar_modificacion', methods=['GET', 'POST'])
@login_required
def solicitar_modificacion():
    if request.method == 'POST':
        tipo = request.form['tipo']
        fecha_str = request.form['fecha']
        hora_str = request.form['hora']
        motivo = request.form['motivo']
        fecha_dt = datetime.fromisoformat(fecha_str)
        hora_dt = datetime.fromisoformat(hora_str)
        solicitud = SolicitudModificacion(
            user_id=session['user_id'],
            fecha=fecha_dt,
            nueva_entrada=hora_dt if tipo == 'entrada' else None,
            nueva_salida=hora_dt if tipo == 'salida' else None,
            motivo=motivo
        )
        db.session.add(solicitud)
        db.session.commit()
        enviar_correo(EMAIL_ADDRESS, 'Nueva solicitud de modificación', f'Usuario {session["nombre"]} solicitó modificación.')
        flash('Solicitud enviada.')
        return redirect(url_for('index'))
    return render_template('solicitud.html')

@app.route('/supervisor')
@login_required
def supervisor():
    if session.get('rol') != 'supervisor':
        return redirect(url_for('index'))
    solicitudes = SolicitudModificacion.query.filter_by(estado='pendiente').all()
    pendientes = Usuario.query.filter_by(rol='supervisor', aprobado=False).all()
    return render_template('supervisor.html', solicitudes=solicitudes, pendientes=pendientes)

@app.route('/autorizar')
@login_required
def autorizar():
    if session.get('rol') != 'supervisor':
        return redirect(url_for('index'))
    solicitud_id = request.args.get('solicitud_id', type=int)
    accion = request.args.get('accion')
    solicitud = SolicitudModificacion.query.get_or_404(solicitud_id)
    if accion == 'aceptar':
        registro = Registro.query.filter_by(usuario_id=solicitud.user_id, fecha=solicitud.fecha.date()).first()
        if registro:
            if solicitud.nueva_entrada:
                registro.hora_entrada = solicitud.nueva_entrada
            if solicitud.nueva_salida:
                registro.hora_salida = solicitud.nueva_salida
        solicitud.estado = 'aceptada'
    else:
        solicitud.estado = 'rechazada'
    solicitud.supervisor_id = session['user_id']
    solicitud.fecha_respuesta = datetime.now()
    db.session.commit()
    flash('Solicitud procesada.')
    return redirect(url_for('supervisor'))

@app.route('/aprobar_supervisor')
@login_required
def aprobar_supervisor():
    if session.get('rol') != 'supervisor':
        return redirect(url_for('index'))
    user_id = request.args.get('user_id', type=int)
    user = Usuario.query.get_or_404(user_id)
    user.aprobado = True
    db.session.commit()
    flash(f'Supervisor {user.nombre} aprobado.')
    return redirect(url_for('supervisor'))

@app.route('/exportar_registros')
@login_required
def exportar_registros():
    usuario = Usuario.query.get(session['user_id'])
    registros = Registro.query.filter_by(usuario_id=usuario.id).order_by(Registro.fecha.desc()).all()
    return render_template('exportar.html', usuario=usuario, registros=registros)

@app.route('/exportar_equipo')
@login_required
def exportar_equipo():
    if session.get('rol') != 'supervisor':
        return redirect(url_for('index'))
    empleado_id = request.args.get('empleado_id', type=int)
    mes = request.args.get('mes')
    empleados = Usuario.query.filter_by(rol='empleado', aprobado=True).all()
    registros = []
    empleado_nombre = ''
    if empleado_id and mes:
        empleado = Usuario.query.get(empleado_id)
        year, month = map(int, mes.split('-'))
        registros = Registro.query.filter(
            Registro.usuario_id == empleado_id,
            extract('year', Registro.fecha) == year,
            extract('month', Registro.fecha) == month
        ).order_by(Registro.fecha).all()
        empleado_nombre = empleado.nombre
    return render_template('exportar_equipo.html', empleados=empleados, registros=registros, empleado_id=empleado_id, empleado_nombre=empleado_nombre)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    mensaje = ''
    if request.method == 'POST':
        nombre = request.form['nombre']
        nueva = request.form['nueva']
        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario:
            usuario.contrasena = generate_password_hash(nueva)
            db.session.commit()
            mensaje = 'Contraseña actualizada.'
        else:
            mensaje = 'Usuario no encontrado.'
    return render_template('reset.html', mensaje=mensaje)
