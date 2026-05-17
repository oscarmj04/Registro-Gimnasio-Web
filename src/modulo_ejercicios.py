from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify
from flask_login import login_required, current_user
import sirope

ejercicios_bp = Blueprint('ejercicios', __name__, url_prefix='/ejercicios')
sirp = sirope.Sirope()

class Ejercicio:
    def __init__(self, nombre, grupo_muscular, descripcion="", es_defecto=False, user_id=None):
        self.nombre = nombre
        self.grupo_muscular = grupo_muscular
        self.descripcion = descripcion
        self.es_defecto = es_defecto
        self.user_id = user_id  # Guardamos qué usuario creó el ejercicio personalizado
        self.activo = True

@ejercicios_bp.route('/')
@login_required
def index():
    from modulo_registros import SesionEntrenamiento
    
    # 1. Cargamos todos los ejercicios del catálogo (sistema + personalizados del usuario)
    lista_ejercicios = [e for e in sirp.load_all(Ejercicio) 
                        if getattr(e, 'activo', True) and (getattr(e, 'es_defecto', False) or getattr(e, 'user_id', None) == current_user.get_id())]
    
    # 2. Obtenemos tus entrenamientos ordenados de más nuevo a más viejo
    mis_entrenamientos = sorted(
        [s for s in sirp.load_all(SesionEntrenamiento) if s.usuario_oid == str(current_user.get_id())],
        key=lambda x: x.fecha, reverse=True
    )
    
    # 3. Mapeamos la última marca usando llaves de tipo texto plano directamente
    ultimas_marcas = {}
    for ej in lista_ejercicios:
        oid_texto = str(ej.__oid__)  # Convertimos el OID a texto aquí en Python
        ultimas_marcas[oid_texto] = None
        
        for entreno in mis_entrenamientos:
            # Buscamos si el ejercicio se realizó en esta sesión
            ej_registrado = next((data for data in entreno.ejercicios_data if data['nombre'] == ej.nombre), None)
            
            if ej_registrado and ej_registrado.get('series'):
                # Buscamos su serie con mayor kilaje de ese día
                mejor_serie = max(ej_registrado['series'], key=lambda s: float(s.get('peso', 0)))
                ultimas_marcas[oid_texto] = {
                    'fecha': entreno.fecha.split(" ")[0],
                    'peso': mejor_serie.get('peso'),
                    'reps': mejor_serie.get('reps')
                }
                break  # Encontrado el más reciente, pasamos al siguiente ejercicio
                
    return render_template('ejercicios_index.html', ejercicios=lista_ejercicios, marcas=ultimas_marcas)

@ejercicios_bp.route('/personalizados')
@login_required
def personalizados():
    mis_ejercicios = [e for e in sirp.load_all(Ejercicio) 
                      if not getattr(e, 'es_defecto', False) and getattr(e, 'user_id', None) == current_user.get_id()]
    return render_template('ejercicios_personalizados.html', ejercicios=mis_ejercicios)

@ejercicios_bp.route('/nuevo_personalizado', methods=['POST'])
@login_required
def nuevo_personalizado():
    nombre = request.form.get('nombre')
    grupo = request.form.get('grupo_muscular')
    desc = request.form.get('descripcion', '')
    
    if nombre and grupo:
        nuevo_ej = Ejercicio(nombre, group_muscular=grupo, descripcion=desc, es_defecto=False, user_id=current_user.get_id())
        sirp.save(nuevo_ej)
        flash('Ejercicio personalizado creado con éxito.')
    return redirect(url_for('ejercicios.personalizados'))

@ejercicios_bp.route('/borrar_total/<oid_ejercicio>', methods=['POST'])
@login_required
def borrar_total(oid_ejercicio):
    from modulo_rutinas import Rutina
    
    for rutina in sirp.load_all(Rutina):
        oids_filtrados = [oid for oid in rutina.lista_ejercicios_oids if str(oid) != str(oid_ejercicio)]
        if len(oids_filtrados) != len(rutina.lista_ejercicios_oids):
            rutina.lista_ejercicios_oids = oids_filtrados
            sirp.save(rutina)
            
    ejercicio_encontrado = None
    for e in sirp.load_all(Ejercicio):
        if str(e.__oid__) == oid_ejercicio:
            ejercicio_encontrado = e
            break
            
    if ejercicio_encontrado:
        if getattr(ejercicio_encontrado, 'es_defecto', False):
            flash('No se pueden eliminar los ejercicios base del sistema.', 'error')
        else:
            sirp.delete(ejercicio_encontrado.__oid__)
            flash('Ejercicio personalizado eliminado por completo del sistema y de tus rutinas.')
            
    return redirect(url_for('ejercicios.personalizados'))

@ejercicios_bp.route('/crear_ajax', methods=['POST'])
@login_required
def crear_ajax():
    data = request.get_json()
    nombre = data.get('nombre')
    grupo = data.get('grupo_muscular')
    
    if not nombre:
        return jsonify({'error': 'Falta el nombre'}), 400
        
    nuevo_ej = Ejercicio(nombre, grupo, "", es_defecto=False, user_id=current_user.get_id())
    oid = sirp.save(nuevo_ej)
    
    return jsonify({
        'oid': str(oid),
        'nombre': nuevo_ej.nombre
    })

@ejercicios_bp.route('/generar_base')
@login_required
def generar_base():
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
