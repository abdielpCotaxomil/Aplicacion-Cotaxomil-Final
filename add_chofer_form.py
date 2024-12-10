import os
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel,
    QDateEdit, QFileDialog, QMessageBox, QHBoxLayout, QComboBox, QDialog, QScrollArea, QProgressBar
)
from PyQt5.QtGui import QPixmap, QRegExpValidator, QImage
from PyQt5.QtCore import QDate, Qt, QRegExp, QBuffer, QThread, pyqtSignal
from add_huella import AddHuellaWindow
from PyQt5.QtMultimedia import QCamera, QCameraInfo, QCameraImageCapture
from PyQt5.QtMultimediaWidgets import QCameraViewfinder
from PyQt5.QtGui import QIntValidator

class CameraDialog(QDialog):
    def __init__(self, photo_type, parent=None):
        super(CameraDialog, self).__init__(parent)
        self.setWindowTitle("Capturar Foto")
        self.photo_type = photo_type
        self.image = None

        layout = QVBoxLayout()
        self.viewfinder = QCameraViewfinder(self)
        layout.addWidget(self.viewfinder)

        self.capture_button = QPushButton("Capturar", self)
        self.capture_button.clicked.connect(self.capture_image)
        layout.addWidget(self.capture_button)

        self.setLayout(layout)

        # Configurar la cámara
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
        self.camera.stop()
        self.image = image
        self.accept()

    def get_image(self):
        return self.image

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super(LoadingDialog, self).__init__(parent)
        self.setWindowTitle("Guardando")
        self.setModal(True)
        self.resize(300, 100)

        layout = QVBoxLayout()
        self.label = QLabel("Guardando datos, por favor espere...")
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #800080;  /* Color morado */
                width: 20px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

class SaveWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, db, data, parent=None):
        super(SaveWorker, self).__init__(parent)
        self.db = db
        self.data = data  # Datos necesarios para guardar

    def run(self):
        try:
            # Simular progreso
            total_steps = 5  # Número de pasos en el proceso de guardado
            for i in range(total_steps):
                time.sleep(0.5)  # Simular una operación que toma tiempo
                progress_percent = int((i + 1) * 100 / total_steps)
                self.progress.emit(progress_percent)

            # Realizar las operaciones de guardado
            id_chofer = self.data['id_chofer']
            nombre = self.data['nombre']
            apellido_paterno = self.data['apellido_paterno']
            apellido_materno = self.data['apellido_materno']
            rfc = self.data['rfc']
            nss = self.data['nss']
            curp = self.data['curp']
            salario_base = self.data['salario_base']
            tipo_jornada = self.data['tipo_jornada']
            fecha_vencimiento_tarjeton = self.data['fecha_vencimiento_tarjeton']
            apodo = self.data['apodo']
            fotos = self.data['fotos']
            telefono = self.data['telefono']

            # Ejecutar la consulta de inserción en empleado_chofer
            query = """
            INSERT INTO empleado_chofer (id_chofer, nombre, apellido_paterno, apellido_materno, rfc, nss, curp, salario_base, tipo_jornada, fecha_vencimiento_tarjeton, foto_credencial_frontal, foto_credencial_trasera, foto_tarjeton_frontal, foto_tarjeton_trasera, foto_chofer, telefono)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_chofer
            """
            data = (
                id_chofer, nombre, apellido_paterno, apellido_materno, rfc, nss, curp, salario_base, tipo_jornada, fecha_vencimiento_tarjeton,
                fotos.get('foto_credencial_frontal'), fotos.get('foto_credencial_trasera'), fotos.get('foto_tarjeton_frontal'),
                fotos.get('foto_tarjeton_trasera'), fotos.get('foto_chofer'), telefono
            )

            self.db.execute_query(query, data)
            id_chofer_inserted = self.db.cursor.fetchone()[0]

            # Insertar el apodo en la tabla apodos
            if apodo.strip():
                apodo_query = """
                INSERT INTO apodos (id_chofer, apodo)
                VALUES (%s, %s)
                """
                self.db.execute_query(apodo_query, (id_chofer_inserted, apodo))

            # Hacer el COMMIT para finalizar ambas transacciones
            self.db.connection.commit()

            # Emitir señal de finalización
            self.finished.emit()

        except Exception as e:
            # Hacer rollback en caso de error
            self.db.connection.rollback()
            self.error.emit(str(e))

