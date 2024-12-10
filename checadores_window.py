import os
import subprocess
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QInputDialog, QMessageBox
from forms import JornadaEntradaForm, JornadaSalidaForm, InfoForm

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

# Clase que ejecuta el archivo verificar.application en un hilo separado
class EjecutarVerificarThread(QThread):
    def run(self):
        # Buscar la aplicación verificar en múltiples rutas posibles
        app_path = encontrar_aplicacion("verificar.application")  # O "verificar.exe" si es un ejecutable

        if app_path is None:
            print("No se pudo encontrar la aplicación verificar en las rutas predefinidas.")
            return

        try:
            if app_path.endswith(".application"):
                # Ejecutar el archivo .application utilizando rundll32
                subprocess.run(["rundll32", "dfshim.dll,ShOpenVerbApplication", app_path], check=True)
            else:
                # Ejecutar directamente si es un archivo .exe
                subprocess.run([app_path], check=True)
            print("Se ha ejecutado verificar.application correctamente.")
        except subprocess.CalledProcessError:
            print("Ocurrió un error al ejecutar verificar.application.")

class ChecadoresWindow(QWidget):
    def __init__(self, db):
        super(ChecadoresWindow, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Checadores')
        self.setGeometry(100, 100, 400, 300)

        # Verificar si ya existe un layout para evitar asignar uno nuevo
        if self.layout() is None:
            layout = QVBoxLayout()

            iniciar_jornada_btn = QPushButton('Iniciar Jornada', self)
            iniciar_jornada_btn.clicked.connect(self.iniciar_jornada)
            iniciar_jornada_btn.setStyleSheet("background-color: rgb(112, 163, 140);")   
            layout.addWidget(iniciar_jornada_btn)

            terminar_jornada_btn = QPushButton('Terminar Jornada', self)
            terminar_jornada_btn.clicked.connect(self.terminar_jornada)
            terminar_jornada_btn.setStyleSheet("background-color: rgb(112, 163, 140);")
            layout.addWidget(terminar_jornada_btn)

            ver_info_btn = QPushButton('Ver Información', self)
            ver_info_btn.clicked.connect(self.ver_informacion)
            ver_info_btn.setStyleSheet("background-color: rgb(112, 163, 140);")
            layout.addWidget(ver_info_btn)

            self.setLayout(layout)

    def iniciar_jornada(self):
        self.jornadaEntradaForm = JornadaEntradaForm(self.db)
        self.jornadaEntradaForm.show()

    def terminar_jornada(self):
        # Iniciar el hilo para ejecutar verificar.application
        self.verificar_thread = EjecutarVerificarThread()
        self.verificar_thread.start()

        # Mostrar el diálogo de folio al mismo tiempo
        folio, ok = QInputDialog.getInt(self, 'Terminar Jornada', 'Ingrese el folio:')
        if ok:
            self.jornadaSalidaForm = JornadaSalidaForm(self.db, folio)
            self.jornadaSalidaForm.show()

    def ver_informacion(self):
        self.infoForm = InfoForm(self.db)
        self.infoForm.show()
