from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QDialog, QFormLayout, QComboBox, QLabel, QLineEdit, QFileDialog, QMessageBox, QHBoxLayout, QDateEdit, QTimeEdit, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime
from PyQt5.QtGui import QIcon, QPixmap
import psycopg2

class RecursosHumanosWindow(QMainWindow):
    def __init__(self, db):
        super(RecursosHumanosWindow, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Recursos Humanos')
        self.setGeometry(80, 80, 200, 200)

        layout = QVBoxLayout()

        self.calcular_sueldo_btn = QPushButton('Calcular Sueldo', self)
        self.calcular_sueldo_btn.clicked.connect(self.calcular_sueldo)
        self.calcular_sueldo_btn.setStyleSheet("background-color: rgb(74, 141, 193);")
        layout.addWidget(self.calcular_sueldo_btn)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def calcular_sueldo(self):
        dialog = CalcularSueldoForm(self.db, self)
        dialog.exec_()

class CalcularSueldoForm(QDialog):
    def __init__(self, db, parent=None):
        super(CalcularSueldoForm, self).__init__(parent)
        self.setWindowTitle('Calcular Sueldo')
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.chofer_combo = QComboBox(self)
        self.populate_choferes()
        form_layout.addRow('Chofer:', self.chofer_combo)

        self.fecha_inicio = QDateEdit(self)
        self.fecha_inicio.setCalendarPopup(True)
        form_layout.addRow('Fecha Inicio:', self.fecha_inicio)

        self.hora_inicio = QTimeEdit(self)
        self.hora_inicio.setDisplayFormat('HH:mm')
        form_layout.addRow('Hora Inicio:', self.hora_inicio)

        self.fecha_final = QDateEdit(self)
        self.fecha_final.setCalendarPopup(True)
        form_layout.addRow('Fecha Final:', self.fecha_final)

        self.hora_final = QTimeEdit(self)
        self.hora_final.setDisplayFormat('HH:mm')
        form_layout.addRow('Hora Final:', self.hora_final)

        self.calcular_btn = QPushButton('Calcular', self)
        self.calcular_btn.clicked.connect(self.calcular)
        self.calcular_btn.setStyleSheet("background-color: rgb(74, 141, 193);")
        form_layout.addRow(self.calcular_btn)

        self.resultado_tabla = QTableWidget(self)
        form_layout.addRow(self.resultado_tabla)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def populate_choferes(self):
        query = "SELECT id_chofer, nombre, apellido_paterno, apellido_materno FROM Empleado_Chofer WHERE estatus = 'ACTIVO' ORDER BY id_chofer ASC"
        self.db.execute_query(query)
        choferes = self.db.fetch_all()
        for chofer in choferes:
            nombre_completo = f"{chofer[0]} - {chofer[1]} {chofer[2]} {chofer[3]}"
            self.chofer_combo.addItem(nombre_completo, chofer[0])

    def calcular(self):
        id_chofer = self.chofer_combo.currentData()
        fecha_inicio = self.fecha_inicio.date().toString('yyyy-MM-dd')
        hora_inicio = self.hora_inicio.time().toString('HH:mm:ss')
        fecha_final = self.fecha_final.date().toString('yyyy-MM-dd')
        hora_final = self.hora_final.time().toString('HH:mm:ss')

        query = """
        SELECT folio, id_chofer, eco, fecha_entrada, hora_entrada, fecha_salida, hora_salida, kilometraje_entrada, kilometraje_salida, diesel_entrada, diesel_salida
        FROM historial_jornada_completa
        WHERE id_chofer = %s AND (fecha_entrada || ' ' || hora_entrada) >= %s AND (fecha_salida || ' ' || hora_salida) <= %s
        """
        params = (id_chofer, f"{fecha_inicio} {hora_inicio}", f"{fecha_final} {hora_final}")

        try:
            self.db.execute_query(query, params)
            registros = self.db.fetch_all()

            total_kilometros = 0
            total_diesel = 0
            total_horas = 0

            for registro in registros:
                kilometros = registro[8] - registro[7]  # kilometraje_salida - kilometraje_entrada
                diesel = registro[9] - registro[10]  # diesel_entrada - diesel_salida
                horas = self.calculate_hours(registro[5], registro[6], registro[3], registro[4])  # fecha_salida, hora_salida, fecha_entrada, hora_entrada

                total_kilometros += kilometros
                total_diesel += diesel
                total_horas += horas

            self.resultado_tabla.setColumnCount(8)
            self.resultado_tabla.setHorizontalHeaderLabels(['Folio', 'ID Chofer', 'Nombre Chofer', 'Fecha Entrada', 'Hora Entrada', 'Económico', 'Fecha Salida', 'Hora Salida'])
            self.resultado_tabla.setRowCount(len(registros))

            for i, registro in enumerate(registros):
                self.resultado_tabla.setItem(i, 0, QTableWidgetItem(str(registro[0])))
                self.resultado_tabla.setItem(i, 1, QTableWidgetItem(str(registro[1])))
                self.resultado_tabla.setItem(i, 2, QTableWidgetItem(self.get_chofer_nombre(registro[1])))
                self.resultado_tabla.setItem(i, 3, QTableWidgetItem(str(registro[3])))
                self.resultado_tabla.setItem(i, 4, QTableWidgetItem(str(registro[4])))
                self.resultado_tabla.setItem(i, 5, QTableWidgetItem(str(registro[2])))
                self.resultado_tabla.setItem(i, 6, QTableWidgetItem(str(registro[5])))
                self.resultado_tabla.setItem(i, 7, QTableWidgetItem(str(registro[6])))

            layout_resultados = QVBoxLayout()

            self.resultado_kilometros = QLabel(f"Kilómetros Recorridos: {total_kilometros}")
            layout_resultados.addWidget(self.resultado_kilometros)

            self.resultado_diesel = QLabel(f"Diesel Consumido: {total_diesel}")
            layout_resultados.addWidget(self.resultado_diesel)

            self.resultado_horas = QLabel(f"Horas Laboradas: {total_horas}")
            layout_resultados.addWidget(self.resultado_horas)

            self.resultado_sueldo = QLabel("Sueldo Base: 5000")
            layout_resultados.addWidget(self.resultado_sueldo)

            self.layout().addLayout(layout_resultados)

        except psycopg2.Error as e:
            self.db.connection.rollback()  # Revertir cambios en caso de error
            print(f"Error en la consulta de cálculo: {e}")
            QMessageBox.critical(self, 'Error', f'Ocurrió un error al calcular el sueldo: {e}', QMessageBox.Ok)

    def calculate_hours(self, fecha_salida, hora_salida, fecha_entrada, hora_entrada):
        datetime_salida = QDateTime.fromString(f"{fecha_salida} {hora_salida}", "yyyy-MM-dd HH:mm:ss")
        datetime_entrada = QDateTime.fromString(f"{fecha_entrada} {hora_entrada}", "yyyy-MM-dd HH:mm:ss")

        if datetime_salida < datetime_entrada:
            datetime_salida = datetime_salida.addDays(1)

        return (datetime_salida.toSecsSinceEpoch() - datetime_entrada.toSecsSinceEpoch()) / 3600

    def get_chofer_nombre(self, id_chofer):
        query = "SELECT nombre, apellido_paterno, apellido_materno FROM Empleado_Chofer WHERE id_chofer = %s"
        self.db.execute_query(query, (id_chofer,))
        result = self.db.fetch_all()[0]
        return f"{result[0]} {result[1]} {result[2]}"

class Database:
    def __init__(self, host, database, user, password):
        self.conn = psycopg2.connect(host=host, database=database, user=user, password=password)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()  # Confirmar la transacción
        except psycopg2.Error as e:
            self.conn.rollback()  # Revertir cambios si ocurre un error
            raise e

    def fetch_all(self):
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()
