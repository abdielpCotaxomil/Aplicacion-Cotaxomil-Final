from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QDateTimeEdit, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QDateTime
import psycopg2

class AddInterForm(QMainWindow):
    def __init__(self, db):
        super(AddInterForm, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Inter')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Generado automáticamente')
        layout.addWidget(self.folio_label)

        self.fecha_inicio_label = QLabel('Fecha Inicio:')
        self.fecha_inicio_edit = QDateTimeEdit(self)
        self.fecha_inicio_edit.setDisplayFormat('yyyy-MM-dd')  # Muestra calendario y hora
        self.fecha_inicio_edit.setCalendarPopup(True)  # Muestra el calendario
        layout.addWidget(self.fecha_inicio_label)
        layout.addWidget(self.fecha_inicio_edit)

        self.hora_inicio_label = QLabel('Hora Inicio:')
        self.hora_inicio_edit = QDateTimeEdit(self)
        self.hora_inicio_edit.setDisplayFormat('HH:mm')
        self.hora_inicio_edit.setTime(QDateTime.currentDateTime().time())  # Establece la hora actual por defecto
        layout.addWidget(self.hora_inicio_label)
        layout.addWidget(self.hora_inicio_edit)

        self.fecha_fin_label = QLabel('Fecha Fin:')
        self.fecha_fin_edit = QDateTimeEdit(self)
        self.fecha_fin_edit.setDisplayFormat('yyyy-MM-dd')  # Muestra calendario y hora
        self.fecha_fin_edit.setCalendarPopup(True)  # Muestra el calendario
        layout.addWidget(self.fecha_fin_label)
        layout.addWidget(self.fecha_fin_edit)

        self.hora_fin_label = QLabel('Hora Fin:')
        self.hora_fin_edit = QDateTimeEdit(self)
        self.hora_fin_edit.setDisplayFormat('HH:mm')
        self.hora_fin_edit.setTime(QDateTime.currentDateTime().time())  # Establece la hora actual por defecto
        layout.addWidget(self.hora_fin_label)
        layout.addWidget(self.hora_fin_edit)

        self.add_recaudo_button = QPushButton('GUARDAR', self)
        self.add_recaudo_button.clicked.connect(self.save_recaudo)
        self.add_recaudo_button.setStyleSheet("background-color: rgb(127, 98, 184);")
        layout.addWidget(self.add_recaudo_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def save_recaudo(self):
        fecha_inicio = self.fecha_inicio_edit.date().toString('yyyy-MM-dd')
        hora_inicio = self.hora_inicio_edit.time().toString('HH:mm')
        fecha_fin = self.fecha_fin_edit.date().toString('yyyy-MM-dd')
        hora_fin = self.hora_fin_edit.time().toString('HH:mm')

        # No se envían monedas y billetes, se pasan como NULL
        self.saved_form = RecSavedForm(self, self.db, fecha_inicio, hora_inicio, fecha_fin, hora_fin, None, None, 0)
        self.saved_form.show()
        self.close()

class RecSavedForm(QMainWindow):
    def __init__(self, parent, db, fecha_inicio, hora_inicio, fecha_fin, hora_fin, total_monedas, total_billetes, total_recaudo):
        super(RecSavedForm, self).__init__(parent)
        self.parent = parent
        self.db = db
        self.fecha_inicio = fecha_inicio
        self.hora_inicio = hora_inicio
        self.fecha_fin = fecha_fin
        self.hora_fin = hora_fin
        self.total_monedas = total_monedas
        self.total_billetes = total_billetes
        self.total_recaudo = total_recaudo
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Recaudo Guardado')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Será generado al guardar')
        layout.addWidget(self.folio_label)

        self.fecha_inicio_label = QLabel(f'Fecha Inicio: {self.fecha_inicio}')
        layout.addWidget(self.fecha_inicio_label)

        self.hora_inicio_label = QLabel(f'Hora Inicio: {self.hora_inicio}')
        layout.addWidget(self.hora_inicio_label)

        self.fecha_fin_label = QLabel(f'Fecha Fin: {self.fecha_fin}')
        layout.addWidget(self.fecha_fin_label)

        self.hora_fin_label = QLabel(f'Hora Fin: {self.hora_fin}')
        layout.addWidget(self.hora_fin_label)

        # Solo muestra el total recaudado, no las monedas ni los billetes
        self.total_recaudo_label = QLabel(f'Total Recaudo: {self.total_recaudo}')
        layout.addWidget(self.total_recaudo_label)

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
            query_folio = "SELECT nextval('folio_seq_cuatro')"
            self.db.cursor.execute(query_folio)
            folio = self.db.cursor.fetchone()[0]

            # Calcular los totales de monedas y billetes en el intervalo de tiempo
            query_sum = """
            SELECT COALESCE(SUM(monedas), 0), COALESCE(SUM(billetes), 0)
            FROM historial_recaudo
            WHERE (fecha || ' ' || hora)::timestamp BETWEEN %s AND %s
            """

            self.db.cursor.execute(query_sum, (f"{self.fecha_inicio} {self.hora_inicio}", f"{self.fecha_fin} {self.hora_fin}"))
            total_monedas, total_billetes = self.db.cursor.fetchone()

            total_recaudo = total_monedas + total_billetes

            query_insert = """
            INSERT INTO suma_historial_recaudo (folio, fecha_inicio, hora_inicio, fecha_fin, hora_fin, total_monedas, total_billetes, total_recaudo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.db.cursor.execute(query_insert, (folio, self.fecha_inicio, self.hora_inicio, self.fecha_fin, self.hora_fin, total_monedas, total_billetes, total_recaudo))
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
