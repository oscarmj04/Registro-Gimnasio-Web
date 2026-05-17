from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import sirope

registros_bp = Blueprint('registros', __name__, url_prefix='/registros')
sirp = sirope.Sirope()

class SesionEntrenamiento:
    def __init__(self, usuario_oid, nombre_rutina, duracion, ejercicios_data):
        self.usuario_oid = str(usuario_oid)  # Guardará siempre el username plano (ej: "oscar")
        self.nombre_rutina = nombre_rutina
        self.duracion = duracion
        self.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.ejercicios_data = ejercicios_data
        self.fuegos = []       
        self.comentarios = []  

@registros_bp.route('/')
@login_required
def index():
    todas = list(sirp.load_all(SesionEntrenamiento))
    
    # ARREGLO DEL FILTRO INDIVIDUAL: Compara directamente contra tu nombre de usuario actual
    mis_sesiones = [s for s in todas if str(s.usuario_oid) == str(current_user.username)]
    
    # Ordenamos de más reciente a más antiguo
    mis_sesiones.sort(key=lambda x: datetime.strptime(x.fecha, "%d/%m/%Y %H:%M"), reverse=True)
    return render_template('registros_index.html', sesiones=mis_sesiones)

@registros_bp.route('/feed')
@login_required
def feed():
    mis_seguidos = getattr(current_user, 'siguiendo', [])
    todas_las_sesiones = list(sirp.load_all(SesionEntrenamiento))
    
    # ARREGLO DEL FEED: Muestra tus entrenos (por username) y los de las cuentas conectadas
    sesiones_visibles = [
        s for s in todas_las_sesiones 
        if str(s.usuario_oid) == str(current_user.username) or str(s.usuario_oid) in mis_seguidos
    ]
    
    sesiones_visibles.sort(key=lambda x: datetime.strptime(x.fecha, "%d/%m/%Y %H:%M"), reverse=True)
    return render_template('feed_index.html', entrenamientos=sesiones_visibles)

@registros_bp.route('/fuego/<oid_sesion>', methods=['POST'])
@login_required
def fuego(oid_sesion):
    sesion = next((s for s in sirp.load_all(SesionEntrenamiento) if str(s.__oid__) == oid_sesion), None)
    if sesion:
        if not hasattr(sesion, 'fuegos'): sesion.fuegos = []
        if current_user.username in sesion.fuegos:
            sesion.fuegos.remove(current_user.username)
        else:
            sesion.fuegos.append(current_user.username)
        sirp.save(sesion)
    return redirect(url_for('registros.feed'))

@registros_bp.route('/comentar/<oid_sesion>', methods=['POST'])
@login_required
def comentar(oid_sesion):
    texto = request.form.get('comentario', '').strip()
    if texto:
        sesion = next((s for s in sirp.load_all(SesionEntrenamiento) if str(s.__oid__) == oid_sesion), None)
        if sesion:
            if not hasattr(sesion, 'comentarios'): sesion.comentarios = []
            sesion.comentarios.append({
                'usuario': current_user.username,
                'texto': texto
            })
            sirp.save(sesion)
            flash('Comentario añadido.')
    return redirect(url_for('registros.feed'))

@registros_bp.route('/detalle/<oid_sesion>')
@login_required
def detalle(oid_sesion):
    sesion = next((s for s in sirp.load_all(SesionEntrenamiento) if str(s.__oid__) == oid_sesion), None)
    if not sesion:
        flash('Entrenamiento no encontrado.', 'error')
        return redirect(url_for('registros.index'))
    return render_template('historial_detalle.html', sesion=sesion)

@registros_bp.route('/borrar_sesion/<oid_sesion>', methods=['POST'])
@login_required
def borrar_sesion(oid_sesion):
    for s in sirp.load_all(SesionEntrenamiento):
        if str(s.__oid__) == oid_sesion and str(s.usuario_oid) == str(current_user.username):
            sirp.delete(s.__oid__)
            flash('Entrenamiento eliminado del historial.')
            break
    return redirect(url_for('registros.index'))