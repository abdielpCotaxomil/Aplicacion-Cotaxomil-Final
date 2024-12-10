import os
import subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import QThread

# Función para buscar la aplicación en diferentes rutas
def encontrar_aplicacion(nombre_aplicacion):
    # Directorios comunes donde podría estar la aplicación
    posibles_rutas = [
        os.path.join(os.path.expanduser("~"), "Desktop"),  # Escritorio
        os.path.join(os.path.expanduser("~"), "Escritorio"),  # Escritorio en español
        "C:\\Program Files",  # Programas instalados
        "C:\\Program Files (x86)",  # Programas instalados (64 bits)
        "C:\\",  # Unidad C raíz
    ]
    
    # Buscar en cada ruta
    for ruta_base in posibles_rutas:
        ruta_app = os.path.join(ruta_base, nombre_aplicacion)
        if os.path.exists(ruta_app):
            return ruta_app  # Retornar la ruta si se encuentra

    return None  # Si no se encuentra en ninguna ubicación

# Clase que ejecuta el programa agregar.application o .exe en un hilo separado
class EjecutarAgregarThread(QThread):
    def run(self):
        # Buscar la aplicación en múltiples rutas posibles
        app_path = encontrar_aplicacion("Agregar.application")  # O "agregar.exe" si es un ejecutable

        if app_path is None:
            print("No se pudo encontrar la aplicación en las rutas predefinidas.")
            return

        try:
            if app_path.endswith(".application"):
                # Ejecutar el archivo .application utilizando rundll32
                subprocess.run(["rundll32", "dfshim.dll,ShOpenVerbApplication", app_path], check=True)
            else:
                # Ejecutar directamente si es un archivo .exe
                subprocess.run([app_path], check=True)
            print("Se ha ejecutado el programa agregar correctamente.")
        except subprocess.CalledProcessError:
            print("Ocurrió un error al ejecutar el programa agregar.")

class AddHuellaWindow(QWidget):
    def __init__(self):
        super(AddHuellaWindow, self).__init__()
        self.initUI()

        # Llamar directamente a la función para ejecutar la aplicación al iniciar la ventana
        self.agregar_huella()

    def initUI(self):
        self.setWindowTitle('Agregar Huella')
        self.setGeometry(100, 100, 400, 300)

        # Crear el layout de la ventana
        layout = QVBoxLayout()

        # Botón para iniciar la acción de agregar (ya no es necesario en este caso)
        agregar_btn = QPushButton('Agregar Huella', self)
        agregar_btn.clicked.connect(self.agregar_huella)
        layout.addWidget(agregar_btn)

        # Establecer el layout
        self.setLayout(layout)

    def agregar_huella(self):
        # Iniciar el hilo para ejecutar agregar.application o .exe
        self.agregar_thread = EjecutarAgregarThread()
        self.agregar_thread.start()

        # Mostrar un mensaje confirmando la acción
        QMessageBox.information(self, 'Proceso en curso', 'El programa agregar se está ejecutando.')
