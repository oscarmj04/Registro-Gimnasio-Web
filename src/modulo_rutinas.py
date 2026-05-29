from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from modulo_registros import SesionEntrenamiento
import sirope

rutinas_bp = Blueprint('rutinas', __name__, url_prefix='/rutinas')
sirp = sirope.Sirope()

class Rutina:
    def __init__(self, nombre, user_id, lista_ejercicios_oids):
        self.nombre = nombre
        self.user_id = user_id
        self.lista_ejercicios_oids = lista_ejercicios_oids

@rutinas_bp.route('/')
@login_required
def index():
    todas_rutinas = list(sirp.load_all(Rutina))
    mis_rutinas = [r for r in todas_rutinas if r.user_id == current_user.get_id()]
    return render_template('rutinas_index.html', rutinas=mis_rutinas)

@rutinas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    from modulo_ejercicios import Ejercicio
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        ejercicios_ids = request.form.getlist('ejercicios_seleccionados')
        
        nueva_r = Rutina(nombre, current_user.get_id(), ejercicios_ids)
        sirp.save(nueva_r)
        flash(f'Rutina "{nombre}" creada correctamente.')
        return redirect(url_for('rutinas.index'))

    catalogo = [e for e in sirp.load_all(Ejercicio) if getattr(e, 'activo', True)]
    return render_template('rutinas_nueva.html', catalogo=catalogo)

@rutinas_bp.route('/editar/<oid_rutina>')
@login_required
def editar(oid_rutina):
    from modulo_ejercicios import Ejercicio
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    if not rutina:
        flash("Error: Rutina no encontrada", "error")
        return redirect(url_for('rutinas.index'))
    
    ejercicios_actuales = []
    for e_oid in rutina.lista_ejercicios_oids:
        ej = next((e for e in sirp.load_all(Ejercicio) if str(e.__oid__) == e_oid), None)
        if ej: ejercicios_actuales.append(ej)

    catalogo = [e for e in sirp.load_all(Ejercicio) if getattr(e, 'activo', True)]
    return render_template('rutinas_editar.html', rutina=rutina, ejercicios=ejercicios_actuales, catalogo=catalogo)

@rutinas_bp.route('/actualizar/<oid_rutina>', methods=['POST'])
@login_required
def actualizar(oid_rutina):
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    if rutina:
        rutina.nombre = request.form.get('nombre')
        rutina.lista_ejercicios_oids = request.form.getlist('ejercicios_seleccionados')
        sirp.save(rutina)
        flash('Rutina actualizada correctamente.')
    return redirect(url_for('rutinas.index'))

@rutinas_bp.route('/borrar/<oid_rutina>', methods=['POST'])
@login_required
def borrar(oid_rutina):
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    if rutina and rutina.user_id == current_user.get_id():
        sirp.delete(rutina.__oid__)
        flash('Rutina eliminada.')
    return redirect(url_for('rutinas.index'))

@rutinas_bp.route('/entrenar/<oid_rutina>')
@login_required
def entrenar(oid_rutina):
    from modulo_ejercicios import Ejercicio
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    
    ejercicios_rutina = []
    for e_oid in rutina.lista_ejercicios_oids:
        ej = next((e for e in sirp.load_all(Ejercicio) if str(e.__oid__) == e_oid), None)
        if ej: ejercicios_rutina.append(ej)

    catalogo = [e for e in sirp.load_all(Ejercicio) 
                if getattr(e, 'activo', True) and 
                (getattr(e, 'es_defecto', False) or getattr(e, 'user_id', None) == current_user.get_id())]
    
    # Pasamos 'catalogo' al template
    return render_template('rutinas_entrenar.html', 
                           rutina=rutina, 
                           ejercicios=ejercicios_rutina, 
                           catalogo=catalogo)

        
@rutinas_bp.route('/finalizar/<oid_rutina>', methods=['POST'])
@login_required
def finalizar(oid_rutina):
    rutina_actual = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    
    # Recogemos de forma segura las listas enviadas por el formulario
    ejercicios_ids = request.form.getlist('ejercicio_id')
    datos_completos = []
    
    for index, eid in enumerate(ejercicios_ids):
        # Obtenemos el nombre correspondiente a este ejercicio concreto
        nombre_ej = request.form.get(f'nombre_ejercicio_{eid}')
        
        # Recuperamos los pesos y repeticiones específicos de este ID de ejercicio
        pesos = request.form.getlist(f'peso_{eid}')
        reps = request.form.getlist(f'reps_{eid}')
        
        series_ejercicio = []
        for i in range(len(pesos)):
            # Evitamos guardar filas vacías o incompletas
            if pesos[i].strip() and reps[i].strip():
                series_ejercicio.append({
                    'peso': pesos[i].strip(),
                    'reps': reps[i].strip()
                })
        
        # Solo añadimos el ejercicio si el usuario ha completado al menos una serie
        if series_ejercicio:
            datos_completos.append({
                'nombre': nombre_ej,
                'series': series_ejercicio
            })

    if datos_completos and rutina_actual:
        # ARREGLO DEL HISTORIAL Y FEED: Guardamos explícitamente con el username del atleta
        nueva_sesion = SesionEntrenamiento(
            usuario_oid=current_user.username, 
            nombre_rutina=rutina_actual.nombre, 
            duracion=request.form.get('duracion', '00:00'), 
            ejercicios_data=datos_completos
        )
        sirp.save(nueva_sesion)
        flash('¡Entrenamiento guardado y publicado en el muro con éxito!')
        
        # ARREGLO DEL REDIRECT: Te redirige al Feed/Muro social para ver tu publicación
        return redirect(url_for('registros.feed'))
    else:
        flash('No se pudo guardar el entrenamiento porque no añadiste ninguna serie.', 'error')
        return redirect(url_for('rutinas.index'))