class AddChoferForm(QWidget):
    def __init__(self, db, parent=None):
        super(AddChoferForm, self).__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Chofer')
        self.resize(450, 600)

        # Creamos el área de scroll y su contenedor principal
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        # Widget que contendrá todos los elementos del formulario
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)

        form_layout = QFormLayout()
        # Campo de ID (solo enteros)
        self.id_chofer = QLineEdit(self)
        self.id_chofer.setValidator(QIntValidator(0, 999999, self))  # Solo permitir números enteros
        form_layout.addRow('ID Chofer:', self.id_chofer)

        self.nombre = QLineEdit(self)
        self.nombre.textChanged.connect(lambda: self.nombre.setText(self.nombre.text().upper()))
        form_layout.addRow('Nombre:', self.nombre)

        self.apellido_paterno = QLineEdit(self)
        self.apellido_paterno.textChanged.connect(lambda: self.apellido_paterno.setText(self.apellido_paterno.text().upper()))
        form_layout.addRow('Apellido Paterno:', self.apellido_paterno)

        self.apellido_materno = QLineEdit(self)
        self.apellido_materno.textChanged.connect(lambda: self.apellido_materno.setText(self.apellido_materno.text().upper()))
        form_layout.addRow('Apellido Materno:', self.apellido_materno)

        self.telefono = QLineEdit(self)
        self.telefono.setMaxLength(10)
        self.telefono.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}$'), self))  # Solo permitir 10 dígitos**
        form_layout.addRow('Teléfono:', self.telefono)

        self.rfc = QLineEdit(self)
        self.rfc.setMaxLength(13)
        self.rfc.textChanged.connect(lambda: self.rfc.setText(self.rfc.text().upper()))
        form_layout.addRow('RFC:', self.rfc)

        self.nss = QLineEdit(self)
        self.nss.setMaxLength(11)
        self.nss.textChanged.connect(lambda: self.nss.setText(self.nss.text().upper()))
        form_layout.addRow('NSS:', self.nss)

        self.curp = QLineEdit(self)
        self.curp.setMaxLength(18)
        self.curp.textChanged.connect(lambda: self.curp.setText(self.curp.text().upper()))
        form_layout.addRow('CURP:', self.curp)

        self.salario_base = QLineEdit(self)
        self.salario_base.setMaxLength(12)
        self.salario_base.setPlaceholderText('99999999.99')
        self.salario_base.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}(\.\d{0,2})?$'), self))
        form_layout.addRow('Salario Base:', self.salario_base)

        self.tipo_jornada = QComboBox(self)
        self.tipo_jornada.addItems(['MATUTINO', 'VESPERTINO', 'MIXTO', 'COMPLETO'])
        form_layout.addRow('Tipo de Jornada:', self.tipo_jornada)

        self.fecha_vencimiento_tarjeton = QDateEdit(self)
        self.fecha_vencimiento_tarjeton.setCalendarPopup(True)
        self.fecha_vencimiento_tarjeton.setDate(QDate.currentDate())
        form_layout.addRow('Fecha Vencimiento Tarjetón:', self.fecha_vencimiento_tarjeton)

        self.apodo = QLineEdit(self)
        form_layout.addRow('Apodo:', self.apodo)

        self.photos = {}
        self.photo_labels = {}

        # Creación de las secciones de fotos
        self.create_photo_section(form_layout, 'Foto Credencial Frontal', 'foto_credencial_frontal')
        self.create_photo_section(form_layout, 'Foto Credencial Trasera', 'foto_credencial_trasera')
        self.create_photo_section(form_layout, 'Foto Tarjetón Frontal', 'foto_tarjeton_frontal')
        self.create_photo_section(form_layout, 'Foto Tarjetón Trasera', 'foto_tarjeton_trasera')
        self.create_photo_section(form_layout, 'Foto Chofer', 'foto_chofer')

        self.submit_btn = QPushButton('Agregar Chofer', self)
        self.submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(self.submit_btn)

        container_layout.addLayout(form_layout)
        scroll_area.setWidget(container_widget)

        # Establecer el layout del widget principal
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def create_photo_section(self, form_layout, label, photo_type):
        container = QWidget()
        layout = QHBoxLayout()

        select_button = QPushButton('Seleccionar Archivo', self)
        select_button.clicked.connect(lambda: self.select_photo(photo_type))
        layout.addWidget(select_button)

        capture_button = QPushButton('Tomar Foto', self)
        capture_button.clicked.connect(lambda: self.take_photo_with_camera(photo_type))
        layout.addWidget(capture_button)

        self.photo_labels[photo_type] = QLabel(self)
        layout.addWidget(self.photo_labels[photo_type])

        container.setLayout(layout)
        form_layout.addRow(label, container)

    # Métodos para capturar fotos específicos
    def take_foto_frontal(self):
        self.take_photo_with_camera('foto_credencial_frontal')

    def take_foto_trasera(self):
        self.take_photo_with_camera('foto_credencial_trasera')

    def take_foto_tarjeton_frontal(self):
        self.take_photo_with_camera('foto_tarjeton_frontal')

    def take_foto_tarjeton_trasera(self):
        self.take_photo_with_camera('foto_tarjeton_trasera')

    def take_foto_chofer(self):
        self.take_photo_with_camera('foto_chofer')

    def take_photo_with_camera(self, photo_type):
        camera_dialog = CameraDialog(photo_type, self)
        if camera_dialog.exec_() == QDialog.Accepted:
            image = camera_dialog.get_image()
            if image:
                # Convertir la imagen a bytes y guardar temporalmente
                buffer = QBuffer()
                buffer.open(QBuffer.WriteOnly)
                image.save(buffer, 'JPEG')
                image_bytes = bytes(buffer.data())

                # Almacenar la imagen capturada
                self.photos[photo_type] = image_bytes

                # Mostrar la imagen en la etiqueta correspondiente
                pixmap = QPixmap.fromImage(image)
                self.photo_labels[photo_type].setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def select_photo(self, photo_type):
        options = QFileDialog.Options()
        filters = "Images (*.jpg *.jpeg *.png)"
        filename, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto", "", filters, options=options)

        if filename:
            if not (filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg') or filename.lower().endswith('.png')):
                QMessageBox.critical(self, 'Error', 'El archivo seleccionado no es una imagen válida (debe ser JPG, JPEG o PNG).', QMessageBox.Ok)
                return

            pixmap = QPixmap(filename)

            # Convertir la imagen a bytes y guardarla temporalmente
            image = QImage(filename)
            buffer = QBuffer()
            buffer.open(QBuffer.WriteOnly)
            image.save(buffer, 'JPEG')
            image_bytes = bytes(buffer.data())

            # Almacenar la imagen seleccionada
            self.photos[photo_type] = image_bytes

            # Mostrar la imagen en la etiqueta correspondiente
            self.photo_labels[photo_type].setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def submit_form(self):
        try:
            # Recopilar los datos del formulario
            id_chofer_text = self.id_chofer.text()
            if not id_chofer_text.isdigit():
                QMessageBox.critical(self, 'Error', 'El ID del chofer debe ser un número entero.', QMessageBox.Ok)
                return
            id_chofer = int(id_chofer_text)
            nombre = self.nombre.text().upper()
            apellido_paterno = self.apellido_paterno.text().upper()
            apellido_materno = self.apellido_materno.text().upper()
            rfc = self.rfc.text().upper()
            nss = self.nss.text().upper()
            curp = self.curp.text().upper()
            salario_base = self.salario_base.text()
            tipo_jornada = self.tipo_jornada.currentText()
            fecha_vencimiento_tarjeton = self.fecha_vencimiento_tarjeton.date().toString('yyyy-MM-dd')
            apodo = self.apodo.text()
            telefono = self.telefono.text()

            # Verificar que todos los campos estén completos
            if not all([id_chofer, nombre, apellido_paterno, apellido_materno, rfc, nss, curp, salario_base, tipo_jornada, fecha_vencimiento_tarjeton, telefono]):
                QMessageBox.critical(self, 'Error', 'Todos los campos deben estar llenos', QMessageBox.Ok)
                return

            # Verificar las fotos
            fotos = {}
            for key in ['foto_credencial_frontal', 'foto_credencial_trasera', 'foto_tarjeton_frontal', 'foto_tarjeton_trasera', 'foto_chofer']:
                if key in self.photos:
                    fotos[key] = self.photos[key]
                else:
                    QMessageBox.critical(self, 'Error', f'{key} no está proporcionada', QMessageBox.Ok)
                    return

            # Mostrar la ventana de carga
            self.loading_dialog = LoadingDialog(self)
            self.loading_dialog.show()

            # Preparar datos para el trabajador
            data = {
                'id_chofer': id_chofer,
                'nombre': nombre,
                'apellido_paterno': apellido_paterno,
                'apellido_materno': apellido_materno,
                'rfc': rfc,
                'nss': nss,
                'curp': curp,
                'salario_base': salario_base,
                'tipo_jornada': tipo_jornada,
                'fecha_vencimiento_tarjeton': fecha_vencimiento_tarjeton,
                'apodo': apodo,
                'fotos': fotos,
                'telefono': telefono
            }

            # Iniciar el hilo de trabajo
            self.worker = SaveWorker(self.db, data)
            self.worker.progress.connect(self.loading_dialog.progress_bar.setValue)
            self.worker.finished.connect(self.on_save_finished)
            self.worker.error.connect(self.on_save_error)
            self.worker.start()

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e), QMessageBox.Ok)

    def on_save_finished(self):
        self.loading_dialog.close()
        QMessageBox.information(self, 'Éxito', 'Chofer y apodo agregado correctamente.', QMessageBox.Ok)
        # Abrir ventana de captura de huella digital
        self.add_huella_window = AddHuellaWindow()
        self.close()

    def on_save_error(self, error_message):
        self.loading_dialog.close()
        QMessageBox.critical(self, 'Error', error_message, QMessageBox.Ok)
