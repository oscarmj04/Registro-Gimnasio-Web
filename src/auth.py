from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sirope

auth_bp = Blueprint('auth', __name__)
sirp = sirope.Sirope()

# Entidad Usuario con campos para seguir a otros usuarios y gestionar solicitudes de seguimiento
class User(UserMixin):
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
        self.siguiendo = []               # Lista de usernames a los que sigue
        self.solicitudes_pendientes = []   # Lista de usernames que le han mandado solicitud

    def get_id(self):
        return self.username

    @staticmethod
    def find(sirp_instance, username):
        usuarios = list(sirp_instance.load_all(User))
        for u in usuarios:
            if u.username == username:
                return u
        return None

# NUEVAS RUTAS SOCIALES 
@auth_bp.route('/buscar_usuarios', methods=['GET', 'POST'])
@login_required
def buscar_usuarios():
    resultados = []
    busqueda = request.form.get('busqueda', '').strip()
    
    if busqueda:
        # Buscamos usuarios que coincidan con el nombre (excluyéndote a ti mismo)
        for u in sirp.load_all(User):
            if busqueda.lower() in u.username.lower() and u.username != current_user.username:
                resultados.append(u)
                
    return render_template('social_buscar.html', resultados=resultados, busqueda=busqueda)

@auth_bp.route('/mandar_solicitud/<username_destino>', methods=['POST'])
@login_required
def mandar_solicitud(username_destino):
    destino = User.find(sirp, username_destino)
    if destino:
        # Aseguramos que las listas existan por retrocompatibilidad en Redis
        if not hasattr(destino, 'solicitudes_pendientes'): destino.solicitudes_pendientes = []
        if not hasattr(current_user, 'siguiendo'): current_user.siguiendo = []
        
        if current_user.username not in destino.solicitudes_pendientes and username_destino not in current_user.siguiendo:
            destino.solicitudes_pendientes.append(current_user.username)
            sirp.save(destino)
            flash(f'Solicitud de seguimiento enviada a {username_destino}.')
        else:
            flash('Ya hay una solicitud pendiente o ya le sigues.')
    return redirect(url_for('auth.buscar_usuarios'))

@auth_bp.route('/gestionar_solicitudes')
@login_required
def gestionar_solicitudes():
    if not hasattr(current_user, 'solicitudes_pendientes'): current_user.solicitudes_pendientes = []
    return render_template('social_solicitudes.html', solicitudes=current_user.solicitudes_pendientes)

@auth_bp.route('/responder_solicitud/<username_origen>/<accion>', methods=['POST'])
@login_required
def responder_solicitud(username_origen, accion):
    if username_origen in current_user.solicitudes_pendientes:
        current_user.solicitudes_pendientes.remove(username_origen)
        
        if accion == 'aceptar':
            origen = User.find(sirp, username_origen)
            if origen:
                if not hasattr(origen, 'siguiendo'): origen.siguiendo = []
                if current_user.username not in origen.siguiendo:
                    origen.siguiendo.append(current_user.username)
                
                # Para que sea bidireccional (conectados mutuamente como pides), nos seguimos ambos:
                if not hasattr(current_user, 'siguiendo'): current_user.siguiendo = []
                if username_origen not in current_user.siguiendo:
                    current_user.siguiendo.append(username_origen)
                    
                sirp.save(origen)
            flash(f'¡Ahora estás conectado con {username_origen}!')
        else:
            flash('Solicitud rechazada.')
            
        sirp.save(current_user)
    return redirect(url_for('auth.gestionar_solicitudes'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.find(sirp, username)
        
        # Validamos usuario y comprobamos que la contraseña coincide con el hash
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('auth.dashboard')) 
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.find(sirp, username):
            flash('Ese nombre de usuario ya está en uso.', 'error')
        else:
            # Guardamos el usuario con la contraseña cifrada
            nuevo_usuario = User(username, generate_password_hash(password))
            sirp.save(nuevo_usuario)
            flash('Registro completado. Ya puedes iniciar sesión.')
            return redirect(url_for('auth.login'))
            
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    # Renderizamos la plantilla pasando el nombre del usuario actual
    return render_template('dashboard.html', username=current_user.username)