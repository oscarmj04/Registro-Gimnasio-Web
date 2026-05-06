from flask import Blueprint, render_template, request, redirect, url_for, flash
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
    
    from modulo_ejercicios import Ejercicio
    todos_ejercicios = {str(e.__oid__): e.nombre for e in sirp.load_all(Ejercicio)}
    
    return render_template('rutinas_index.html', rutinas=mis_rutinas, ejercicios_dict=todos_ejercicios)

@rutinas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    from modulo_ejercicios import Ejercicio
    lista_ejercicios = list(sirp.load_all(Ejercicio))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        ejercicios_seleccionados = request.form.getlist('ejercicios') 
        
        nueva_rutina = Rutina(nombre, current_user.get_id(), ejercicios_seleccionados)
        sirp.save(nueva_rutina)
        
        flash('Rutina creada con éxito.')
        return redirect(url_for('rutinas.index'))
        
    return render_template('rutinas_nueva.html', ejercicios=lista_ejercicios)

@rutinas_bp.route('/borrar/<oid_rutina>', methods=['POST'])
@login_required
def borrar(oid_rutina):
    # Buscamos la rutina exacta comparando textos
    for r in sirp.load_all(Rutina):
        if str(r.__oid__) == oid_rutina:
            # Una vez encontrada, usamos su OID real e interno para borrarla
            sirp.delete(r.__oid__)
            flash('Rutina eliminada correctamente.')
            break
            
    return redirect(url_for('rutinas.index'))

@rutinas_bp.route('/entrenar/<oid_rutina>')
@login_required
def entrenar(oid_rutina):
    # 1. En lugar de construir el OID a mano, cargamos TODAS las rutinas 
    # y buscamos la que coincida en su representación de string.
    # Es un poco menos eficiente, pero INFALIBLE contra el NameError.
    
    rutina_encontrada = None
    for r in sirp.load_all(Rutina):
        if str(r.__oid__) == oid_rutina:
            rutina_encontrada = r
            break
            
    if not rutina_encontrada:
        flash("Error: No se pudo encontrar la rutina.")
        return redirect(url_for('rutinas.index'))
    
    from modulo_ejercicios import Ejercicio
    ejercicios_rutina = []
    
    for e_oid in rutina_encontrada.lista_ejercicios_oids:
        # Aquí hacemos lo mismo: buscamos el ejercicio por su OID string
        ej_encontrado = None
        for e in sirp.load_all(Ejercicio):
            if str(e.__oid__) == e_oid:
                ej_encontrado = e
                break
        
        if ej_encontrado:
            ejercicios_rutina.append({'oid': e_oid, 'nombre': ej_encontrado.nombre})
            
    return render_template('rutinas_entrenar.html', rutina=rutina_encontrada, ejercicios=ejercicios_rutina)