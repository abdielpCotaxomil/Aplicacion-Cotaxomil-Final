from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt5.QtGui import QDoubleValidator
import psycopg2

class AddSumTanForm(QMainWindow):
    def __init__(self, db):
        super(AddSumTanForm, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Historial de Tanque')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Generado automáticamente')
        layout.addWidget(self.folio_label)

        self.litros_inicial_label = QLabel('Litros Iniciales:')
        self.litros_inicial_edit = QLineEdit(self)
        self.litros_inicial_edit.setMaxLength(12)
        self.litros_inicial_edit.setPlaceholderText('999999.99')
        self.litros_inicial_edit.setValidator(QDoubleValidator(0.00, 999999.99, 2))  # Rango y precisión
        layout.addWidget(self.litros_inicial_label)
        layout.addWidget(self.litros_inicial_edit)

        self.litros_final_label = QLabel('Litros Finales:')
        self.litros_final_edit = QLineEdit(self)
        self.litros_final_edit.setMaxLength(12)
        self.litros_final_edit.setPlaceholderText('999999.99')
        self.litros_final_edit.setValidator(QDoubleValidator(0.00, 999999.99, 2))  # Rango y precisión
        layout.addWidget(self.litros_final_label)
        layout.addWidget(self.litros_final_edit)

        self.litros_diesel_label = QLabel('Litros Diesel:')
        self.litros_diesel_edit = QLineEdit(self)
        self.litros_diesel_edit.setMaxLength(12)
        self.litros_diesel_edit.setPlaceholderText('999999.99')
        self.litros_diesel_edit.setValidator(QDoubleValidator(0.00, 999999.99, 2))  # Rango y precisión
        layout.addWidget(self.litros_diesel_label)
        layout.addWidget(self.litros_diesel_edit)

        self.add_tank_button = QPushButton('GUARDAR', self)
        self.add_tank_button.clicked.connect(self.save_tank_history)
        self.add_tank_button.setStyleSheet('background-color: rgb(88, 129, 216 );; color: white;')
        layout.addWidget(self.add_tank_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def save_tank_history(self):
        litros_inicial = self.litros_inicial_edit.text()
        litros_final = self.litros_final_edit.text()
        litros_diesel = self.litros_diesel_edit.text()

        try:
            query_folio = "SELECT nextval('folio_seq_cinco')"
            self.db.cursor.execute(query_folio)
            folio = self.db.cursor.fetchone()[0]

            query_insert = """
            INSERT INTO historial_tanque (folio, litros_inicial, litros_final, litros_diesel)
            VALUES (%s, %s, %s, %s)
            """

            self.db.cursor.execute(query_insert, (folio, litros_inicial, litros_final, litros_diesel))
            self.db.connection.commit()

            QMessageBox.information(self, 'Éxito', 'Historial de tanque agregado correctamente.', QMessageBox.Ok)
            self.close()

        except psycopg2.Error as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al agregar historial de tanque: {e}', QMessageBox.Ok)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
