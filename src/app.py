from flask import Flask, redirect, url_for
from flask_login import LoginManager
import sirope
from auth import auth_bp, User 

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura_para_el_gimnasio" 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login" 

sirp = sirope.Sirope()

@login_manager.user_loader
def load_user(username):
    return User.find(sirp, username)

# --- REGISTRO DE MÓDULOS (DISEÑO MODULAR) ---
app.register_blueprint(auth_bp)

from modulo_ejercicios import ejercicios_bp
app.register_blueprint(ejercicios_bp)

from modulo_rutinas import rutinas_bp
app.register_blueprint(rutinas_bp)

from modulo_registros import registros_bp
app.register_blueprint(registros_bp)
# --------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)