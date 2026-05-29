from flask import Flask, redirect, url_for
from flask_login import LoginManager
import sirope
from auth import auth_bp, User 
# Importamos la clase Ejercicio directamente desde donde esté definida
from modulo_ejercicios import ejercicios_bp, Ejercicio 

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura_para_el_gimnasio" 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login" 

sirp = sirope.Sirope()

# --- FUNCIÓN DE INICIALIZACIÓN (Integrada en app.py) ---
def inicializar_catalogo():
    # 1. Cargamos todos los ejercicios usando load_all
    todos_ejercicios = list(sirp.load_all(Ejercicio))
    
    # 2. Filtramos en memoria aquellos que tienen es_defecto == True
    ejercicios_base = [e for e in todos_ejercicios if getattr(e, 'es_defecto', False)]
    
    # 3. Si no hay ninguno, los creamos
    if len(ejercicios_base) == 0:
        print("Cargando ejercicios base...")
        base = [
            Ejercicio(nombre="Press de Banca", grupo_muscular="Pecho", es_defecto=True),
            Ejercicio(nombre="Sentadilla", grupo_muscular="Pierna", es_defecto=True),
            Ejercicio(nombre="Peso Muerto", grupo_muscular="Espalda", es_defecto=True),
            Ejercicio(nombre="Press Militar", grupo_muscular="Hombro", es_defecto=True),
            Ejercicio(nombre="Dominadas", grupo_muscular="Espalda", es_defecto=True)
        ]
        for e in base:
            sirp.save(e)
        print("Catálogo base inicializado correctamente.")
    else:
        print("El catálogo base ya existe.")

# Ejecutamos la carga al arrancar el contexto de la app
with app.app_context():
    inicializar_catalogo()

# --- REGISTRO DE MÓDULOS ---
app.register_blueprint(auth_bp)
app.register_blueprint(ejercicios_bp)

from modulo_rutinas import rutinas_bp
app.register_blueprint(rutinas_bp)

from modulo_registros import registros_bp
app.register_blueprint(registros_bp)

@login_manager.user_loader
def load_user(username):
    return User.find(sirp, username)

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)