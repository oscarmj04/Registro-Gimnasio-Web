from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import login_required
import sirope

ejercicios_bp = Blueprint('ejercicios', __name__, url_prefix='/ejercicios')
sirp = sirope.Sirope()

class Ejercicio:
    def __init__(self, nombre, grupo_muscular, descripcion):
        self.nombre = nombre
        self.grupo_muscular = grupo_muscular
        self.descripcion = descripcion
        self.activo = True  # Novedad: Permite el "borrado suave"

@ejercicios_bp.route('/')
@login_required
def index():
    # Solo mostramos en el catálogo los que están "activos"
    lista_ejercicios = [e for e in sirp.load_all(Ejercicio) if getattr(e, 'activo', True)]
    return render_template('ejercicios_index.html', ejercicios=lista_ejercicios)

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
        return redirect(url_for('ejercicios.index'))
    return render_template('ejercicios_nuevo.html')

@ejercicios_bp.route('/borrar/<oid_ejercicio>/<tipo>', methods=['POST'])
@login_required
def borrar(oid_ejercicio, tipo):
    from modulo_rutinas import Rutina 
    from modulo_registros import Registro
    
    # 1. Sacar el ejercicio de todas las rutinas futuras
    for rutina in sirp.load_all(Rutina):
        oids_str = [str(oid) for oid in rutina.lista_ejercicios_oids]
        if str(oid_ejercicio) in oids_str:
            rutina.lista_ejercicios_oids = [oid for oid in rutina.lista_ejercicios_oids if str(oid) != str(oid_ejercicio)]
            sirp.save(rutina)
            
    # 2. Encontrar el objeto Ejercicio real para manipularlo o borrarlo
    ejercicio_encontrado = None
    for e in sirp.load_all(Ejercicio):
        if str(e.__oid__) == oid_ejercicio:
            ejercicio_encontrado = e
            break

    if tipo == 'suave':
        if ejercicio_encontrado:
            ejercicio_encontrado.activo = False
            sirp.save(ejercicio_encontrado) # Actualizamos el objeto real
            flash('Ejercicio archivado. Se ha quitado de las rutinas, pero el historial se mantiene.')
            
    elif tipo == 'duro':
        # Primero borramos su historial buscando los registros
        for reg in sirp.load_all(Registro):
            if str(reg.ejercicio_oid) == str(oid_ejercicio):
                sirp.delete(reg.__oid__) # Borramos con el OID real del registro
                
        # Luego destruimos el ejercicio usando su OID real
        if ejercicio_encontrado:
            sirp.delete(ejercicio_encontrado.__oid__)
            flash('Ejercicio destruido permanentemente (incluyendo historiales).')

    return redirect(url_for('ejercicios.index'))