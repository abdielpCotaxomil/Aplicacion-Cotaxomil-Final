from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer
import psycopg2
from datetime import datetime, timedelta, time  # Añadido 'time' aquí

class RelojWindow(QMainWindow):
    def __init__(self, db):
        super(RelojWindow, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Historial Jornada Entrada')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Tabla para mostrar los datos
        self.jornada_table = QTableWidget(self)
        layout.addWidget(self.jornada_table)

        # Configurar el widget central
        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        # Configurar la tabla con las columnas necesarias
        self.jornada_table.setColumnCount(8)  # Cambiado de 5 a 8
        self.jornada_table.setHorizontalHeaderLabels([
            'ID Chofer', 'Nombre', 'Apellido Paterno', 'Apellido Materno',
            'ECO', 'Hora Entrada', 'Tipo Jornada', 'Tiempo Restante'
        ])

        # Timer para actualizar la tabla en tiempo real
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(1000)  # Actualiza cada segundo

    def update_table(self):
        # Obtener los rangos de fecha y hora
        start_datetime = datetime.now().replace(hour=3, minute=45, second=0, microsecond=0)
        end_datetime = (start_datetime + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)

        # Convertir a cadenas de texto para evitar problemas de tipo
        start_datetime_str = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        end_datetime_str = end_datetime.strftime('%Y-%m-%d %H:%M:%S')

        query = """
            SELECT h.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, h.eco, h.hora_entrada, e.tipo_jornada
            FROM historial_jornada_entrada h
            JOIN empleado_chofer e ON h.id_chofer = e.id_chofer
            WHERE (h.fecha_entrada || ' ' || h.hora_entrada) >= %s
            AND (h.fecha_entrada || ' ' || h.hora_entrada) < %s;
        """
        params = (start_datetime_str, end_datetime_str)

        try:
            self.db.execute_query(query, params)
            records = self.db.fetch_all()

            # Configurar la tabla
            self.jornada_table.setRowCount(len(records))

            current_time = datetime.now()

            for row_idx, row_data in enumerate(records):
                (
                    id_chofer, nombre, apellido_paterno, apellido_materno,
                    eco, hora_entrada_value, tipo_jornada
                ) = row_data

                # Manejar hora_entrada según su tipo
                if isinstance(hora_entrada_value, time):
                    hora_entrada = hora_entrada_value
                    hora_entrada_str = hora_entrada.strftime('%H:%M:%S')
                elif isinstance(hora_entrada_value, str):
                    # Intentar convertir la cadena a un objeto time
                    try:
                        hora_entrada = datetime.strptime(hora_entrada_value, '%H:%M:%S').time()
                        hora_entrada_str = hora_entrada_value
                    except ValueError as e:
                        print(f"Error al convertir hora_entrada_value: {hora_entrada_value}, error: {e}")
                        hora_entrada = None
                        hora_entrada_str = 'Hora inválida'
                else:
                    hora_entrada = None
                    hora_entrada_str = 'Hora inválida'

                # Si no se pudo obtener una hora válida, continuar con el siguiente registro
                if hora_entrada is None:
                    continue

                entrada_datetime = datetime.combine(current_time.date(), hora_entrada)

                # Ajustar la fecha si la hora de entrada es mayor a la hora actual
                if entrada_datetime > current_time:
                    entrada_datetime -= timedelta(days=1)

                # Duración de la jornada según el tipo
                if tipo_jornada in ['VESPERTINO', 'MATUTINO', 'MIXTO']:
                    jornada_duration = timedelta(hours=10)
                elif tipo_jornada == 'COMPLETO':
                    jornada_duration = timedelta(hours=16)
                else:
                    jornada_duration = timedelta(hours=0)  # Ajustar según sea necesario

                jornada_end_time = entrada_datetime + jornada_duration
                time_remaining = jornada_end_time - current_time

                if time_remaining.total_seconds() > 0:
                    hours, remainder = divmod(time_remaining.total_seconds(), 3600)
                    minutes, _ = divmod(remainder, 60)
                    time_remaining_str = f"{int(hours)}h {int(minutes)}m"
                else:
                    time_remaining_str = "Jornada terminada"

                # Rellenar la tabla con las columnas adicionales
                self.jornada_table.setItem(row_idx, 0, QTableWidgetItem(str(id_chofer)))
                self.jornada_table.setItem(row_idx, 1, QTableWidgetItem(nombre))
                self.jornada_table.setItem(row_idx, 2, QTableWidgetItem(apellido_paterno))
                self.jornada_table.setItem(row_idx, 3, QTableWidgetItem(apellido_materno))
                self.jornada_table.setItem(row_idx, 4, QTableWidgetItem(str(eco)))
                self.jornada_table.setItem(row_idx, 5, QTableWidgetItem(hora_entrada_str))
                self.jornada_table.setItem(row_idx, 6, QTableWidgetItem(tipo_jornada))
                self.jornada_table.setItem(row_idx, 7, QTableWidgetItem(time_remaining_str))

        except psycopg2.Error as e:
            print(f"Error al conectar con la base de datos: {e}")
            self.db.conn.rollback()

# Clase de conexión a la base de datos
class Database:
    def __init__(self, host, database, user, password):
        self.conn = psycopg2.connect(host=host, database=database, user=user, password=password)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise e

    def fetch_all(self):
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()
