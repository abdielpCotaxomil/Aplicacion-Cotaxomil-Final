from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QLineEdit, QDateEdit, QMessageBox, QHBoxLayout, QLabel, QComboBox, QFileDialog, QDialog, QScrollArea
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap, QRegExpValidator, QImage
from PyQt5.QtCore import QRegExp, QBuffer
from PyQt5.QtMultimedia import QCamera, QCameraInfo, QCameraImageCapture
from PyQt5.QtMultimediaWidgets import QCameraViewfinder
import psycopg2
import sys
import datetime

class DatabaseConnection:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="tu_db",
            user="tu_usuario",
            password="tu_contraseña",
            host="localhost"
        )
        self.cursor = self.connection.cursor()

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

class EditChoForm(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Choferes")
        self.resize(600, 600)

        self.layout = QVBoxLayout()

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Buscar chofer...")
        self.search_bar.setStyleSheet("font-size: 16px;")
        self.search_bar.textChanged.connect(self.update_search_results)
        self.layout.addWidget(self.search_bar)

        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.list_widget)

        self.load_data_btn = QPushButton('Cargar Datos', self)
        self.load_data_btn.setStyleSheet("font-size: 16px;")
        self.load_data_btn.clicked.connect(self.load_data)
        self.layout.addWidget(self.load_data_btn)

        self.setLayout(self.layout)

    def load_data(self, search_text=""):
        try:
            # Modificar el query para incluir el texto de búsqueda
            if search_text:
                search_pattern = f"%{search_text}%"
                query = """
                SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, a.apodo
                FROM empleado_chofer e
                LEFT JOIN apodos a ON e.id_chofer = a.id_chofer
                WHERE e.estatus = 'ACTIVO' AND(
                CAST(e.id_chofer AS TEXT) ILIKE %s OR e.nombre ILIKE %s OR e.apellido_paterno ILIKE %s OR e.apellido_materno ILIKE %s OR a.apodo ILIKE %s)
                ORDER BY e.id_chofer ASC
                """
                # Ajustamos los parámetros para incluir el nuevo placeholder
                params = (search_pattern,) * 5
                self.db.cursor.execute(query, params)
            else:
                query = """
                SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, a.apodo
                FROM empleado_chofer e
                LEFT JOIN apodos a ON e.id_chofer = a.id_chofer WHERE e.estatus = 'ACTIVO' ORDER BY e.id_chofer ASC
                """
                self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()

            self.list_widget.clear()
            for row in rows:
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)

                item_text = f"{row[0]} - {row[1]} {row[2]} {row[3]}"
                if row[4]:
                    item_text += f" - \"<span style='color:red;'> {row[4]}</span>\""

                item_label = QLabel(item_text)
                item_label.setStyleSheet("font-size: 16px;")
                item_label.setFixedHeight(25)
                item_label.setTextFormat(Qt.RichText)

                edit_btn = QPushButton("Editar")
                edit_btn.setStyleSheet("background-color: rgb(255, 165, 0); font-size: 16px;")
                edit_btn.setFixedSize(80, 50)
                edit_btn.clicked.connect(lambda ch, row=row: self.edit_item(row[0]))

                item_layout.addWidget(item_label)
                item_layout.addWidget(edit_btn)

                item_widget.setLayout(item_layout)

                list_item = QListWidgetItem(self.list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, item_widget)

        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los datos: {e}', QMessageBox.Ok)

    def update_search_results(self):
        search_text = self.search_bar.text()
        self.load_data(search_text)

    def edit_item(self, item_id):
        self.edit_window = EditWindow(self.db, item_id)
        self.edit_window.show()

