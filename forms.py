from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QPushButton, QDialog, QLabel, QTimeEdit, QInputDialog, QMessageBox
from PyQt5.QtCore import QDate, QDateTime
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class AddBusForm(QWidget):
    def __init__(self, parent=None):
        super(AddBusForm, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Autobus')
        self.resize(400, 300)

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.eco = QLineEdit(self)
        form_layout.addRow('ECO:', self.eco)

        self.placa = QLineEdit(self)
        form_layout.addRow('Placa:', self.placa)

        self.numero_serie = QLineEdit(self)
        form_layout.addRow('Número de Serie:', self.numero_serie)

        self.numero_motor = QLineEdit(self)
        form_layout.addRow('Número de Motor:', self.numero_motor)

        self.fecha_vigencia_seguro = QDateEdit(self)
        self.fecha_vigencia_seguro.setCalendarPopup(True)
        self.fecha_vigencia_seguro.setDate(QDate.currentDate())
        form_layout.addRow('Fecha Vigencia Seguro:', self.fecha_vigencia_seguro)

        self.nombre_aseguradora = QLineEdit(self)
        form_layout.addRow('Nombre de la Aseguradora:', self.nombre_aseguradora)

        self.tipo = QComboBox(self)
        self.tipo.addItems(['TORETO', 'ZAFIRO'])
        form_layout.addRow('Tipo:', self.tipo)

        self.submit_btn = QPushButton('Agregar', self)
        self.submit_btn.setStyleSheet("background-color: rgb(112, 163, 140)")
        form_layout.addRow(self.submit_btn)

        layout.addLayout(form_layout)
        self.setLayout(layout)

class JornadaEntradaForm(QDialog):
    def __init__(self, db, parent=None):
        super(JornadaEntradaForm, self).__init__(parent)
        self.setWindowTitle('Iniciar Jornada')
        self.db = db

        layout = QVBoxLayout()

        self.id_chofer = QComboBox(self)
        self.populate_choferes()
        layout.addWidget(QLabel('Chofer:'))
        layout.addWidget(self.id_chofer)

        self.fecha_entrada = QDateEdit(self)
        self.fecha_entrada.setDate(QDateTime.currentDateTime().date())
        self.fecha_entrada.setEnabled(False)
        layout.addWidget(QLabel('Fecha de Entrada:'))
        layout.addWidget(self.fecha_entrada)

        self.hora_entrada = QTimeEdit(self)
        self.hora_entrada.setTime(QDateTime.currentDateTime().time())
        self.hora_entrada.setEnabled(False)
        layout.addWidget(QLabel('Hora de Entrada:'))
        layout.addWidget(self.hora_entrada)

        self.eco = QComboBox(self)
        self.populate_autobuses()
        layout.addWidget(QLabel('Económico:'))
        layout.addWidget(self.eco)

        self.kilometraje_entrada = QLineEdit(self)
        self.kilometraje_entrada.setPlaceholderText('Kilometraje de Entrada')
        layout.addWidget(QLabel('Kilometraje de Entrada:'))
        layout.addWidget(self.kilometraje_entrada)

        self.diesel_entrada = QLineEdit(self)
        self.diesel_entrada.setPlaceholderText('Diesel de Entrada (%)')
        layout.addWidget(QLabel('Diesel de Entrada (%):'))
        layout.addWidget(self.diesel_entrada)

        self.aceite_entrada = QLineEdit(self)
        self.aceite_entrada.setPlaceholderText('Aceite de Entrada')
        layout.addWidget(QLabel('Aceite de Entrada:'))
        layout.addWidget(self.aceite_entrada)

        self.adblue_entrada = QLineEdit(self)
        self.adblue_entrada.setPlaceholderText('Adblue de Entrada')
        layout.addWidget(QLabel('Adblue de Entrada:'))
        layout.addWidget(self.adblue_entrada)

        self.submit_btn = QPushButton('Iniciar Jornada', self)
        self.submit_btn.clicked.connect(self.iniciar_jornada)
        self.submit_btn.setStyleSheet("background-color: rgb(112, 163, 140);")
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)

    def iniciar_jornada(self):
        try:
            id_chofer = self.id_chofer.currentData()
            fecha_entrada = self.fecha_entrada.date().toString('yyyy-MM-dd')
            hora_entrada = self.hora_entrada.time().toString()
            eco = self.eco.currentData()
            kilometraje_entrada = self.kilometraje_entrada.text()
            diesel_entrada_porcentaje = self.diesel_entrada.text()
            aceite_entrada = self.aceite_entrada.text()
            adblue_entrada = self.adblue_entrada.text()

            # Validaciones
            if not kilometraje_entrada.isdigit():
                raise ValueError("El kilometraje de entrada debe ser un número.")
            if diesel_entrada_porcentaje and not diesel_entrada_porcentaje.replace('.', '', 1).isdigit():
                raise ValueError("El porcentaje de diesel de entrada debe ser un número.")
            # Eliminamos la validación de aceite_entrada
            if adblue_entrada and not adblue_entrada.replace('.', '', 1).isdigit():
                raise ValueError("El adblue de entrada debe ser un número.")

            # Verificar si ya existe un registro para el mismo chofer en la misma fecha
            check_query = """
            SELECT COUNT(*) FROM Historial_Jornada_Entrada
            WHERE id_chofer = %s AND fecha_entrada = %s
            """
            self.db.execute_query(check_query, (id_chofer, fecha_entrada))
            count = self.db.fetch_all()[0][0]

            if count > 0:
                QMessageBox.warning(self, 'Advertencia', 'El chofer ya tiene una jornada iniciada para el día de hoy.')
                return

            # Obtener el tipo de autobús y la capacidad del tanque
            query_tanque = "SELECT tipo, tanque_litros FROM Autobus WHERE eco = %s"
            self.db.execute_query(query_tanque, (eco,))
            autobus = self.db.fetch_all()[0]
            tipo = autobus[0]
            tanque_litros = autobus[1]

            # Convertir el porcentaje de diesel a litros
            try:
                diesel_entrada_litros = (float(diesel_entrada_porcentaje) / 100) * tanque_litros if diesel_entrada_porcentaje else 0
            except ValueError:
                QMessageBox.warning(self, 'Advertencia', 'El porcentaje de diesel de entrada no es un número válido.')
                return

            query = """
            INSERT INTO Historial_Jornada_Entrada (id_chofer, fecha_entrada, hora_entrada, eco, kilometraje_entrada, diesel_entrada, aceite_entrada, adblue_entrada)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING folio
            """
            params = (id_chofer, fecha_entrada, hora_entrada, eco, kilometraje_entrada, diesel_entrada_litros, aceite_entrada, adblue_entrada)

            self.db.execute_query(query, params)
            folio = self.db.fetch_all()[0][0]
            QMessageBox.information(self, 'Éxito', f'Jornada iniciada exitosamente. Folio: {folio}')
            self.close()
        except ValueError as e:
            QMessageBox.warning(self, 'Advertencia', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al iniciar la jornada: {e}')

    def populate_choferes(self):
        query = """
        SELECT id_chofer, nombre, apellido_paterno, apellido_materno
        FROM Empleado_Chofer
        WHERE estatus = 'ACTIVO' AND fecha_vencimiento_tarjeton >= CURRENT_DATE
        ORDER BY id_chofer ASC
        """
        try:
            self.db.execute_query(query)
            choferes = self.db.fetch_all()
            print("Choferes encontrados:", choferes)  # Agregado para depuración
            if choferes:
                for chofer in choferes:
                    self.id_chofer.addItem(f"{chofer[0]} - {chofer[1]} {chofer[2]} {chofer[3]}", chofer[0])
            else:
                QMessageBox.warning(self, 'Advertencia', 'No se encontraron choferes con tarjetón vigente.')
        except Exception as e:
            print(f"Error al poblar choferes: {e}")
            QMessageBox.critical(self, 'Error', f"Error al poblar choferes: {e}")

    def populate_autobuses(self):
        query = "SELECT eco FROM Autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC" 
        try:
            self.db.execute_query(query)
            autobuses = self.db.fetch_all()
            print("Autobuses encontrados:", autobuses)  # Agregado para depuración
            if autobuses:
                for autobus in autobuses:
                    self.eco.addItem(str(autobus[0]), autobus[0])
            else:
                QMessageBox.warning(self, 'Advertencia', 'No se encontraron autobuses registrados.')
        except Exception as e:
            print(f"Error al poblar autobuses: {e}")
            QMessageBox.critical(self, 'Error', f"Error al poblar autobuses: {e}")

class JornadaSalidaForm(QDialog):
    def __init__(self, db, folio, parent=None):
        super(JornadaSalidaForm, self).__init__(parent)
        self.setWindowTitle('Terminar Jornada')
        self.db = db
        self.folio = folio

        layout = QVBoxLayout()

        self.fecha_salida = QDateEdit(self)
        self.fecha_salida.setDate(QDateTime.currentDateTime().date())
        self.fecha_salida.setEnabled(False)
        layout.addWidget(QLabel('Fecha de Salida:'))
        layout.addWidget(self.fecha_salida)

        self.hora_salida = QTimeEdit(self)
        self.hora_salida.setTime(QDateTime.currentDateTime().time())
        self.hora_salida.setEnabled(False)
        layout.addWidget(QLabel('Hora de Salida:'))
        layout.addWidget(self.hora_salida)

        self.kilometraje_salida = QLineEdit(self)
        self.kilometraje_salida.setPlaceholderText('Kilometraje de Salida')
        layout.addWidget(QLabel('Kilometraje de Salida:'))
        layout.addWidget(self.kilometraje_salida)

        self.diesel_salida = QLineEdit(self)
        self.diesel_salida.setPlaceholderText('Diesel de Salida (%)')
        layout.addWidget(QLabel('Diesel de Salida (%):'))
        layout.addWidget(self.diesel_salida)

        self.aceite_salida = QLineEdit(self)
        self.aceite_salida.setPlaceholderText('Aceite de Salida')
        layout.addWidget(QLabel('Aceite de Salida:'))
        layout.addWidget(self.aceite_salida)

        self.adblue_salida = QLineEdit(self)
        self.adblue_salida.setPlaceholderText('Adblue de Salida')
        layout.addWidget(QLabel('Adblue de Salida:'))
        layout.addWidget(self.adblue_salida)

        self.submit_btn = QPushButton('Terminar Jornada', self)
        self.submit_btn.clicked.connect(self.terminar_jornada)
        self.submit_btn.setStyleSheet("background-color: rgb(112, 163, 140);")
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)

    def terminar_jornada(self):
        fecha_salida = self.fecha_salida.date().toString('yyyy-MM-dd')
        hora_salida = self.hora_salida.time().toString()
        kilometraje_salida = self.kilometraje_salida.text()
        diesel_salida_porcentaje = self.diesel_salida.text()
        aceite_salida = self.aceite_salida.text()
        adblue_salida = self.adblue_salida.text()

        # Obtener el tipo de autobús y la capacidad del tanque
        query_tanque = "SELECT tipo, tanque_litros FROM Autobus WHERE eco = (SELECT eco FROM Historial_Jornada_Entrada WHERE folio = %s)"
        self.db.execute_query(query_tanque, (self.folio,))
        autobus = self.db.fetch_all()[0]
        tipo = autobus[0]
        tanque_litros = autobus[1]

        # Convertir el porcentaje de diesel a litros
        if diesel_salida_porcentaje:
            diesel_salida_litros = (float(diesel_salida_porcentaje) / 100) * tanque_litros
        else:
            diesel_salida_litros = 0

        query_salida = """
        INSERT INTO Historial_Jornada_Salida (folio, fecha_salida, hora_salida, kilometraje_salida, diesel_salida, aceite_salida, adblue_salida)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params_salida = (self.folio, fecha_salida, hora_salida, kilometraje_salida, diesel_salida_litros, aceite_salida, adblue_salida)

        try:
            self.db.execute_query(query_salida, params_salida)
            QMessageBox.information(self, 'Éxito', 'Jornada terminada exitosamente.')
            self.close()
        except Exception as e:
            print(f"Error al terminar la jornada: {e}")
            QMessageBox.critical(self, 'Error', f'Error al terminar la jornada: {e}')

class InfoForm(QDialog):
    def __init__(self, db, parent=None):
        super(InfoForm, self).__init__(parent)
        self.setWindowTitle('Ver Información')
        self.db = db

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.chofer_combo = QComboBox(self)
        self.populate_choferes()
        form_layout.addRow('Seleccionar Chofer:', self.chofer_combo)

        self.eco_combo = QComboBox(self)
        self.populate_economicos()
        form_layout.addRow('Seleccionar Económico:', self.eco_combo)

        layout.addLayout(form_layout)

        self.submit_chofer_btn = QPushButton('Ver por Chofer', self)
        self.submit_chofer_btn.clicked.connect(self.ver_por_chofer)
        self.submit_chofer_btn.setStyleSheet("background-color: rgb(112, 163, 140);")
        layout.addWidget(self.submit_chofer_btn)

        self.submit_eco_btn = QPushButton('Ver por Económico', self)
        self.submit_eco_btn.clicked.connect(self.ver_por_eco)
        self.submit_eco_btn.setStyleSheet("background-color: rgb(112, 163, 140);")
        layout.addWidget(self.submit_eco_btn)

        self.setLayout(layout)

    def populate_choferes(self):
        query = "SELECT id_chofer, nombre, apellido_paterno, apellido_materno FROM Empleado_Chofer WHERE estatus = 'ACTIVO' ORDER BY id_chofer ASC"
        try:
            self.db.execute_query(query)
            choferes = self.db.fetch_all()
            for chofer in choferes:
                self.chofer_combo.addItem(f"{chofer[0]} - {chofer[1]} {chofer[2]} {chofer[3]}", chofer[0])
        except Exception as e:
            print(f"Error al poblar choferes: {e}")
            QMessageBox.critical(self, 'Error', f"Error al poblar choferes: {e}")

    def populate_economicos(self):
        query = "SELECT eco FROM Autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"
        try:
            self.db.execute_query(query)
            economicos = self.db.fetch_all()
            for eco in economicos:
                self.eco_combo.addItem(str(eco[0]), eco[0])
        except Exception as e:
            print(f"Error al poblar económicos: {e}")
            QMessageBox.critical(self, 'Error', f"Error al poblar económicos: {e}")

    def ver_por_chofer(self):
        id_chofer = self.chofer_combo.currentData()
        query = """
        SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, a.apodo, e.foto_chofer, h.hora_entrada, h.eco, h.folio
        FROM Historial_Jornada_Entrada h
        JOIN Empleado_Chofer e ON h.id_chofer = e.id_chofer
        LEFT JOIN Apodos a ON e.id_chofer = a.id_chofer
        WHERE e.id_chofer = %s AND h.fecha_entrada = CURRENT_DATE ORDER BY e.id_chofer ASC
        """
        try:
            self.db.execute_query(query, (id_chofer,))
            results = self.db.fetch_all()
            if results:
                result = results[0]
                self.show_info(result)
            else:
                QMessageBox.information(self, 'Sin resultados', 'No se encontraron datos para el chofer seleccionado.')
        except Exception as e:
            print(f"Error al consultar por chofer: {e}")
            QMessageBox.critical(self, 'Error', f'Error al consultar la información: {e}')

    def ver_por_eco(self):
        eco = self.eco_combo.currentData()
        query = """
        SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, a.apodo, e.foto_chofer, h.hora_entrada, h.eco, h.folio
        FROM Historial_Jornada_Entrada h
        JOIN Empleado_Chofer e ON h.id_chofer = e.id_chofer
        LEFT JOIN Apodos a ON e.id_chofer = a.id_chofer
        WHERE h.eco = %s AND h.fecha_entrada = CURRENT_DATE ORDER BY h.eco ASC
        """
        try:
            self.db.execute_query(query, (eco,))
            results = self.db.fetch_all()
            if results:
                result = results[0]
                self.show_info(result)
            else:
                QMessageBox.information(self, 'Sin resultados', 'No se encontraron datos para el económico seleccionado.')
        except Exception as e:
            print(f"Error al consultar por económico: {e}")
            QMessageBox.critical(self, 'Error', f'Error al consultar la información: {e}')

    def show_info(self, result):
        id_chofer, nombre, apellido_paterno, apellido_materno, apodo, foto_chofer, hora_entrada, eco, folio = result

        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("Información del Chofer")

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.addRow("ID Chofer:", QLabel(str(id_chofer)))
        form_layout.addRow("Nombre:", QLabel(nombre))
        form_layout.addRow("Apellido Paterno:", QLabel(apellido_paterno))
        form_layout.addRow("Apellido Materno:", QLabel(apellido_materno))
        form_layout.addRow("Apodo:", QLabel(apodo if apodo else "N/A"))
        form_layout.addRow("Hora de Entrada:", QLabel(str(hora_entrada)))
        form_layout.addRow("Económico:", QLabel(str(eco)))
        form_layout.addRow("Folio:", QLabel(str(folio)))

        if foto_chofer:
            foto_label = QLabel(self)
            pixmap = QPixmap()
            pixmap.loadFromData(foto_chofer)
            foto_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            form_layout.addRow("Foto del Chofer:", foto_label)

        layout.addLayout(form_layout)

        close_button = QPushButton('Cerrar', info_dialog)
        close_button.clicked.connect(info_dialog.accept)
        close_button.setStyleSheet("background-color: rgb(112, 163, 140);")
        layout.addWidget(close_button)

        info_dialog.setLayout(layout)
        info_dialog.exec_()
