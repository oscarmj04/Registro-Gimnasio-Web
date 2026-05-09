from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import sirope

registros_bp = Blueprint('registros', __name__, url_prefix='/registros')
sirp = sirope.Sirope()

# Mantenemos el antiguo para evitar errores con caché residual
class Registro:
    def __init__(self, user_id, ejercicio_oid, peso, repeticiones):
        self.user_id = user_id
        self.ejercicio_oid = ejercicio_oid
        self.peso = peso
        self.repeticiones = repeticiones
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

class SesionEntrenamiento:
    def __init__(self, usuario_oid, nombre_rutina, duracion, ejercicios_data):
        self.usuario_oid = str(usuario_oid)
        self.nombre_rutina = nombre_rutina
        self.duracion = duracion
        self.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.ejercicios_data = ejercicios_data

@registros_bp.route('/')
@login_required
def index():
    todas = list(sirp.load_all(SesionEntrenamiento))
    mis_sesiones = [s for s in todas if s.usuario_oid == str(current_user.get_id())]
    
    # EL VERDADERO CAMBIO: Ordenamos matemáticamente leyendo el texto de la fecha
    mis_sesiones.sort(
        key=lambda x: datetime.strptime(x.fecha, "%d/%m/%Y %H:%M"), 
        reverse=True
    )
    
    return render_template('registros_index.html', sesiones=mis_sesiones)

@registros_bp.route('/detalle/<oid_sesion>')
@login_required
def detalle(oid_sesion):
    sesion = next((s for s in sirp.load_all(SesionEntrenamiento) if str(s.__oid__) == oid_sesion), None)
    return render_template('historial_detalle.html', sesion=sesion)

@registros_bp.route('/borrar_sesion/<oid_sesion>', methods=['POST'])
@login_required
def borrar_sesion(oid_sesion):
    for s in sirp.load_all(SesionEntrenamiento):
        if str(s.__oid__) == oid_sesion and s.usuario_oid == str(current_user.get_id()):
            sirp.delete(s.__oid__)
            flash('Sesión de entrenamiento eliminada del historial.')
            break
    return redirect(url_for('registros.index'))