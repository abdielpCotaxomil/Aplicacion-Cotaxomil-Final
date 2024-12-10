from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QDateTimeEdit, QMessageBox, QHBoxLayout, QComboBox
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import QDateTime
import psycopg2

class AddRecForm(QMainWindow):
    def __init__(self, db):
        super(AddRecForm, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Recaudo')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Generado automáticamente')
        layout.addWidget(self.folio_label)

        self.fecha_hora_label = QLabel('Fecha y Hora:')
        self.fecha_hora_edit = QDateTimeEdit(self)
        self.fecha_hora_edit.setDateTime(QDateTime.currentDateTime())
        self.fecha_hora_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.fecha_hora_edit.setReadOnly(True)
        layout.addWidget(self.fecha_hora_label)
        layout.addWidget(self.fecha_hora_edit)

        self.eco_label = QLabel('Eco:')
        self.eco_combo = QComboBox(self)
        self.load_autobus_data()  # Cargar datos en el combo box
        layout.addWidget(self.eco_label)
        layout.addWidget(self.eco_combo)

        # Conectar la señal al método on_eco_selected
        self.eco_combo.currentIndexChanged.connect(self.on_eco_selected)

        self.id_chofer1_label = QLabel('ID Chofer 1:')
        self.id_chofer1_combo = QComboBox(self)
        layout.addWidget(self.id_chofer1_label)
        layout.addWidget(self.id_chofer1_combo)

        self.id_chofer2_label = QLabel('ID Chofer 2 (opcional):')
        self.id_chofer2_combo = QComboBox(self)
        layout.addWidget(self.id_chofer2_label)
        layout.addWidget(self.id_chofer2_combo)

        self.monedas_label = QLabel('Monedas:')
        self.monedas_edit = QLineEdit(self)
        self.monedas_edit.setMaxLength(12)
        self.monedas_edit.setPlaceholderText('99999999.99')
        self.monedas_edit.setValidator(QDoubleValidator(0.00, 99999999.99, 2))  # Rango y precisión
        layout.addWidget(self.monedas_label)
        layout.addWidget(self.monedas_edit)

        self.billetes_label = QLabel('Billetes:')
        self.billetes_edit = QLineEdit(self)
        self.billetes_edit.setMaxLength(12)
        self.billetes_edit.setPlaceholderText('99999999.99')
        self.billetes_edit.setValidator(QDoubleValidator(0.00, 99999999.99, 2))  # Rango y precisión
        layout.addWidget(self.billetes_label)
        layout.addWidget(self.billetes_edit)

        self.add_recaudo_button = QPushButton('GUARDAR', self)
        self.add_recaudo_button.clicked.connect(self.show_saved_form)
        self.add_recaudo_button.setStyleSheet("background-color: rgb(127, 98, 184);")
        layout.addWidget(self.add_recaudo_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        # Cargar todos los choferes activos al iniciar
        self.load_all_active_choferes()

        # Llamar a on_eco_selected() para cargar choferes del eco seleccionado inicialmente
        self.on_eco_selected()

    def load_autobus_data(self):
        try:
            query = "SELECT eco, tipo FROM autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"
            self.db.cursor.execute(query)
            autobuses = self.db.cursor.fetchall()

            for eco, tipo in autobuses:
                self.eco_combo.addItem(f"{eco} - {tipo}", eco)

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar datos de autobuses: {e}', QMessageBox.Ok)

    def on_eco_selected(self):
        selected_eco = self.eco_combo.currentData()
        if selected_eco:
            self.preselect_choferes_for_eco(selected_eco)

    def load_all_active_choferes(self):
        try:
            # Limpiar los combos de choferes
            self.id_chofer1_combo.clear()
            self.id_chofer2_combo.clear()

            # Añadir la opción de NULL al combo de id_chofer2
            self.id_chofer2_combo.addItem("Sin Chofer 2", None)

            # Cargar todos los choferes activos
            query = """
            SELECT c.id_chofer, c.nombre, c.apellido_paterno, c.apellido_materno, a.apodo
            FROM empleado_chofer c
            LEFT JOIN apodos a ON c.id_chofer = a.id_chofer
            WHERE c.estatus = 'ACTIVO'
            ORDER BY c.id_chofer
            """
            self.db.cursor.execute(query)
            self.all_choferes = self.db.cursor.fetchall()

            for id_chofer, nombre, apellido_paterno, apellido_materno, apodo in self.all_choferes:
                display_text = f"{id_chofer} - {nombre} {apellido_paterno} {apellido_materno}"
                if apodo:
                    display_text += f" - {apodo}"
                self.id_chofer1_combo.addItem(display_text, id_chofer)
                self.id_chofer2_combo.addItem(display_text, id_chofer)

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar todos los choferes activos: {e}', QMessageBox.Ok)

    def preselect_choferes_for_eco(self, eco):
        try:
            # Obtener la fecha y hora actuales
            now = QDateTime.currentDateTime()
            today_date = now.date().toString('yyyy-MM-dd')

            # Construir los rangos de fecha y hora
            start_datetime = QDateTime.fromString(f"{today_date} 03:45:00", 'yyyy-MM-dd HH:mm:ss')
            end_datetime = start_datetime.addDays(1).addSecs(-7200)  # Hasta las 2:00 am del siguiente día

            start_datetime_str = start_datetime.toString('yyyy-MM-dd HH:mm:ss')
            end_datetime_str = end_datetime.toString('yyyy-MM-dd HH:mm:ss')

            # Consulta para obtener los choferes, combinando fecha_entrada y hora_entrada
            query = """
            SELECT DISTINCT c.id_chofer
            FROM historial_jornada_entrada hje
            INNER JOIN empleado_chofer c ON hje.id_chofer = c.id_chofer
            WHERE hje.eco = %s
            AND (hje.fecha_entrada || ' ' || hje.hora_entrada)::timestamp BETWEEN %s AND %s
            """
            self.db.cursor.execute(query, (eco, start_datetime_str, end_datetime_str))
            choferes = self.db.cursor.fetchall()
            chofer_ids = [row[0] for row in choferes]

            # Preseleccionar los choferes en los combos si están en la lista
            if chofer_ids:
                index1 = self.id_chofer1_combo.findData(chofer_ids[0])
                if index1 != -1:
                    self.id_chofer1_combo.setCurrentIndex(index1)
                if len(chofer_ids) > 1:
                    index2 = self.id_chofer2_combo.findData(chofer_ids[1])
                    if index2 != -1:
                        self.id_chofer2_combo.setCurrentIndex(index2)
                else:
                    # Si solo hay un chofer, seleccionar 'Sin Chofer 2' en id_chofer2_combo
                    self.id_chofer2_combo.setCurrentIndex(0)  # Índice 0 es 'Sin Chofer 2'
            else:
                # Si no hay choferes, resetear selecciones
                self.id_chofer1_combo.setCurrentIndex(-1)
                self.id_chofer2_combo.setCurrentIndex(0)  # 'Sin Chofer 2'

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al preseleccionar choferes: {e}', QMessageBox.Ok)

    def show_saved_form(self):
        fecha_hora = self.fecha_hora_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')
        eco = self.eco_combo.currentData()  # Obtener el valor de eco

        id_chofer1 = self.id_chofer1_combo.currentData()  # Obtener el valor de id_chofer1
        id_chofer2 = self.id_chofer2_combo.currentData()  # Obtener el valor de id_chofer2

        monedas = self.monedas_edit.text()
        billetes = self.billetes_edit.text()

        self.saved_form = RecSavedForm(self, self.db, fecha_hora, eco, id_chofer1, id_chofer2, monedas, billetes)
        self.saved_form.show()
        self.close()

class RecSavedForm(QMainWindow):
    def __init__(self, parent, db, fecha_hora, eco, id_chofer1, id_chofer2, monedas, billetes):
        super(RecSavedForm, self).__init__(parent)
        self.parent = parent
        self.db = db
        self.fecha_hora = fecha_hora
        self.eco = eco
        self.id_chofer1 = id_chofer1
        self.id_chofer2 = id_chofer2
        self.monedas = monedas
        self.billetes = billetes
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Recaudo Guardado')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Será generado al guardar')
        layout.addWidget(self.folio_label)

        self.fecha_hora_label = QLabel(f'Fecha y Hora: {self.fecha_hora}')
        layout.addWidget(self.fecha_hora_label)

        self.eco_label = QLabel(f'Eco: {self.eco}')
        layout.addWidget(self.eco_label)

        self.id_chofer1_label = QLabel(f'ID Chofer 1: {self.id_chofer1}')
        layout.addWidget(self.id_chofer1_label)

        self.id_chofer2_label = QLabel(f'ID Chofer 2: {self.id_chofer2}')
        layout.addWidget(self.id_chofer2_label)

        self.monedas_label = QLabel(f'Monedas: {self.monedas}')
        layout.addWidget(self.monedas_label)

        self.billetes_label = QLabel(f'Billetes: {self.billetes}')
        layout.addWidget(self.billetes_label)

        buttons_layout = QHBoxLayout()

        self.accept_button = QPushButton('Aceptar', self)
        self.accept_button.clicked.connect(self.accept)
        self.accept_button.setStyleSheet("background-color: rgb(127, 98, 184);")
        buttons_layout.addWidget(self.accept_button)

        self.edit_button = QPushButton('Editar', self)
        self.edit_button.clicked.connect(self.edit)
        self.edit_button.setStyleSheet("background-color: rgb(127, 98, 184);")
        buttons_layout.addWidget(self.edit_button)

        layout.addLayout(buttons_layout)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def accept(self):
        try:
            # Generar folio automáticamente (entero)
            query_folio = "SELECT nextval('folio_seq')"
            self.db.cursor.execute(query_folio)
            folio = self.db.cursor.fetchone()[0]

            query_insert = """
            INSERT INTO historial_recaudo (folio, fecha, hora, eco, id_chofer1, id_chofer2, monedas, billetes)
            VALUES (%s, current_date, %s, %s, %s, %s, %s, %s)
            """

            self.db.cursor.execute(query_insert, (
                folio, self.fecha_hora, self.eco, self.id_chofer1, self.id_chofer2, self.monedas, self.billetes
            ))

            # Agregar commit para finalizar la transacción
            self.db.connection.commit()

            QMessageBox.information(self, 'Éxito', 'Recaudo agregado correctamente.', QMessageBox.Ok)
            self.close()

        except psycopg2.Error as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al agregar recaudo: {e}', QMessageBox.Ok)

        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)

    def edit(self):
        self.close()
        self.parent.show()
