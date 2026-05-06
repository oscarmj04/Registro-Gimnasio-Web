# 🏋️‍♂️ Gym Tracker App

Este repositorio contiene la implementación del proyecto **Gym Tracker App**, una aplicación web para la gestión de entrenamientos.

## 🎯 Objetivo del Proyecto

Desarrollar una plataforma robusta que permita a los usuarios gestionar su catálogo de ejercicios, estructurar rutinas y registrar sus entrenamientos en tiempo real. La arquitectura se centra en la **integridad de los datos**, implementando mecanismos avanzados de borrado (suave y duro) utilizando Redis y el ORM Sirope.

## ✅ Funcionalidades Implementadas

- **Sistema de Autenticación**
  - Flujos seguros de registro, inicio y cierre de sesión.
  - Contraseñas encriptadas mediante hashes utilizando `Werkzeug`.

- **Gestión de Ejercicios y Rutinas**
  - **Catálogo Global:** Creación y almacenamiento persistente de ejercicios personalizados.
  - **Rutinas a Medida:** Agrupación de ejercicios del catálogo en rutinas definidas por el usuario.

- **Modo Entrenamiento en Vivo**
  - Interfaz interactiva con cronómetro integrado mediante JavaScript.
  - Registro en tiempo real de pesos y repeticiones durante la sesión activa.

- **Integridad de Datos y Borrados Seguros**
  - **Borrado Suave:** Archiva ejercicios del catálogo, ocultándolos de futuras rutinas pero conservando intacto el historial de levantamientos del usuario.
  - **Borrado Duro:** Elimina permanentemente los ejercicios y destruye en cascada todos los registros históricos asociados a los mismos.
  - **Borrado de Rutinas Independiente:** Elimina la agrupación de la rutina sin alterar el historial general de entrenamientos realizados.

## 🚀 Instalación y Ejecución

- **Requisitos Previos**
  - Python 3.12+ 
  - Servidor **Redis** en ejecución (local o WSL).

- **Configuración del Entorno**
  - Crear entorno: `python -m venv venv`
  - Activar (Windows): `.\venv\Scripts\activate`
  - Activar (Linux/WSL): `source venv/bin/activate`

- **Dependencias y Arranque**
  - Instalar librerías: `pip install flask flask-login werkzeug sirope redis`
  - Ejecutar: Navegar a la carpeta `src/` y lanzar el comando `flask run`.
  - Acceso: `http://127.0.0.1:5000`

## 📝 Notas

- Desarrollado con el framework **Flask** (Python) y renderizado con plantillas **Jinja2**.
- Persistencia de datos gestionada mediante **Redis** a través del ORM **Sirope**.
- La arquitectura mantiene una separación clara entre los modelos de la base de datos, las rutas de la aplicación y la interfaz de usuario.
