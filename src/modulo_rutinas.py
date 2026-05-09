from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
import sirope

rutinas_bp = Blueprint('rutinas', __name__, url_prefix='/rutinas')
sirp = sirope.Sirope()

class Rutina:
    def __init__(self, nombre, user_id, lista_ejercicios_oids=None):
        self.nombre = nombre
        self.user_id = user_id
        self.lista_ejercicios_oids = lista_ejercicios_oids if lista_ejercicios_oids else []

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

    # Si es GET, cargamos el catálogo para el selector de la nueva pantalla
    catalogo = [e for e in sirp.load_all(Ejercicio) if getattr(e, 'activo', True)]
    return render_template('rutinas_nueva.html', catalogo=catalogo)

@rutinas_bp.route('/entrenar/<oid_rutina>')
@login_required
def entrenar(oid_rutina):
    from modulo_ejercicios import Ejercicio
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    
    ejercicios_actuales = []
    for e_oid in rutina.lista_ejercicios_oids:
        ej = next((e for e in sirp.load_all(Ejercicio) if str(e.__oid__) == e_oid), None)
        if ej: ejercicios_actuales.append({'oid': e_oid, 'nombre': ej.nombre})

    catalogo = [e for e in sirp.load_all(Ejercicio) if getattr(e, 'activo', True)]
    return render_template('rutinas_entrenar.html', rutina=rutina, ejercicios=ejercicios_actuales, catalogo=catalogo)

@rutinas_bp.route('/finalizar/<oid_rutina>', methods=['POST'])
@login_required
def finalizar(oid_rutina):
    from modulo_registros import SesionEntrenamiento
    from modulo_ejercicios import Ejercicio
    
    rutina_original = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    
    ejercicios_finales_oids = []
    datos_sesion = []
    
    # Procesamos todos los pesos enviados para saber qué se ha entrenado
    for key in request.form.keys():
        if key.startswith('peso_'):
            e_oid = key.replace('peso_', '').replace('[]', '')
            pesos = request.form.getlist(f'peso_{e_oid}[]')
            reps = request.form.getlist(f'reps_{e_oid}[]')
            
            series = []
            for p, r in zip(pesos, reps):
                if p.strip() and r.strip():
                    series.append({'peso': float(p), 'reps': int(r)})
            
            if series:
                ej = next((e for e in sirp.load_all(Ejercicio) if str(e.__oid__) == e_oid), None)
                datos_sesion.append({'nombre': ej.nombre if ej else "Ej. Borrado", 'series': series})
                ejercicios_finales_oids.append(e_oid)

    if not datos_sesion:
        flash('Entrenamiento descartado (vacío).')
        return redirect(url_for('rutinas.index'))

    # Guardamos la sesión en el historial/feed
    nueva_s = SesionEntrenamiento(current_user.get_id(), rutina_original.nombre, request.form.get('duracion'), datos_sesion)
    sirp.save(nueva_s)

    # DETECCIÓN DE CAMBIOS: ¿Son los ejercicios entrenados distintos a los de la rutina?
    if set(ejercicios_finales_oids) != set(rutina_original.lista_ejercicios_oids):
        # Guardamos temporalmente los nuevos OIDs en la sesión de Flask para la confirmación
        session['temp_update_oids'] = ejercicios_finales_oids
        return redirect(url_for('rutinas.confirmar_cambios', oid_rutina=oid_rutina))

    flash('¡Entrenamiento finalizado!')
    return redirect(url_for('ejercicios.index'))

@rutinas_bp.route('/confirmar_cambios/<oid_rutina>')
@login_required
def confirmar_cambios(oid_rutina):
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    return render_template('rutinas_confirmar_cambios.html', rutina=rutina)

@rutinas_bp.route('/aplicar_cambios/<oid_rutina>', methods=['POST'])
@login_required
def aplicar_cambios(oid_rutina):
    decision = request.form.get('decision')
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    
    if decision == 'si' and 'temp_update_oids' in session:
        rutina.lista_ejercicios_oids = session['temp_update_oids']
        sirp.save(rutina)
        flash('Rutina actualizada con los nuevos ejercicios.')
    
    session.pop('temp_update_oids', None)
    return redirect(url_for('ejercicios.index'))

@rutinas_bp.route('/borrar/<oid_rutina>', methods=['POST'])
@login_required
def borrar(oid_rutina):
    for r in sirp.load_all(Rutina):
        if str(r.__oid__) == oid_rutina:
            sirp.delete(r.__oid__)
            flash('Rutina eliminada correctamente.')
            break
    return redirect(url_for('rutinas.index'))

@rutinas_bp.route('/editar/<oid_rutina>')
@login_required
def editar(oid_rutina):
    from modulo_ejercicios import Ejercicio
    
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    if not rutina:
        flash("Error: Rutina no encontrada")
        return redirect(url_for('rutinas.index'))
    
    # Cargamos los objetos ejercicio actuales en el orden guardado
    ejercicios_actuales = []
    for e_oid in rutina.lista_ejercicios_oids:
        ej = next((e for e in sirp.load_all(Ejercicio) if str(e.__oid__) == e_oid), None)
        if ej:
            ejercicios_actuales.append(ej)

    # Catálogo para añadir nuevos
    catalogo = [e for e in sirp.load_all(Ejercicio) if getattr(e, 'activo', True)]
    
    return render_template('rutinas_editar.html', rutina=rutina, ejercicios=ejercicios_actuales, catalogo=catalogo)

@rutinas_bp.route('/actualizar/<oid_rutina>', methods=['POST'])
@login_required
def actualizar(oid_rutina):
    rutina = next((r for r in sirp.load_all(Rutina) if str(r.__oid__) == oid_rutina), None)
    
    if rutina:
        rutina.nombre = request.form.get('nombre')
        # Los ejercicios llegan en el orden en que aparecen en el formulario HTML
        rutina.lista_ejercicios_oids = request.form.getlist('ejercicios_seleccionados')
        sirp.save(rutina)
        flash('Rutina actualizada correctamente.')
    
    return redirect(url_for('rutinas.index'))