class EditWindow(QWidget):
    def __init__(self, db, item_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.item_id = item_id
        self.setWindowTitle("Editar Chofer")
        self.resize(600, 700)

        # Add scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        # Container for form content
        container_widget = QWidget()
        container_layout = QFormLayout(container_widget)

        # Campo para editar id_chofer
        self.id_chofer = QLineEdit(self)
        self.id_chofer.setValidator(QRegExpValidator(QRegExp(r'^\d+$'), self))  # Solo números enteros
        container_layout.addRow('ID Chofer:', self.id_chofer)

        # Text Fields for Driver Data
        self.nombre = QLineEdit(self)
        self.nombre.textChanged.connect(lambda: self.nombre.setText(self.nombre.text().upper()))
        container_layout.addRow('Nombre:', self.nombre)

        self.apellido_paterno = QLineEdit(self)
        self.apellido_paterno.textChanged.connect(lambda: self.apellido_paterno.setText(self.apellido_paterno.text().upper()))
        container_layout.addRow('Apellido Paterno:', self.apellido_paterno)

        self.apellido_materno = QLineEdit(self)
        self.apellido_materno.textChanged.connect(lambda: self.apellido_materno.setText(self.apellido_materno.text().upper()))
        container_layout.addRow('Apellido Materno:', self.apellido_materno)

        self.telefono = QLineEdit(self)
        self.telefono.setMaxLength(10)
        self.telefono.setValidator(QRegExpValidator(QRegExp(r'^\d{10}$'), self))  # Validar que solo sean 10 dígitos
        container_layout.addRow('Teléfono:', self.telefono)

        self.rfc = QLineEdit(self)
        self.rfc.setMaxLength(13)
        self.rfc.textChanged.connect(lambda: self.rfc.setText(self.rfc.text().upper()))
        container_layout.addRow('RFC:', self.rfc)

        self.nss = QLineEdit(self)
        self.nss.setMaxLength(11)
        self.nss.textChanged.connect(lambda: self.nss.setText(self.nss.text().upper()))
        container_layout.addRow('NSS:', self.nss)

        self.curp = QLineEdit(self)
        self.curp.setMaxLength(18)
        self.curp.textChanged.connect(lambda: self.curp.setText(self.curp.text().upper()))
        container_layout.addRow('CURP:', self.curp)

        self.salario_base = QLineEdit(self)
        self.salario_base.setPlaceholderText('99999999.99')
        self.salario_base.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}(\.\d{0,2})?$'), self))
        container_layout.addRow('Salario Base:', self.salario_base)

        self.tipo_jornada = QComboBox(self)
        self.tipo_jornada.addItems(['MATUTINO', 'VESPERTINO', 'MIXTO', 'COMPLETO'])
        container_layout.addRow('Tipo de Jornada:', self.tipo_jornada)

        self.fecha_vencimiento_tarjeton = QDateEdit(self)
        self.fecha_vencimiento_tarjeton.setCalendarPopup(True)
        container_layout.addRow('Fecha Vencimiento Tarjetón:', self.fecha_vencimiento_tarjeton)

        self.apodo = QLineEdit(self)
        container_layout.addRow('Apodo:', self.apodo)

        # Photos Section
        self.photos = {}
        self.photo_labels = {}
        self.create_photo_section(container_layout, 'Foto Credencial Frontal', 'foto_credencial_frontal')
        self.create_photo_section(container_layout, 'Foto Credencial Trasera', 'foto_credencial_trasera')
        self.create_photo_section(container_layout, 'Foto Tarjetón Frontal', 'foto_tarjeton_frontal')
        self.create_photo_section(container_layout, 'Foto Tarjetón Trasera', 'foto_tarjeton_trasera')
        self.create_photo_section(container_layout, 'Foto Chofer', 'foto_chofer')

        self.update_btn = QPushButton('Actualizar Datos', self)
        self.update_btn.clicked.connect(self.update_data)
        container_layout.addRow(self.update_btn)

        # Set up scroll area and main layout
        scroll_area.setWidget(container_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        self.load_data()

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

    def load_data(self):
        try:
            query = """
            SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, e.rfc, e.nss, e.curp, e.salario_base, e.tipo_jornada, e.fecha_vencimiento_tarjeton, a.apodo, 
                   e.foto_credencial_frontal, e.foto_credencial_trasera, e.foto_tarjeton_frontal, e.foto_tarjeton_trasera, e.foto_chofer, e.telefono
            FROM empleado_chofer e
            LEFT JOIN apodos a ON e.id_chofer = a.id_chofer
            WHERE e.id_chofer = %s
            """
            self.db.cursor.execute(query, (self.item_id,))
            row = self.db.cursor.fetchone()

            if row:
                (id_chofer, nombre, apellido_paterno, apellido_materno, rfc, nss, curp, salario_base, tipo_jornada, fecha_vencimiento, apodo,
                 foto_credencial_frontal, foto_credencial_trasera, foto_tarjeton_frontal, foto_tarjeton_trasera, foto_chofer, telefono) = row

                self.id_chofer.setText(str(id_chofer))
                self.nombre.setText(nombre)
                self.apellido_paterno.setText(apellido_paterno)
                self.apellido_materno.setText(apellido_materno)
                self.telefono.setText(telefono)
                self.rfc.setText(rfc)
                self.nss.setText(nss)
                self.curp.setText(curp)
                self.salario_base.setText(str(salario_base))
                self.tipo_jornada.setCurrentText(tipo_jornada)

                # Convert datetime.date to QDate
                if isinstance(fecha_vencimiento, datetime.date):
                    fecha_vencimiento_qdate = QDate(fecha_vencimiento.year, fecha_vencimiento.month, fecha_vencimiento.day)
                    self.fecha_vencimiento_tarjeton.setDate(fecha_vencimiento_qdate)

                self.apodo.setText(apodo if apodo else "")

                # Load and display photos
                self.display_photo('foto_credencial_frontal', foto_credencial_frontal)
                self.display_photo('foto_credencial_trasera', foto_credencial_trasera)
                self.display_photo('foto_tarjeton_frontal', foto_tarjeton_frontal)
                self.display_photo('foto_tarjeton_trasera', foto_tarjeton_trasera)
                self.display_photo('foto_chofer', foto_chofer)

        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los datos: {e}', QMessageBox.Ok)

    def display_photo(self, photo_type, photo_data):
        if photo_data:
            pixmap = QPixmap()
            pixmap.loadFromData(photo_data)
            self.photo_labels[photo_type].setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def select_photo(self, photo_type):
        options = QFileDialog.Options()
        filters = "Images (*.jpg *.jpeg *.png)"
        filename, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto", "", filters, options=options)

        if filename:
            pixmap = QPixmap(filename)
            image = QImage(filename)
            buffer = QBuffer()
            buffer.open(QBuffer.WriteOnly)
            image.save(buffer, 'JPEG')
            image_bytes = bytes(buffer.data())

            self.photos[photo_type] = image_bytes
            self.photo_labels[photo_type].setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def take_photo_with_camera(self, photo_type):
        camera_dialog = CameraDialog(photo_type, self)
        if camera_dialog.exec_() == QDialog.Accepted:
            image = camera_dialog.get_image()
            if image:
                buffer = QBuffer()
                buffer.open(QBuffer.WriteOnly)
                image.save(buffer, 'JPEG')
                image_bytes = bytes(buffer.data())

                self.photos[photo_type] = image_bytes

                pixmap = QPixmap.fromImage(image)
                self.photo_labels[photo_type].setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def update_data(self):
        try:
            id_chofer = int(self.id_chofer.text())
            nombre = self.nombre.text()
            apellido_paterno = self.apellido_paterno.text()
            apellido_materno = self.apellido_materno.text()
            telefono = self.telefono.text()
            rfc = self.rfc.text()
            nss = self.nss.text()
            curp = self.curp.text()
            salario_base = self.salario_base.text()
            tipo_jornada = self.tipo_jornada.currentText()
            fecha_vencimiento_tarjeton = self.fecha_vencimiento_tarjeton.date().toString('yyyy-MM-dd')
            apodo = self.apodo.text()

            if not all([id_chofer, nombre, apellido_paterno, apellido_materno, rfc, nss, curp, salario_base, tipo_jornada, fecha_vencimiento_tarjeton]):
                QMessageBox.critical(self, 'Error', 'Todos los campos deben estar llenos', QMessageBox.Ok)
                return

            query = """
            UPDATE empleado_chofer
            SET id_chofer = %s, nombre = %s, apellido_paterno = %s, apellido_materno = %s, rfc = %s, nss = %s, curp = %s, salario_base = %s, tipo_jornada = %s, fecha_vencimiento_tarjeton = %s, telefono = %s
            WHERE id_chofer = %s
            """
            self.db.cursor.execute(query, (id_chofer, nombre, apellido_paterno, apellido_materno, rfc, nss, curp, salario_base, tipo_jornada, fecha_vencimiento_tarjeton, telefono, self.item_id))

            # Update photos if they were changed
            for key, value in self.photos.items():
                query_photo = f"UPDATE empleado_chofer SET {key} = %s WHERE id_chofer = %s"
                self.db.cursor.execute(query_photo, (value, id_chofer))

            # Update or insert apodo in the apodos table
            query_apodo = """
            INSERT INTO apodos (id_chofer, apodo)
            VALUES (%s, %s)
            ON CONFLICT (id_chofer)
            DO UPDATE SET apodo = %s
            """
            self.db.cursor.execute(query_apodo, (id_chofer, apodo, apodo))

            # Confirm changes
            self.db.connection.commit()

            QMessageBox.information(self, 'Éxito', 'Datos actualizados correctamente', QMessageBox.Ok)
            self.close()
        except psycopg2.Error as e:
            self.db.connection.rollback()
            print(f"Error durante la actualización del query: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudo actualizar el chofer: {e}', QMessageBox.Ok)
        except Exception as e:
            print(f"Error inesperado: {e}")
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
