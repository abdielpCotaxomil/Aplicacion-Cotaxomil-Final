from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QDateTimeEdit, QMessageBox, QHBoxLayout, QComboBox
from PyQt5.QtCore import QDateTime
import psycopg2

class AddLlenAutForm(QMainWindow):
    def __init__(self, db):
        super(AddLlenAutForm, self).__init__()
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


        self.cuenta_litros_inicial_label = QLabel('Litros inicial:')
        self.cuenta_litros_inicial_edit = QLineEdit(self)
        layout.addWidget(self.cuenta_litros_inicial_label)
        layout.addWidget(self.cuenta_litros_inicial_edit)

        self.cuenta_litros_final_label = QLabel('Litros Final:')
        self.cuenta_litros_final_edit = QLineEdit(self)
        layout.addWidget(self.cuenta_litros_final_label)
        layout.addWidget(self.cuenta_litros_final_edit)

        self.add_recaudo_button = QPushButton('Mostrar Datos Recaudo', self)
        self.add_recaudo_button.clicked.connect(self.show_saved_form)
        layout.addWidget(self.add_recaudo_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def show_saved_form(self):
        fecha_hora = self.fecha_hora_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')
        cuenta_litros_inicial = self.cuenta_litros_inicial_edit.text()
        cuenta_litros_final = self.cuenta_litros_final_edit.text()

        self.saved_form = RecSavedForm(self, self.db, fecha_hora, cuenta_litros_inicial, cuenta_litros_final)
        self.saved_form.show()
        self.close()

class RecSavedForm(QMainWindow):
    def __init__(self, parent, db, fecha_hora, cuenta_litros_inicial, cuenta_litros_final):
        super(RecSavedForm, self).__init__(parent)
        self.parent = parent
        self.db = db
        self.fecha_hora = fecha_hora
        self.cuenta_litros_inicial = cuenta_litros_inicial
        self.cuenta_litros_final = cuenta_litros_final
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Recaudo Guardado')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Será generado al guardar')
        layout.addWidget(self.folio_label)

        self.fecha_hora_label = QLabel(f'Fecha y Hora: {self.fecha_hora}')
        layout.addWidget(self.fecha_hora_label)

        self.monedas_label = QLabel(f'Litros inicial: {self.cuenta_litros_inicial}')
        layout.addWidget(self.monedas_label)

        self.billetes_label = QLabel(f'Litron final: {self.cuenta_litros_final}')
        layout.addWidget(self.billetes_label)

        buttons_layout = QHBoxLayout()

        self.accept_button = QPushButton('Aceptar', self)
        self.accept_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.accept_button)

        self.edit_button = QPushButton('Editar', self)
        self.edit_button.clicked.connect(self.edit)
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
            INSERT INTO cuenta_litros (folio, fecha, hora, cuenta_litros_inicial, cuenta_litros_final)
            VALUES (%s, current_date, %s, %s, %s, %s, %s, %s)
            """

            self.db.cursor.execute(query_insert, (folio, self.fecha_hora, self.cuenta_litros_inicial, self.cuenta_litros_final))
            self.db.connection.commit()

            QMessageBox.information(self, 'Éxito', 'Recaudo agregado correctamente.', QMessageBox.Ok)
            self.close()

        except psycopg2.Error as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al agregar recaudo: {e}', QMessageBox.Ok)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)

    def edit(self):
        self.close()
        self.parent.show()
