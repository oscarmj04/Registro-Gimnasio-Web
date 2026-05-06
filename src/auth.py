from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sirope

auth_bp = Blueprint('auth', __name__)
sirp = sirope.Sirope()

# Entidad Usuario (Requerida para Flask-Login)
class User(UserMixin):
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash

    def get_id(self):
        return self.username

    @staticmethod
    def find(sirp_instance, username):
        # Buscamos al usuario iterando sobre todos los guardados en REDIS
        usuarios = list(sirp_instance.load_all(User))
        for u in usuarios:
            if u.username == username:
                return u
        return None

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
            flash('Usuario o contraseña incorrectos.')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.find(sirp, username):
            flash('Ese nombre de usuario ya está en uso.')
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