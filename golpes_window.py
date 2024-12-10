from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QDialog, QFormLayout, QComboBox, QLabel, QLineEdit, QFileDialog, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage
from PyQt5.QtCore import Qt, QDateTime, QPoint, QBuffer
from PyQt5.QtMultimedia import QCamera, QCameraInfo, QCameraImageCapture
from PyQt5.QtMultimediaWidgets import QCameraViewfinder
import os
import psycopg2
import sys

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class GolpesWindow(QMainWindow):
    def __init__(self, db):
        super(GolpesWindow, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Golpes')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.registrar_btn = QPushButton('Registrar Golpe', self)
        self.registrar_btn.clicked.connect(self.registrar_golpes)
        self.registrar_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
        layout.addWidget(self.registrar_btn)

        self.borrar_btn = QPushButton('Borrar Golpe', self)
        self.borrar_btn.clicked.connect(self.borrar_golpes)
        self.borrar_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
        layout.addWidget(self.borrar_btn)

        self.ver_btn = QPushButton('Ver Golpes', self)
        self.ver_btn.clicked.connect(self.ver_golpes)
        self.ver_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
        layout.addWidget(self.ver_btn)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def registrar_golpes(self):
        dialog = RegistrarGolpesForm(self.db, self)
        dialog.exec_()

    def borrar_golpes(self):
        dialog = BorrarGolpesForm(self.db, self)
        dialog.exec_()

    def ver_golpes(self):
        dialog = VerGolpesForm(self.db, self)
        dialog.exec_()

class CameraDialog(QDialog):
    def __init__(self, parent=None):
        super(CameraDialog, self).__init__(parent)
        self.setWindowTitle('Tomar Foto')
        self.camera = None
        self.image_capture = None
        self.image_data = None
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        self.viewfinder = QCameraViewfinder(self)
        layout.addWidget(self.viewfinder)
        
        self.capture_button = QPushButton('Capturar', self)
        self.capture_button.clicked.connect(self.capture_image)
        self.capture_button.setStyleSheet("background-color: rgb(197, 73, 73 );")
        layout.addWidget(self.capture_button)
        
        self.setLayout(layout)
        
        available_cameras = QCameraInfo.availableCameras()
        if not available_cameras:
            QMessageBox.warning(self, "No Camera", "No se encontró una cámara en este dispositivo.")
            self.reject()
            return
        
        self.camera = QCamera(available_cameras[0])
        self.camera.setViewfinder(self.viewfinder)
        
        self.image_capture = QCameraImageCapture(self.camera)
        self.image_capture.imageCaptured.connect(self.image_captured)
        
        self.camera.start()
    
    def capture_image(self):
        self.image_capture.capture()
    
    def image_captured(self, id, image):
        self.image_data = image
        self.camera.stop()
        self.accept()
    
    def get_image_data(self):
        return self.image_data

class RegistrarGolpesForm(QDialog):
    def __init__(self, db, parent=None):
        super(RegistrarGolpesForm, self).__init__(parent)
        self.setWindowTitle('Registrar Golpe')
        self.db = db
        self.golpe_positions = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.eco_combo = QComboBox(self)
        self.populate_autobuses()
        form_layout.addRow('Económico:', self.eco_combo)

        self.chofer_combo = QComboBox(self)
        self.populate_choferes()
        form_layout.addRow('Chofer:', self.chofer_combo)

        self.fecha_hora = QLineEdit(self)
        self.fecha_hora.setText(QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss'))
        self.fecha_hora.setEnabled(False)
        form_layout.addRow('Fecha y Hora:', self.fecha_hora)

        self.detalle_combo = QComboBox(self)
        self.detalle_combo.addItems(['TALLADO', 'RAYADO', 'DESCARAPELADO', 'HUNDIDO', 'ESTRELLADO', 'ROTO', 'FLOJO', 'SUELTO', 'PINTADO','SINIESTRO'])
        form_layout.addRow('Detalle:', self.detalle_combo)

        self.foto_golpe = QLabel(self)
        self.set_default_image()
        form_layout.addRow('Foto Golpe:', self.foto_golpe)

        self.submit_btn = QPushButton('Registrar', self)
        self.submit_btn.clicked.connect(self.registrar_golpe)
        self.submit_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
        form_layout.addRow(self.submit_btn)

        self.undo_btn = QPushButton('Deshacer Último Golpe', self)
        self.undo_btn.clicked.connect(self.undo_golpe)
        self.undo_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
        form_layout.addRow(self.undo_btn)

        layout.addLayout(form_layout)
        self.setLayout(layout)
        self.eco_combo.currentIndexChanged.connect(self.update_image_by_bus_type)
        # Evento de clic para la etiqueta de la imagen
        self.foto_golpe.mousePressEvent = self.mark_golpe
       

    def populate_autobuses(self):
        query = "SELECT eco FROM Autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"
        self.db.execute_query(query)
        autobuses = self.db.fetch_all()
        for autobus in autobuses:
            self.eco_combo.addItem(str(autobus[0]), autobus[0])

    def populate_choferes(self):
        query = "SELECT id_chofer, nombre, apellido_paterno, apellido_materno FROM Empleado_Chofer WHERE estatus = 'ACTIVO' ORDER BY id_chofer ASC"
        self.db.execute_query(query)
        choferes = self.db.fetch_all()
        for chofer in choferes:
            nombre_completo = f"{chofer[1]} {chofer[2]} {chofer[3]}"
            self.chofer_combo.addItem(nombre_completo, chofer[0])

    def set_default_image(self):
        eco = self.eco_combo.currentData()
        
        query = "SELECT tipo FROM Autobus WHERE eco = %s"
        self.db.execute_query(query, (eco,))
        bus_type = self.db.fetch_all()[0][0]

        if bus_type == "ZAFIRO":
            image_path = resource_path("path_to_image/Final_Camion.png")
        elif bus_type == "TORETO":
            image_path = resource_path("path_to_image/Toreto.png")
        else:
            image_path = resource_path("path_to_image/default.png")

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen en {image_path}")
        self.foto_golpe.setPixmap(pixmap.scaled(1280, 720, Qt.KeepAspectRatio))

    def update_image_by_bus_type(self):
        # Obtener el eco seleccionado
        eco = self.eco_combo.currentData()

        # Consultar el tipo de autobús
        query = "SELECT tipo FROM Autobus WHERE eco = %s"
        self.db.execute_query(query, (eco,))
        bus_type = self.db.fetch_all()[0][0]  # Suponemos que siempre habrá un resultado

        # Cargar la imagen correspondiente según el tipo de autobús
        if bus_type == "ZAFIRO":
            image_path = resource_path("path_to_image/Final_Camion.png")
        elif bus_type == "TORETO":
            image_path = resource_path("path_to_image/Toreto.png")
        else:
            image_path = resource_path("path_to_image/default.png")  # Imagen por defecto si el tipo no es reconocido

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen en {image_path}")
        self.foto_golpe.setPixmap(pixmap.scaled(1280, 720, Qt.KeepAspectRatio))
    


    def registrar_golpe(self):
        eco = self.eco_combo.currentData()
        id_chofer = self.chofer_combo.currentData()
        fecha_hora = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
        estatus = 'ACTIVA'
        detalle = self.detalle_combo.currentText()

        # Abrir la cámara y capturar la foto para evidencia
        camera_dialog = CameraDialog(self)
        if camera_dialog.exec_() == QDialog.Accepted:
            image_data = camera_dialog.get_image_data()
            if image_data:
                # Convertir la imagen a bytes
                buffer = QBuffer()
                buffer.open(QBuffer.WriteOnly)
                image_data.save(buffer, 'PNG')
                evidencia = bytes(buffer.data())  # Convertir a 'bytes' estándar de Python
            else:
                QMessageBox.warning(self, 'Error', 'No se pudo capturar la imagen.')
                return
        else:
            QMessageBox.warning(self, 'Operación cancelada', 'Captura de imagen cancelada.')
            return

        query = """
        INSERT INTO historial_golpes (fecha, hora, eco, id_chofer, foto_golpe, estatus, x, y, detalle, evidencia)
        VALUES (CURRENT_DATE, CURRENT_TIME, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for pos in self.golpe_positions:
            params = (eco, id_chofer, None, estatus, pos.x(), pos.y(), detalle, evidencia)
            try:
                self.db.execute_query(query, params)
            except Exception as e:
                print(f"Error al registrar golpe: {e}")
                QMessageBox.critical(self, 'Error', f'Error al registrar golpe: {e}')
                return

        QMessageBox.information(self, 'Éxito', 'Golpe registrado exitosamente.')
        self.close()


    def load_image(self):
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        self.foto_golpe.pixmap().save(buffer, "PNG")
        return buffer.data()

    def mark_golpe(self, event):
        pos = event.pos()
        self.golpe_positions.append(pos)
        self.update_image()

    def undo_golpe(self):
        if self.golpe_positions:
            self.golpe_positions.pop()
            self.update_image()

    def update_image(self):
        eco = self.eco_combo.currentData()
        query = "SELECT tipo FROM Autobus WHERE eco = %s"
        self.db.execute_query(query, (eco,))
        bus_type = self.db.fetch_all()[0][0]

        if bus_type == "ZAFIRO":
            image_path = resource_path("path_to_image/Final_Camion.png")
        elif bus_type == "TORETO":
            image_path = resource_path("path_to_image/Toreto.png")
        else:
            image_path = resource_path("path_to_image/default.png")

        pixmap = QPixmap(image_path)
        painter = QPainter(pixmap)
        pen = QPen(Qt.red, 5)
        painter.setPen(pen)
        for pos in self.golpe_positions:
            painter.drawEllipse(pos, 30, 30)
        painter.end()
        self.foto_golpe.setPixmap(pixmap.scaled(1280, 720, Qt.KeepAspectRatio))

class VerGolpesForm(QDialog):
    def __init__(self, db, parent=None):
        super(VerGolpesForm, self).__init__(parent)
        self.setWindowTitle('Ver Golpes')
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        
        self.eco_combo = QComboBox(self)
        self.populate_autobuses()
        form_layout.addRow('Económico:', self.eco_combo)

        self.submit_btn = QPushButton('Ver Golpes', self)
        self.submit_btn.clicked.connect(self.ver_golpes)
        self.submit_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
        form_layout.addRow(self.submit_btn)

        self.foto_golpe = QLabel(self)
        form_layout.addRow('Esquema Golpes:', self.foto_golpe)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def populate_autobuses(self):
        query = "SELECT eco FROM Autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"

        self.db.execute_query(query)
        autobuses = self.db.fetch_all()
        for autobus in autobuses:
            self.eco_combo.addItem(str(autobus[0]), autobus[0])

    def ver_golpes(self):
        eco = self.eco_combo.currentData()

        # Obtener el tipo de autobús y cargar la imagen correspondiente
        query = "SELECT tipo FROM Autobus WHERE eco = %s"
        self.db.execute_query(query, (eco,))
        bus_type = self.db.fetch_all()[0][0]

        # Cargar la imagen correspondiente según el tipo de autobús
        if bus_type == "ZAFIRO":
            image_path = resource_path("path_to_image/Final_Camion.png")
        elif bus_type == "TORETO":
            image_path = resource_path("path_to_image/Toreto.png")
        else:
            image_path = resource_path("path_to_image/default.png")

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen en {image_path}")

        # Continuar con la lógica de mostrar los golpes
        self.foto_golpe.setPixmap(pixmap.scaled(1280, 720, Qt.KeepAspectRatio))

        # Extraer coordenadas de los golpes
        query_golpes = "SELECT x, y, detalle FROM historial_golpes WHERE eco = %s AND estatus = 'ACTIVA'"
        self.db.execute_query(query_golpes, (eco,))
        golpes = self.db.fetch_all()

        painter = QPainter(pixmap)
        pen = QPen(Qt.red, 5)
        painter.setPen(pen)
        for golpe in golpes:
            if golpe[0] is not None and golpe[1] is not None:
                painter.drawEllipse(QPoint(golpe[0], golpe[1]), 10, 10)
        painter.end()

        self.foto_golpe.setPixmap(pixmap.scaled(1280, 720, Qt.KeepAspectRatio))

        # Agregar evento de clic para mostrar detalle del golpe
        self.foto_golpe.mousePressEvent = lambda event: self.mostrar_detalle_golpe(event, golpes)

    def mostrar_detalle_golpe(self, event, golpes):
        pos = event.pos()
        for golpe in golpes:
            if abs(golpe[0] - pos.x()) < 10 and abs(golpe[1] - pos.y()) < 10:
                query = """
                SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, h.fecha, h.detalle, h.evidencia
                FROM historial_golpes h
                JOIN Empleado_Chofer e ON h.id_chofer = e.id_chofer
                WHERE h.eco = %s AND h.x = %s AND h.y = %s 
                """
                self.db.execute_query(query, (self.eco_combo.currentData(), golpe[0], golpe[1]))
                result = self.db.fetch_all()[0]
                chofer_id = result[0]
                nombre_completo = f"{result[1]} {result[2]} {result[3]}"
                fecha = result[4]
                detalle = result[5]
                evidencia = result[6]  # Aquí obtenemos los datos de la imagen

                # Crear la ventana emergente con los detalles del golpe
                detalle_dialog = QDialog(self)
                detalle_dialog.setWindowTitle("Detalle del Golpe")

                layout = QVBoxLayout()
                form_layout = QFormLayout()
                form_layout.addRow("ID Chofer:", QLabel(str(chofer_id)))
                form_layout.addRow("Nombre:", QLabel(nombre_completo))
                form_layout.addRow("Fecha:", QLabel(str(fecha)))
                form_layout.addRow("Detalle:", QLabel(detalle))

                # Crear la miniatura de la imagen
                if evidencia:
                    pixmap = QPixmap()
                    pixmap.loadFromData(evidencia)  # Cargar la imagen desde los datos en binario
                    pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio)  # Escalar la imagen a tamaño pequeño (miniatura)

                    imagen_label = QLabel()
                    imagen_label.setPixmap(pixmap)
                    imagen_label.mousePressEvent = lambda event, evidencia=evidencia: self.mostrar_imagen_completa(evidencia)

                    form_layout.addRow("Imagen del golpe:", imagen_label)

                layout.addLayout(form_layout)
                detalle_dialog.setLayout(layout)
                detalle_dialog.exec_()

    # Función para mostrar la imagen en tamaño completo
    def mostrar_imagen_completa(self, evidencia):
        imagen_dialog = QDialog(self)
        imagen_dialog.setWindowTitle("Imagen Completa del Golpe")

        layout = QVBoxLayout()

        pixmap = QPixmap()
        pixmap.loadFromData(evidencia)  # Cargar la imagen desde los datos en binario
        imagen_label = QLabel()
        imagen_label.setPixmap(pixmap.scaled(800, 800, Qt.KeepAspectRatio))  # Mostrar la imagen en un tamaño más grande

        layout.addWidget(imagen_label)
        imagen_dialog.setLayout(layout)
        imagen_dialog.exec_()

class BorrarGolpesForm(QDialog):
    def __init__(self, db, parent=None):
        super(BorrarGolpesForm, self).__init__(parent)
        self.setWindowTitle('Borrar Golpes')
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.eco_combo = QComboBox(self)
        self.populate_autobuses()
        form_layout.addRow('Económico:', self.eco_combo)

        self.submit_btn = QPushButton('Cargar Esquema', self)
        self.submit_btn.clicked.connect(self.cargar_esquema)
        self.submit_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
        form_layout.addRow(self.submit_btn)

        self.foto_golpe = QLabel(self)
        form_layout.addRow('Esquema Golpes:', self.foto_golpe)

        layout.addLayout(form_layout)
        self.setLayout(layout)
    
        self.eco_combo.currentIndexChanged.connect(self.update_image_by_bus_type)

    def update_image_by_bus_type(self):
        eco = self.eco_combo.currentData()
        query = "SELECT tipo FROM Autobus WHERE eco = %s"
        self.db.execute_query(query, (eco,))
        bus_type = self.db.fetch_all()[0][0]

        if bus_type == "ZAFIRO":
            image_path = resource_path("path_to_image/Final_Camion.png")
        elif bus_type == "TORETO":
            image_path = resource_path("path_to_image/Toreto.png")
        else:
            image_path = resource_path("path_to_image/default.png")

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen en {image_path}")
        self.foto_golpe.setPixmap(pixmap.scaled(1280, 720, Qt.KeepAspectRatio))

    def populate_autobuses(self):
        query = "SELECT eco FROM Autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"
        self.db.execute_query(query)
        autobuses = self.db.fetch_all()
        for autobus in autobuses:
            self.eco_combo.addItem(str(autobus[0]), autobus[0])

    def cargar_esquema(self):
        eco = self.eco_combo.currentData()

        # Obtener el tipo de autobús y cargar la imagen correspondiente
        query = "SELECT tipo FROM Autobus WHERE eco = %s"
        self.db.execute_query(query, (eco,))
        bus_type = self.db.fetch_all()[0][0]

        # Cargar la imagen correspondiente según el tipo de autobús
        if bus_type == "ZAFIRO":
            image_path = resource_path("path_to_image/Final_Camion.png")
        elif bus_type == "TORETO":
            image_path = resource_path("path_to_image/Toreto.png")
        else:
            image_path = resource_path("path_to_image/default.png")

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen en {image_path}")

        # Extraer coordenadas de los golpes
        query_golpes = "SELECT x, y, detalle FROM historial_golpes WHERE eco = %s AND estatus = 'ACTIVA'"
        self.db.execute_query(query_golpes, (eco,))
        self.golpes = self.db.fetch_all()

        # Pintar los golpes sobre la imagen
        painter = QPainter(pixmap)
        pen = QPen(Qt.red, 5)
        painter.setPen(pen)
        for golpe in self.golpes:
            if golpe[0] is not None and golpe[1] is not None:
                painter.drawEllipse(QPoint(golpe[0], golpe[1]), 10, 10)
        painter.end()

        # Mostrar la imagen con los golpes marcados
        self.foto_golpe.setPixmap(pixmap.scaled(1280, 720, Qt.KeepAspectRatio))

        # Agregar evento de clic para mostrar detalle del golpe
        self.foto_golpe.mousePressEvent = self.mostrar_detalle_golpe


    def mostrar_detalle_golpe(self, event):
        pos = event.pos()
        for golpe in self.golpes:
            if abs(golpe[0] - pos.x()) < 10 and abs(golpe[1] - pos.y()) < 10:
                query = """
                SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, h.fecha, h.detalle
                FROM historial_golpes h
                JOIN Empleado_Chofer e ON h.id_chofer = e.id_chofer
                WHERE h.eco = %s AND h.x = %s AND h.y = %s 
                """
                self.db.execute_query(query, (self.eco_combo.currentData(), golpe[0], golpe[1]))
                result = self.db.fetch_all()[0]
                chofer_id = result[0]
                nombre_completo = f"{result[1]} {result[2]} {result[3]}"
                fecha = result[4]
                detalle = result[5]

                detalle_dialog = QDialog(self)
                detalle_dialog.setWindowTitle("Detalle del Golpe")

                layout = QVBoxLayout()
                form_layout = QFormLayout()
                form_layout.addRow("ID Chofer:", QLabel(str(chofer_id)))
                form_layout.addRow("Nombre:", QLabel(nombre_completo))
                form_layout.addRow("Fecha:", QLabel(str(fecha)))
                form_layout.addRow("Detalle:", QLabel(detalle))

                layout.addLayout(form_layout)

                delete_btn = QPushButton('Borrar Golpe', detalle_dialog)
                delete_btn.clicked.connect(lambda: self.borrar_golpe(golpe[0], golpe[1], detalle_dialog))
                delete_btn.setStyleSheet("background-color: rgb(197, 73, 73 );")
                layout.addWidget(delete_btn)

                detalle_dialog.setLayout(layout)
                detalle_dialog.exec_()
                break  # Añadir un break para evitar múltiples diálogos

    def borrar_golpe(self, x, y, dialog):
        query = "UPDATE historial_golpes SET estatus = 'RESUELTO' WHERE eco = %s AND x = %s AND y = %s"
        params = (self.eco_combo.currentData(), x, y)
        try:
            self.db.execute_query(query, params)
            QMessageBox.information(self, 'Éxito', 'Golpe resuelto exitosamente.')
            dialog.accept()
            self.cargar_esquema()  # Recargar el esquema para reflejar los cambios
        except Exception as e:
            print(f"Error al borrar golpe: {e}")
            QMessageBox.critical(self, 'Error', f'Error al borrar golpe: {e}')

class Database:
    def __init__(self, host, database, user, password):
        self.conn = psycopg2.connect(host=host, database=database, user=user, password=password)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=None):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_all(self):
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()
