from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QDateEdit,
    QRadioButton, QButtonGroup, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
import psycopg2
from autobus_info_window import AutobusInfoWindow

class AddAutobusForm(QWidget):
    def __init__(self, db, parent=None):
        super(AddAutobusForm, self).__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Autobus')
        self.resize(400, 400)

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.eco = QLineEdit(self)
        form_layout.addRow('ECO:', self.eco)

        self.placa = QLineEdit(self)
        self.placa.setMaxLength(10)
        self.placa.textChanged.connect(lambda: self.placa.setText(self.placa.text().upper()))
        form_layout.addRow('Placa:', self.placa)

        self.numero_serie = QLineEdit(self)
        form_layout.addRow('Número de Serie:', self.numero_serie)
        self.numero_serie.textChanged.connect(lambda: self.numero_serie.setText(self.numero_serie.text().upper()))

        self.numero_motor = QLineEdit(self)
        form_layout.addRow('Número de Motor:', self.numero_motor)
        self.numero_motor.textChanged.connect(lambda: self.numero_motor.setText(self.numero_motor.text().upper()))

        self.fecha_vigencia_seguro = QDateEdit(self)
        self.fecha_vigencia_seguro.setCalendarPopup(True)
        self.fecha_vigencia_seguro.setDate(QDate.currentDate())
        form_layout.addRow('Fecha de Vigencia del Seguro:', self.fecha_vigencia_seguro)

        self.nombre_aseguradora = QLineEdit(self)
        form_layout.addRow('Nombre de la Aseguradora:', self.nombre_aseguradora)
        self.nombre_aseguradora.textEdited.connect(lambda: self.nombre_aseguradora.setText(self.nombre_aseguradora.text().upper()))

        # Radio buttons for tipo
        self.tipo_toreto = QRadioButton('TORETO')
        self.tipo_zafiro = QRadioButton('ZAFIRO')
        self.tipo_group = QButtonGroup()
        self.tipo_group.addButton(self.tipo_toreto)
        self.tipo_group.addButton(self.tipo_zafiro)

        tipo_layout = QVBoxLayout()
        tipo_layout.addWidget(self.tipo_toreto)
        tipo_layout.addWidget(self.tipo_zafiro)
        form_layout.addRow('Tipo:', tipo_layout)

        self.submit_btn = QPushButton('Agregar Autobus', self)
        self.submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(self.submit_btn)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def submit_form(self):
        try:
            eco = self.eco.text()
            placa = self.placa.text()
            numero_serie = self.numero_serie.text().upper()
            numero_motor = self.numero_motor.text().upper()
            fecha_vigencia_seguro = self.fecha_vigencia_seguro.text()
            estatus_fecha_seguro = self.eco.text()
            nombre_aseguradora = self.nombre_aseguradora.text().upper()
            tanque_litros = 11

            # Obtener el tipo seleccionado
            tipo_button = self.tipo_group.checkedButton()
            if tipo_button is None:
                QMessageBox.critical(self, 'Error', 'Debe seleccionar un tipo (TORETO o ZAFIRO)', QMessageBox.Ok)
                return
            tipo = tipo_button.text()

            if not all([eco, placa, numero_serie, numero_motor, fecha_vigencia_seguro, nombre_aseguradora, tipo]):
                QMessageBox.critical(self, 'Error', 'Todos los campos deben estar llenos', QMessageBox.Ok)
                return

            query = """
            INSERT INTO autobus (eco, placa, numero_serie, numero_motor, fecha_vigencia_seguro, estatus_fecha_seguro, nombre_aseguradora, tipo, tanque_litros)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING eco
            """

            try:
                self.db.cursor.execute(query, (eco, placa, numero_serie, numero_motor, fecha_vigencia_seguro, estatus_fecha_seguro, nombre_aseguradora, tipo, tanque_litros))
                id_autobus = self.db.cursor.fetchone()[0]
                self.db.connection.commit()

                QMessageBox.information(self, 'Éxito', f'Autobus agregado correctamente con ECO: {id_autobus}', QMessageBox.Ok)
                self.close()
            except psycopg2.Error as e:
                self.db.connection.rollback()
                QMessageBox.critical(self, 'Error', f'No se pudo agregar el autobus: {e}', QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado fuera del formulario: {e}', QMessageBox.Ok)

    def fetch_autobus_data(self, eco):
        try:
            query = """
            SELECT eco, placa, numero_serie, numero_motor, fecha_vigencia_seguro, estatus_fecha_seguro, nombre_aseguradora, tipo, tanque_litros
            FROM autobus
            WHERE eco = %s
            """
            self.db.cursor.execute(query, (eco,))
            row = self.db.cursor.fetchone()

            autobus_data = {
                "eco": row[0],
                "placa": row[1],
                "numero_serie": row[2],
                "numero_motor": row[3],
                "fecha_vigencia_seguro": row[4],
                "estatus_fecha_seguro": row[5],
                "nombre_aseguradora": row[6],
                "tipo": row[7],
                "tanque_litros": row[8]
            }
            return autobus_data
        except Exception as e:
            print(f"Error obteniendo los datos del autobus: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudo obtener los datos del autobus: {e}', QMessageBox.Ok)
            return {}

    def show_autobus_info(self, autobus_data):
        self.autobus_info_window = AutobusInfoWindow(autobus_data)
        self.autobus_info_window.exec_()
