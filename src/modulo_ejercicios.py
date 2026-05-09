from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
import sirope

ejercicios_bp = Blueprint('ejercicios', __name__, url_prefix='/feed')
sirp = sirope.Sirope()

class Ejercicio:
    def __init__(self, nombre, grupo_muscular, descripcion, es_defecto=False):
        self.nombre = nombre
        self.grupo_muscular = grupo_muscular
        self.descripcion = descripcion
        self.es_defecto = es_defecto  # NUEVO: Si es True, no se puede borrar
        self.activo = True

@ejercicios_bp.route('/')
@login_required
def index():
    from modulo_registros import SesionEntrenamiento
    todas_las_sesiones = list(sirp.load_all(SesionEntrenamiento))
    todas_las_sesiones.sort(key=lambda x: x.fecha, reverse=True)
    return render_template('feed_index.html', sesiones=todas_las_sesiones)

# NUEVA RUTA: Para crear ejercicios desde dentro de un entrenamiento sin recargar
@ejercicios_bp.route('/crear_ajax', methods=['POST'])
@login_required
def crear_ajax():
    data = request.get_json()
    nombre = data.get('nombre')
    grupo = data.get('grupo_muscular')
    desc = data.get('descripcion', '')

    if not nombre or not grupo:
        return jsonify({"error": "Faltan campos"}), 400

    nuevo_ej = Ejercicio(nombre, grupo, desc)
    oid = sirp.save(nuevo_ej)
    
    return jsonify({
        "oid": str(oid),
        "nombre": nuevo_ej.nombre
    })

@ejercicios_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        nuevo_ejercicio = Ejercicio(
            request.form.get('nombre'),
            request.form.get('grupo_muscular'),
            request.form.get('descripcion')
        )
        sirp.save(nuevo_ejercicio)
        flash('Ejercicio añadido al catálogo.')
        return redirect(url_for('rutinas.index'))
    return render_template('ejercicios_nuevo.html')

@ejercicios_bp.route('/borrar/<oid_ejercicio>/<tipo>', methods=['POST'])
@login_required
def borrar(oid_ejercicio, tipo):
    from modulo_rutinas import Rutina 
    from modulo_registros import Registro
    
    for rutina in sirp.load_all(Rutina):
        oids_str = [str(oid) for oid in rutina.lista_ejercicios_oids]
        if str(oid_ejercicio) in oids_str:
            rutina.lista_ejercicios_oids = [oid for oid in rutina.lista_ejercicios_oids if str(oid) != str(oid_ejercicio)]
            sirp.save(rutina)
            
    ejercicio_encontrado = None
    for e in sirp.load_all(Ejercicio):
        if str(e.__oid__) == oid_ejercicio:
            ejercicio_encontrado = e
            break
    if getattr(ejercicio_encontrado, 'es_defecto', False):
        flash('No puedes archivar ni borrar los ejercicios base del sistema.', 'error')
        return redirect(url_for('rutinas.index'))
    
    if tipo == 'suave' and ejercicio_encontrado:
        ejercicio_encontrado.activo = False
        sirp.save(ejercicio_encontrado)
        flash('Ejercicio archivado.')
    elif tipo == 'duro':
        if ejercicio_encontrado:
            sirp.delete(ejercicio_encontrado.__oid__)
            flash('Ejercicio destruido permanentemente.')

    return redirect(url_for('rutinas.index'))

@ejercicios_bp.route('/generar_base')
@login_required
def generar_base():
    # Lista de ejercicios intocables
    ejercicios_base = [
        Ejercicio("Press de Banca", "Pecho", "Básico con barra", es_defecto=True),
        Ejercicio("Sentadilla Trasera", "Pierna", "Básico con barra", es_defecto=True),
        Ejercicio("Peso Muerto", "Espalda", "Levantamiento tradicional", es_defecto=True),
        Ejercicio("Dominadas", "Espalda", "Tracción con peso corporal", es_defecto=True),
        Ejercicio("Press Militar", "Brazos", "Empuje vertical de hombros", es_defecto=True)
    ]
    
    for ej in ejercicios_base:
        sirp.save(ej)
        
    flash('¡Ejercicios por defecto generados con éxito!')
    return redirect(url_for('rutinas.index'))