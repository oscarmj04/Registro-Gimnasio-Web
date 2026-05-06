from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import sirope

registros_bp = Blueprint('registros', __name__, url_prefix='/registros')
sirp = sirope.Sirope()

class Registro:
    def __init__(self, user_id, ejercicio_oid, peso, repeticiones):
        self.user_id = user_id
        self.ejercicio_oid = ejercicio_oid
        self.peso = peso
        self.repeticiones = repeticiones
        # Guardamos la fecha actual en formato texto (ej: 2026-05-04)
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

@registros_bp.route('/')
@login_required
def index():
    todos_registros = list(sirp.load_all(Registro))
    # Filtramos para mostrar solo el historial del usuario actual
    mis_registros = [r for r in todos_registros if r.user_id == current_user.get_id()]
    
    # Cargamos los nombres de los ejercicios para mostrarlos en el HTML
    from modulo_ejercicios import Ejercicio
    todos_ejercicios = {str(e.__oid__): e.nombre for e in sirp.load_all(Ejercicio)}
    
    return render_template('registros_index.html', registros=mis_registros, ejercicios_dict=todos_ejercicios)

@registros_bp.route('/nuevo', methods=['POST'])
@login_required
def nuevo():
    # Esta ruta será llamada por JavaScript más adelante sin recargar la página,
    # pero por ahora la dejamos lista para recibir datos de un formulario normal.
    ejercicio_oid = request.form.get('ejercicio_oid')
    peso = request.form.get('peso')
    repeticiones = request.form.get('repeticiones')
    
    nuevo_registro = Registro(current_user.get_id(), ejercicio_oid, float(peso), int(repeticiones))
    sirp.save(nuevo_registro)
    
    flash('Serie registrada con éxito.')
    # Volvemos a la página anterior (suele ser la vista de la rutina)
    return redirect(request.referrer or url_for('rutinas.index'))