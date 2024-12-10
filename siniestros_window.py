from PyQt5.QtWidgets import QMainWindow, qApp, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QTimeEdit, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QFileDialog, QTextEdit, QWidget, QApplication
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QDateTime, QDate
from PyQt5.QtWidgets import QListWidget

import os
import sys
import tempfile
import subprocess
import psycopg2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class SiniestrosWindow(QDialog):
    def __init__(self, db, parent=None):
        super(SiniestrosWindow, self).__init__(parent)
        self.setWindowTitle('Siniestros')
        self.db = db

        layout = QVBoxLayout()

        self.registrar_btn = QPushButton('Registrar Siniestro', self)
        self.registrar_btn.clicked.connect(self.registrar_siniestro)
        self.registrar_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.registrar_btn)

        self.ver_activos_btn = QPushButton('Ver Siniestros Activos / Cambiar Estatus', self)
        self.ver_activos_btn.clicked.connect(self.ver_siniestros_activos)
        self.ver_activos_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.ver_activos_btn)

        self.ver_todos_btn = QPushButton('Ver Siniestros', self)
        self.ver_todos_btn.clicked.connect(self.ver_siniestros)
        self.ver_todos_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.ver_todos_btn)

        self.imprimir_formato_btn = QPushButton('Imprimir Formato', self)
        self.imprimir_formato_btn.clicked.connect(self.imprimir_formato)
        self.imprimir_formato_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.imprimir_formato_btn)

        # Botón para buscar PDF por fecha
        self.buscar_pdf_btn = QPushButton('Buscar PDF', self)
        self.buscar_pdf_btn.clicked.connect(self.buscar_pdf_por_fecha)
        self.buscar_pdf_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.buscar_pdf_btn)

        self.setLayout(layout)

    def registrar_siniestro(self):
        dialog = RegistrarSiniestroForm(self.db, self)
        dialog.exec_()

    def ver_siniestros_activos(self):
        dialog = VerSiniestrosActivosForm(self.db, self)
        dialog.exec_()

    def ver_siniestros(self):
        dialog = VerSiniestrosForm(self.db, self)
        dialog.exec_()

    def imprimir_formato(self):
        dialog = SeleccionarFormatoDialog(self.db, self)
        dialog.exec_()

    def buscar_pdf_por_fecha(self):
        dialog = BuscarPDFPorFechaDialog(self.db, self)
        dialog.exec_()

class BuscarPDFPorFechaDialog(QDialog):
    def __init__(self, db, parent=None):
        super(BuscarPDFPorFechaDialog, self).__init__(parent)
        self.db = db
        self.setWindowTitle('Buscar PDF')
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Selector de fecha
        self.fecha_edit = QDateEdit(self)
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setDate(QDate.currentDate())
        layout.addWidget(QLabel('Selecciona la fecha del PDF:'))
        layout.addWidget(self.fecha_edit)

        # Lista de folios
        self.folios_list = QListWidget(self)
        layout.addWidget(QLabel('Folios encontrados:'))
        layout.addWidget(self.folios_list)

        # Botón de buscar
        self.buscar_btn = QPushButton('Buscar Folios', self)
        self.buscar_btn.clicked.connect(self.buscar_folios)
        self.buscar_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.buscar_btn)

        # Conexión al evento de selección en la lista
        self.folios_list.itemDoubleClicked.connect(self.abrir_pdf)

        self.setLayout(layout)

    def buscar_folios(self):
        """Busca folios para la fecha seleccionada y los muestra en la lista."""
        fecha_seleccionada = self.fecha_edit.date().toString('yyyy-MM-dd')
        query = "SELECT folio,  TO_CHAR(hora, 'HH24:MI:SS') AS hora_formateada, tipo FROM historial_siniestros WHERE fecha = %s"
        params = (fecha_seleccionada,)

        try:
            self.db.execute_query(query, params)
            result = self.db.fetch_all()

            if result:
                self.folios_list.clear()
                for row in result:
                    # Muestra folio, fecha y tipo juntos en una línea
                    folio = row[0]
                    hora = row[1]
                    tipo = row[2]
                    self.folios_list.addItem(f"Folio: {folio}, Hora: {hora}, Tipo: {tipo}")
            else:
                self.folios_list.clear()
                QMessageBox.warning(self, 'No encontrado', f'No se encontraron folios para la fecha {fecha_seleccionada}.')
        except Exception as e:
            self.db.connection.rollback()  # Revertir cambios si ocurre algún error
            print(f"Error al buscar los folios: {e}")
            QMessageBox.critical(self, 'Error', f'Error al buscar los folios: {e}')

    def abrir_pdf(self, item):
        """Abre el PDF asociado al folio seleccionado."""
        # Extrae solo el número del folio
        texto_item = item.text()
        try:
            folio_seleccionado = texto_item.split(",")[0].split(":")[1].strip()
        except IndexError:
            QMessageBox.critical(self, 'Error', 'El formato del folio seleccionado no es válido.')
            return

        query = "SELECT pdf FROM historial_siniestros WHERE folio = %s"
        params = (folio_seleccionado,)

        try:
            self.db.execute_query(query, params)
            result = self.db.fetch_all()

            if result:
                pdf_data = result[0][0]
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(pdf_data)
                    pdf_path = temp_file.name
                subprocess.run(["start", pdf_path], shell=True)
                QMessageBox.information(self, 'Éxito', f'PDF del folio {folio_seleccionado} encontrado y abierto.')
            else:
                QMessageBox.warning(self, 'No encontrado', f'No se encontró un PDF para el folio {folio_seleccionado}.')
        except Exception as e:
            self.db.connection.rollback()  # Revertir cambios si ocurre algún error
            print(f"Error al abrir el PDF: {e}")
            QMessageBox.critical(self, 'Error', f'Error al abrir el PDF: {e}')

class SeleccionarFormatoDialog(QDialog):
    def __init__(self, db, parent=None):
        super(SeleccionarFormatoDialog, self).__init__(parent)
        self.db = db  # Guarda la instancia de la base de datos
        self.setWindowTitle('Seleccionar Formato')
        self.resize(300, 100)

        layout = QVBoxLayout()

        self.formato_combo = QComboBox(self)
        self.formato_combo.addItems(['Pago', 'Reparación'])
        layout.addWidget(QLabel('Selecciona el tipo de formato:'))
        layout.addWidget(self.formato_combo)

        self.siguiente_btn = QPushButton('Siguiente', self)
        self.siguiente_btn.clicked.connect(self.siguiente)
        self.siguiente_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.siguiente_btn)

        self.setLayout(layout)

    def siguiente(self):
        tipo_formato = self.formato_combo.currentText()
        if tipo_formato == 'Pago':
            dialog = FormatoPagoDialog(self.db, self)
        else:
            dialog = FormatoReparacionDialog(self.db, self)
        dialog.exec_()
        self.close()

class FormatoPagoDialog(QDialog):
    def __init__(self, db, parent=None):
        super(FormatoPagoDialog, self).__init__(parent)
        self.db = db
        self.setWindowTitle('Recibo de Pago por Reparación de Daños')
        self.resize(400, 600)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.fecha_pago = QDateEdit(self)
        self.fecha_pago.setCalendarPopup(True)
        self.fecha_pago.setDate(QDate.currentDate())
        form_layout.addRow('Fecha del Pago:', self.fecha_pago)

        self.nombre_receptor = QLineEdit(self)
        form_layout.addRow('Nombre Afectado:', self.nombre_receptor)

        self.rol_receptor = QLineEdit(self)
        form_layout.addRow('Rol/Cargo:', self.rol_receptor)

        self.nombre_pagador = QLineEdit(self)
        form_layout.addRow('Nombre del Ejecutivo:', self.nombre_pagador)

        self.monto_letras = QLineEdit(self)
        form_layout.addRow('Monto en Letras:', self.monto_letras)

        self.monto_numeros = QLineEdit(self)
        form_layout.addRow('Monto en Números:', self.monto_numeros)

        self.fecha_incidente = QDateEdit(self)
        self.fecha_incidente.setCalendarPopup(True)
        self.fecha_incidente.setDate(QDate.currentDate())
        form_layout.addRow('Fecha del Incidente:', self.fecha_incidente)

        self.descripcion_dano = QTextEdit(self)
        form_layout.addRow('Descripción del Daño:', self.descripcion_dano)

        self.metodo_pago_combo = QComboBox(self)
        self.metodo_pago_combo.addItems(['Efectivo', 'Transferencia Bancaria'])
        form_layout.addRow('Método de Pago:', self.metodo_pago_combo)

        self.banco = QLineEdit(self)
        form_layout.addRow('Banco:', self.banco)

        self.numero_cuenta = QLineEdit(self)
        form_layout.addRow('Número de Cuenta:', self.numero_cuenta)

        self.fecha_transferencia = QDateEdit(self)
        self.fecha_transferencia.setCalendarPopup(True)
        self.fecha_transferencia.setDate(QDate.currentDate())
        form_layout.addRow('Fecha de la Transferencia:', self.fecha_transferencia)

        self.referencia_transferencia = QLineEdit(self)
        form_layout.addRow('Referencia de la Transferencia:', self.referencia_transferencia)

        self.observaciones = QTextEdit(self)
        form_layout.addRow('Observaciones:', self.observaciones)

        self.nombre_responsable_pago = QLineEdit(self)
        form_layout.addRow('Nombre del Ejecutivo a Pagar:', self.nombre_responsable_pago)

        layout.addLayout(form_layout)

        # Botón de Imprimir que guarda los datos automáticamente antes de imprimir
        self.imprimir_btn = QPushButton('Imprimir', self)
        self.imprimir_btn.clicked.connect(self.imprimir_y_guardar)
        self.imprimir_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.imprimir_btn)

        self.setLayout(layout)

    def guardar_datos(self):
        try:
            # Generar folio automáticamente
            query_folio = "SELECT nextval('folio_seq_ocho')"
            cursor = self.db.connection.cursor()  # Corrección aquí
            cursor.execute(query_folio)
            folio = cursor.fetchone()[0]

            # Obtener valores del formulario
            fecha_pago = self.fecha_pago.date().toString("yyyy-MM-dd")
            nombre_receptor = self.nombre_receptor.text()
            rol_receptor = self.rol_receptor.text()
            nombre_pagador = self.nombre_pagador.text()
            monto_letras = self.monto_letras.text()
            monto_numeros = float(self.monto_numeros.text()) if self.monto_numeros.text() else 0.0
            fecha_incidente = self.fecha_incidente.date().toString("yyyy-MM-dd")
            descripcion_dano = self.descripcion_dano.toPlainText()
            metodo_pago = self.metodo_pago_combo.currentText()
            banco = self.banco.text()
            numero_cuenta = int(self.numero_cuenta.text()) if self.numero_cuenta.text().isdigit() else None
            fecha_transferencia = self.fecha_transferencia.date().toString("yyyy-MM-dd")
            referencia_transferencia = self.referencia_transferencia.text()
            observaciones = self.observaciones.toPlainText()
            nombre_responsable_pago = self.nombre_responsable_pago.text()

            # Consulta de inserción
            query_insert = """
            INSERT INTO formato (
                folio, fecha_p, nombre_afectado, rol_car, nombre_ejecutivo, monto_l, monto_n,
                fecha_i, descripcion, metodo_pago, banco, num_cuenta, fecha_t, referencia_t, observaciones, nombre_ejecpag
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
            """

            # Ejecutar consulta de inserción
            cursor.execute(query_insert, (
                folio, fecha_pago, nombre_receptor, rol_receptor, nombre_pagador, monto_letras, monto_numeros,
                fecha_incidente, descripcion_dano, metodo_pago, banco, numero_cuenta, fecha_transferencia,
                referencia_transferencia, observaciones, nombre_responsable_pago
            ))

            # Confirmar la transacción
            self.db.connection.commit()
            cursor.close()  # Cerramos el cursor
            print("Datos guardados correctamente")
            QMessageBox.information(self, 'Éxito', 'Datos guardados correctamente.', QMessageBox.Ok)

        except Exception as e:
            print(f"Error al guardar los datos: {e}")
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al guardar los datos: {e}')

    def imprimir_y_guardar(self):
        # Guardar los datos antes de imprimir
        self.guardar_datos()
        # Llama a la función de impresión
        self.imprimir()

    def imprimir(self):
        # Obtener el folio del último registro relacionado
        try:
            query_folio = "SELECT COALESCE(MAX(folio), 0) FROM historial_siniestros"
            cursor = self.db.connection.cursor()
            cursor.execute(query_folio)
            folio = cursor.fetchone()[0]  # Obtener el valor del folio
            nuevo_folio = folio + 1  # Sumamos uno al folio
            folio_text = f"Folio: {nuevo_folio}"
        except Exception as e:
            folio_text = "Folio: Error"
            print(f"Error al obtener el folio: {e}")

        # Configuración del tamaño del ticket
        ticket_width = 48 * mm
        ticket_height = 200 * mm
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            c = canvas.Canvas(temp_file.name, pagesize=(ticket_width, ticket_height))
            # Agregar folio
            c.setFont("Helvetica-Bold", 6)
            y = ticket_height - 10 * mm  # Espacio inicial para el folio
            c.drawString(2 * mm, y, folio_text)
            y -= 15  # Reducir la posición para agregar el logo

            # Agregar logo
            logo_path = resource_path('resources/cotaxomil.jpg')
            if os.path.exists(logo_path):
                try:
                    c.drawImage(logo_path, 7 * mm, y - 20 * mm, width=30 * mm, height=20 * mm)
                    y -= 30
                except Exception as e:
                    print(f"Error al dibujar la imagen: {e}")
            y -= 40
            c.setFont("Helvetica-Bold", 5)
            c.drawString(2 * mm, y, "RECIBO DE PAGO SINIESTRO COTAXOMIL")
            y -= 10

            c.setFont("Helvetica", 5)
            c.drawString(1 * mm, y, f"Fecha: {self.fecha_pago.date().toString('dd/MM/yyyy')}")
            y -= 6

            c.drawString(1 * mm, y, f"Nombre del afectado: {self.nombre_receptor.text()}")
            y -= 6

            c.drawString(1 * mm, y, f"Rol del Ejecutivo: {self.rol_receptor.text()}")
            y -= 6

            c.drawString(1 * mm, y, f"Nombre del Pagador: {self.nombre_pagador.text()}")
            y -= 6

            c.drawString(1 * mm, y, f"Monto en Letras: {self.monto_letras.text()}")
            y -= 6

            c.drawString(1 * mm, y, f"Monto en Números: {self.monto_numeros.text()}")
            y -= 6

            c.drawString(1 * mm, y, f"Fecha del Incidente: {self.fecha_incidente.date().toString('dd/MM/yyyy')}")
            y -= 6

            # Ajustar el texto de la descripción del daño al tamaño del ticket
            descripcion_dano = self.descripcion_dano.toPlainText()
            max_width = ticket_width - 4 * mm  # Márgenes de 2 mm a cada lado
            styles = getSampleStyleSheet()
            styleN = ParagraphStyle('Normal', fontSize=5, leftIndent=2, rightIndent=2)
            p = Paragraph(descripcion_dano, styleN)
            width, height = p.wrap(max_width, y)
            p.drawOn(c, 2 * mm, y - height)
            y -= height + 6

            c.drawString(1 * mm, y, f"Método de Pago: {self.metodo_pago_combo.currentText()}")
            y -= 6

            if self.metodo_pago_combo.currentText() == 'Transferencia Bancaria':
                c.drawString(1 * mm, y, f"Banco: {self.banco.text()}")
                y -= 6
                c.drawString(1 * mm, y, f"Número de cuenta: {self.numero_cuenta.text()}")
                y -= 6
                c.drawString(1 * mm, y, f"Fecha de la Transferencia: {self.fecha_transferencia.date().toString('dd/MM/yyyy')}")
                y -= 6
                c.drawString(1 * mm, y, f"Referencia de la Transferencia: {self.referencia_transferencia.text()}")
                y -= 6

            # Ajustar el texto de las observaciones al tamaño del ticket
            observaciones = self.observaciones.toPlainText()
            p = Paragraph(observaciones, styleN)
            width, height = p.wrap(max_width, y)
            p.drawOn(c, 2 * mm, y - height)
            y -= height + 6

            c.drawString(1 * mm, y, f"Nombre del Afectado: {self.nombre_responsable_pago.text()}")
            y -= 6

            c.drawString(1 * mm, y, "Firma: ____________________________")
            y -= 10

            c.drawString(1 * mm, y, "Dirección de la Empresa:")
            y -= 6
            c.setFont("Helvetica", 4)
            c.drawString(1 * mm, y, "Camino antiguo a San Lucas 533, Talas de San Lorenzo,")
            y -= 5
            c.drawString(1 * mm, y, "Xochimilco, Ciudad de México, CP:16090, México")
            y -= 5
            c.drawString(1 * mm, y, "Teléfono: 00-00-00-00-00")

            c.save()

        with open(temp_file.name, 'rb') as file:
            pdf_data = file.read()

        try:
            query = """
            INSERT INTO historial_siniestros (fecha, hora, pdf, tipo)
            VALUES (CURRENT_DATE, CURRENT_TIME, %s, %s)
            """
            params = (psycopg2.Binary(pdf_data), 'Pago')
            self.db.execute_query(query, params)
            self.db.connection.commit()  # Confirmar la transacción
            QMessageBox.information(self, 'Éxito', 'El PDF de pago se ha guardado correctamente en la base de datos.')
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error al guardar el PDF en la base de datos: {e}")
            QMessageBox.critical(self, 'Error', f'Error al guardar el PDF: {e}')

        subprocess.run(["start", temp_file.name], shell=True)

class FormatoReparacionDialog(QDialog):
    def __init__(self, db, parent=None):
        super(FormatoReparacionDialog, self).__init__(parent)
        self.db = db
        self.setWindowTitle('Formato de Reparación')
        self.resize(400, 600)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.fecha_r = QDateEdit(self)
        self.fecha_r.setCalendarPopup(True)
        self.fecha_r.setDate(QDate.currentDate())
        form_layout.addRow('Fecha de Redacción:', self.fecha_r)

        self.nombre_afectado = QLineEdit(self)
        form_layout.addRow('Nombre del Afectado:', self.nombre_afectado)

        self.nombre_ejecutivo = QLineEdit(self)
        form_layout.addRow('Nombre del Ejecutivo:', self.nombre_ejecutivo)

        self.rol_car = QLineEdit(self)
        form_layout.addRow('Rol/Cargo:', self.rol_car)

        self.fecha_i = QDateEdit(self)
        self.fecha_i.setCalendarPopup(True)
        self.fecha_i.setDate(QDate.currentDate())
        form_layout.addRow('Fecha del Incidente:', self.fecha_i)

        self.descripcion = QTextEdit(self)
        form_layout.addRow('Descripción del Daño:', self.descripcion)

        self.plazo_reparacion = QDateEdit(self)
        self.plazo_reparacion.setCalendarPopup(True)
        self.plazo_reparacion.setDate(QDate.currentDate().addDays(7))
        form_layout.addRow('Plazo para la Reparación:', self.plazo_reparacion)

        self.condiciones_e = QTextEdit(self)
        form_layout.addRow('Condiciones Específicas:', self.condiciones_e)

        self.observaciones = QTextEdit(self)
        form_layout.addRow('Observaciones:', self.observaciones)

        layout.addLayout(form_layout)

        self.guardar_btn = QPushButton('Imprimir', self)
        self.guardar_btn.clicked.connect(self.imprimir_y_guardar)
        self.guardar_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.guardar_btn)

        self.setLayout(layout)

    def guardar_datos(self):
        try:
            # Generar folio automáticamente
            query_folio = "SELECT nextval('folio_seq_nueve')"
            cursor = self.db.connection.cursor()  # Corrección aquí
            cursor.execute(query_folio)
            folio = cursor.fetchone()[0]
            # Obtener valores del formulario
            fecha_r = self.fecha_r.date().toString("yyyy-MM-dd")
            nombre_ejecutivo = self.nombre_ejecutivo.text()
            rol_car = self.rol_car.text()
            fecha_i = self.fecha_i.date().toString("yyyy-MM-dd")
            descripcion = self.descripcion.toPlainText()
            plazo_reparacion = self.plazo_reparacion.date().toString("yyyy-MM-dd")
            condiciones_e = self.condiciones_e.toPlainText()
            observaciones = self.observaciones.toPlainText()
            nombre_afectado = self.nombre_afectado.text()

            # Consulta de inserción
            query_insert = """
            INSERT INTO formato_reparacion (
                fecha_r, nombre_ejecutivo, rol_car, fecha_i, descripcion,
                plazo_repacion, condiciones_e, observaciones, nombre_afectado
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
            """
            params = (
                fecha_r, nombre_ejecutivo, rol_car, fecha_i,
                descripcion, plazo_reparacion, condiciones_e, observaciones, nombre_afectado
            )

            # Ejecutar consulta de inserción
            cursor = self.db.connection.cursor()
            cursor.execute(query_insert, params)
            self.db.connection.commit()
            cursor.close()

            QMessageBox.information(self, 'Éxito', 'Formato de reparación guardado correctamente.', QMessageBox.Ok)
            self.close()

        except Exception as e:
            print(f"Error al guardar los datos: {e}")
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al guardar los datos: {e}')

    def imprimir_y_guardar(self):
        # Guardar los datos antes de imprimir
        self.guardar_datos()
        # Llama a la función de impresión
        self.imprimir()

    def imprimir(self):
        # Configuración del tamaño del ticket
        ticket_width = 48 * mm
        ticket_height = 200 * mm

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            c = canvas.Canvas(temp_file.name, pagesize=(ticket_width, ticket_height))

            # Añadir logo
            logo_path = resource_path('resources/cotaxomil.jpg')
            if os.path.exists(logo_path):
                try:
                    c.drawImage(logo_path, 5 * mm, ticket_height - 20 * mm, width=30 * mm, height=20 * mm)
                except Exception as e:
                    print(f"Error al dibujar la imagen: {e}")

            y = ticket_height - 30 * mm
            c.setFont("Helvetica-Bold", 5)
            c.drawString(1 * mm, y, "COMPROMISO DE REPARACIÓN DE DAÑOS")
            y -= 20

            c.setFont("Helvetica", 5)
            c.drawString(2 * mm, y, f"Fecha: {self.fecha_r.date().toString('dd/MM/yyyy')}")
            y -= 15

            c.drawString(2 * mm, y, f"Nombre del Afectado: {self.nombre_afectado.text()}")
            y -= 15

            c.drawString(2 * mm, y, f"Rol/Cargo: {self.rol_car.text()}")
            y -= 15

            c.drawString(2 * mm, y, f"Fecha del Incidente: {self.fecha_i.date().toString('dd/MM/yyyy')}")
            y -= 15

            # Ajustar el texto de la descripción del daño al tamaño del ticket
            descripcion = self.descripcion.toPlainText()
            max_width = ticket_width - 10 * mm  # Margen de 5 mm a cada lado
            styles = getSampleStyleSheet()
            styleN = ParagraphStyle('Normal', fontSize=5)
            p = Paragraph(descripcion, styleN)
            width, height = p.wrap(max_width, y)
            p.drawOn(c, 5 * mm, y - height)
            y -= height + 15

            c.drawString(2 * mm, y, f"Plazo para la Reparación: {self.plazo_reparacion.date().toString('dd/MM/yyyy')}")
            y -= 15

            # Ajustar el texto de condiciones específicas al tamaño del ticket
            condiciones = self.condiciones_e.toPlainText()
            p = Paragraph(condiciones, styleN)
            width, height = p.wrap(max_width, y)
            p.drawOn(c, 5 * mm, y - height)
            y -= height + 15

            # Ajustar el texto de las observaciones al tamaño del ticket
            observaciones = self.observaciones.toPlainText()
            p = Paragraph(observaciones, styleN)
            width, height = p.wrap(max_width, y)
            p.drawOn(c, 5 * mm, y - height)
            y -= height + 15

            c.drawString(2 * mm, y, "Firma: ____________________________")
            y -= 30

            c.drawString(2 * mm, y, f"Ejecutivo Responsable:")
            y -= 15
            c.drawString(2 * mm, y, f"Nombre: {self.nombre_ejecutivo.text()}")
            y -= 30
            c.drawString(2 * mm, y, "Firma: ____________________________")
            y -= 30

            c.drawString(2 * mm, y, "Dirección de la Empresa:")
            y -= 15
            c.drawString(2 * mm, y, "Camino antiguo a San Lucas 533 Talas de San Lorenzo")
            y -= 15
            c.drawString(2 * mm, y, "Xochimilco, Ciudad de México, CP:16090, México")
            y -= 15
            c.drawString(2 * mm, y, "Teléfono:00-00-00-00-00")

            c.save()

        with open(temp_file.name, 'rb') as file:
            pdf_data = file.read()

        try:
            query = """
            INSERT INTO historial_siniestros (fecha, hora, pdf, tipo)
            VALUES (CURRENT_DATE, CURRENT_TIME, %s, %s)
            """
            params = (psycopg2.Binary(pdf_data), 'Repa')
            self.db.execute_query(query, params)
            QMessageBox.information(self, 'Éxito', 'El PDF de reparación se ha guardado correctamente en la base de datos.')
        except Exception as e:
            print(f"Error al guardar el PDF en la base de datos: {e}")
            QMessageBox.critical(self, 'Error', f'Error al guardar el PDF: {e}')

        subprocess.run(["start", temp_file.name], shell=True)

class RegistrarSiniestroForm(QDialog):
    def __init__(self, db, parent=None):
        super(RegistrarSiniestroForm, self).__init__(parent)
        self.setWindowTitle('Registrar Siniestro')
        self.db = db

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.eco = QComboBox(self)
        self.populate_autobuses()
        form_layout.addRow('Económico:', self.eco)

        self.id_chofer = QComboBox(self)
        self.populate_choferes()
        form_layout.addRow('Chofer:', self.id_chofer)

        self.culpable = QCheckBox(self)
        form_layout.addRow('Culpable:', self.culpable)

        self.tipo_pago = QLineEdit(self)
        form_layout.addRow('Tipo de Pago:', self.tipo_pago)

        self.foto_general_btn = QHBoxLayout()
        self.foto_general_label = QLabel('No seleccionada')
        self.foto_general_select_btn = QPushButton('Seleccionar Foto General', self)
        self.foto_general_select_btn.clicked.connect(self.select_foto_general)
        self.foto_general_select_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_general_take_btn = QPushButton('Tomar Foto General', self)
        self.foto_general_take_btn.clicked.connect(self.take_foto_general)
        self.foto_general_take_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_general_btn.addWidget(self.foto_general_select_btn)
        self.foto_general_btn.addWidget(self.foto_general_take_btn)
        self.foto_general_btn.addWidget(self.foto_general_label)
        form_layout.addRow('Foto General:', self.foto_general_btn)

        self.foto_frontal_btn = QHBoxLayout()
        self.foto_frontal_label = QLabel('No seleccionada')
        self.foto_frontal_select_btn = QPushButton('Seleccionar Foto Frontal', self)
        self.foto_frontal_select_btn.clicked.connect(self.select_foto_frontal)
        self.foto_frontal_select_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_frontal_take_btn = QPushButton('Tomar Foto Frontal', self)
        self.foto_frontal_take_btn.clicked.connect(self.take_foto_frontal)
        self.foto_frontal_take_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_frontal_btn.addWidget(self.foto_frontal_select_btn)
        self.foto_frontal_btn.addWidget(self.foto_frontal_take_btn)
        self.foto_frontal_btn.addWidget(self.foto_frontal_label)
        form_layout.addRow('Foto Frontal:', self.foto_frontal_btn)

        self.foto_trasera_btn = QHBoxLayout()
        self.foto_trasera_label = QLabel('No seleccionada')
        self.foto_trasera_select_btn = QPushButton('Seleccionar Foto Trasera', self)
        self.foto_trasera_select_btn.clicked.connect(self.select_foto_trasera)
        self.foto_trasera_select_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_trasera_take_btn = QPushButton('Tomar Foto Trasera', self)
        self.foto_trasera_take_btn.clicked.connect(self.take_foto_trasera)
        self.foto_trasera_take_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_trasera_btn.addWidget(self.foto_trasera_select_btn)
        self.foto_trasera_btn.addWidget(self.foto_trasera_take_btn)
        self.foto_trasera_btn.addWidget(self.foto_trasera_label)
        form_layout.addRow('Foto Trasera:', self.foto_trasera_btn)

        self.foto_lateral_izquierdo_btn = QHBoxLayout()
        self.foto_lateral_izquierdo_label = QLabel('No seleccionada')
        self.foto_lateral_izquierdo_select_btn = QPushButton('Seleccionar Foto Lateral Izquierdo', self)
        self.foto_lateral_izquierdo_select_btn.clicked.connect(self.select_foto_lateral_izquierdo)
        self.foto_lateral_izquierdo_select_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_lateral_izquierdo_take_btn = QPushButton('Tomar Foto Lateral Izquierdo', self)
        self.foto_lateral_izquierdo_take_btn.clicked.connect(self.take_foto_lateral_izquierdo)
        self.foto_lateral_izquierdo_take_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_lateral_izquierdo_btn.addWidget(self.foto_lateral_izquierdo_select_btn)
        self.foto_lateral_izquierdo_btn.addWidget(self.foto_lateral_izquierdo_take_btn)
        self.foto_lateral_izquierdo_btn.addWidget(self.foto_lateral_izquierdo_label)
        form_layout.addRow('Foto Lateral Izquierdo:', self.foto_lateral_izquierdo_btn)

        self.foto_lateral_derecho_btn = QHBoxLayout()
        self.foto_lateral_derecho_label = QLabel('No seleccionada')
        self.foto_lateral_derecho_select_btn = QPushButton('Seleccionar Foto Lateral Derecho', self)
        self.foto_lateral_derecho_select_btn.clicked.connect(self.select_foto_lateral_derecho)
        self.foto_lateral_derecho_select_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_lateral_derecho_take_btn = QPushButton('Tomar Foto Lateral Derecho', self)
        self.foto_lateral_derecho_take_btn.clicked.connect(self.take_foto_lateral_derecho)
        self.foto_lateral_derecho_take_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        self.foto_lateral_derecho_btn.addWidget(self.foto_lateral_derecho_select_btn)
        self.foto_lateral_derecho_btn.addWidget(self.foto_lateral_derecho_take_btn)
        self.foto_lateral_derecho_btn.addWidget(self.foto_lateral_derecho_label)
        form_layout.addRow('Foto Lateral Derecho:', self.foto_lateral_derecho_btn)

        self.descripcion = QTextEdit(self)
        form_layout.addRow('Descripción:', self.descripcion)

        self.submit_btn = QPushButton('Registrar', self)
        self.submit_btn.clicked.connect(self.registrar)
        self.submit_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        form_layout.addRow(self.submit_btn)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def populate_autobuses(self):
        query = "SELECT eco FROM Autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"
        self.db.execute_query(query)
        autobuses = self.db.fetch_all()
        for autobus in autobuses:
            self.eco.addItem(str(autobus[0]), autobus[0])

    def populate_choferes(self):
        query = "SELECT id_chofer, nombre, apellido_paterno, apellido_materno FROM Empleado_Chofer WHERE estatus = 'ACTIVO' ORDER BY id_chofer ASC"
        self.db.execute_query(query)
        choferes = self.db.fetch_all()
        for chofer in choferes:
            self.id_chofer.addItem(f"{chofer[0]} - {chofer[1]} {chofer[2]} {chofer[3]}", chofer[0])

    def select_foto_general(self):
        self.foto_general_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto General", "", "Images (*.png *.xpm *.jpg)")
        if self.foto_general_path:
            self.foto_general_label.setText(os.path.basename(self.foto_general_path))

    def take_foto_general(self):
        os.system('start microsoft.windows.camera:')

    def select_foto_frontal(self):
        self.foto_frontal_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto Frontal", "", "Images (*.png *.xpm *.jpg)")
        if self.foto_frontal_path:
            self.foto_frontal_label.setText(os.path.basename(self.foto_frontal_path))

    def take_foto_frontal(self):
        os.system('start microsoft.windows.camera:')

    def select_foto_trasera(self):
        self.foto_trasera_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto Trasera", "", "Images (*.png *.xpm *.jpg)")
        if self.foto_trasera_path:
            self.foto_trasera_label.setText(os.path.basename(self.foto_trasera_path))

    def take_foto_trasera(self):
        os.system('start microsoft.windows.camera:')

    def select_foto_lateral_izquierdo(self):
        self.foto_lateral_izquierdo_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto Lateral Izquierdo", "", "Images (*.png *.xpm *.jpg)")
        if self.foto_lateral_izquierdo_path:
            self.foto_lateral_izquierdo_label.setText(os.path.basename(self.foto_lateral_izquierdo_path))

    def take_foto_lateral_izquierdo(self):
        os.system('start microsoft.windows.camera:')

    def select_foto_lateral_derecho(self):
        self.foto_lateral_derecho_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto Lateral Derecho", "", "Images (*.png *.xpm *.jpg)")
        if self.foto_lateral_derecho_path:
            self.foto_lateral_derecho_label.setText(os.path.basename(self.foto_lateral_derecho_path))

    def take_foto_lateral_derecho(self):
        os.system('start microsoft.windows.camera:')

    def registrar(self):
        eco = self.eco.currentText()
        id_chofer = self.id_chofer.currentData()
        culpable = self.culpable.isChecked()
        tipo_pago = self.tipo_pago.text()
        descripcion = self.descripcion.toPlainText()
        estatus = 'ACTIVA'

        # Load images
        foto_general = self.load_image(self.foto_general_path)
        foto_frontal = self.load_image(self.foto_frontal_path)
        foto_trasera = self.load_image(self.foto_trasera_path)
        foto_lateral_izquierdo = self.load_image(self.foto_lateral_izquierdo_path)
        foto_lateral_derecho = self.load_image(self.foto_lateral_derecho_path)

        query = """
        INSERT INTO Siniestros (fecha, hora, eco, id_chofer, culpable, tipo_pago, foto_general, foto_frontal, foto_trasera, foto_lateral_izquierdo, foto_lateral_derecho, descripcion, estatus)
        VALUES (CURRENT_DATE, CURRENT_TIME, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (eco, id_chofer, culpable, tipo_pago, foto_general, foto_frontal, foto_trasera, foto_lateral_izquierdo, foto_lateral_derecho, descripcion, estatus)

        try:
            self.db.execute_query(query, params)
            QMessageBox.information(self, 'Éxito', 'Siniestro registrado exitosamente.')
            self.close()
        except Exception as e:
            print(f"Error al registrar siniestro: {e}")
            QMessageBox.critical(self, 'Error', f'Error al registrar siniestro: {e}')

    def load_image(self, image_path):
        if image_path:
            with open(image_path, 'rb') as file:
                return file.read()
        return None

class VerSiniestrosActivosForm(QDialog):
    def __init__(self, db, parent=None):
        super(VerSiniestrosActivosForm, self).__init__(parent)
        self.setWindowTitle('Ver Siniestros Activos / Cambiar Estatus')
        self.db = db

        layout = QVBoxLayout()

        self.table = QTableWidget(self)
        layout.addWidget(self.table)

        self.load_data()

        self.setLayout(layout)

    def load_data(self):
        query = "SELECT folio, eco, fecha FROM Siniestros WHERE estatus = 'ACTIVA' ORDER BY eco ASC"
        self.db.execute_query(query)
        siniestros = self.db.fetch_all()

        self.table.setRowCount(len(siniestros))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Folio', 'Económico', 'Fecha'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row_num, siniestro in enumerate(siniestros):
            self.table.setItem(row_num, 0, QTableWidgetItem(str(siniestro[0])))
            self.table.setItem(row_num, 1, QTableWidgetItem(str(siniestro[1])))
            self.table.setItem(row_num, 2, QTableWidgetItem(str(siniestro[2])))

        self.table.cellDoubleClicked.connect(self.change_status)

    def change_status(self, row, column):
        folio = self.table.item(row, 0).text()
        new_status, ok = QInputDialog.getItem(self, 'Cambiar Estatus', 'Seleccionar nuevo estatus:', ['ACTIVA', 'RESUELTO'], editable=False)
        if ok:
            query = "UPDATE Siniestros SET estatus = %s WHERE folio = %s"
            params = (new_status, folio)
            try:
                self.db.execute_query(query, params)
                self.db.connection.commit()
                QMessageBox.information(self, 'Éxito', 'Estatus actualizado exitosamente.')
                self.load_data()
            except Exception as e:
                self.db.connection.rollback()
                print(f"Error al actualizar estatus: {e}")
                QMessageBox.critical(self, 'Error', f'Error al actualizar estatus: {e}')

class VerSiniestrosForm(QDialog):
    def __init__(self, db, parent=None):
        super(VerSiniestrosForm, self).__init__(parent)
        self.setWindowTitle('Ver Siniestros')
        self.db = db

        layout = QVBoxLayout()

        self.status_combo = QComboBox(self)
        self.status_combo.addItems(['ACTIVA', 'RESUELTO'])
        layout.addWidget(self.status_combo)

        self.load_btn = QPushButton('Cargar Siniestros', self)
        self.load_btn.clicked.connect(self.load_siniestros)
        self.load_btn.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(self.load_btn)

        self.table = QTableWidget(self)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_siniestros(self):
        estatus = self.status_combo.currentText()
        query = "SELECT folio, eco, fecha FROM Siniestros WHERE estatus = %s"
        self.db.execute_query(query, (estatus,))
        siniestros = self.db.fetch_all()

        self.table.setRowCount(len(siniestros))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Folio', 'Económico', 'Fecha'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row_num, siniestro in enumerate(siniestros):
            self.table.setItem(row_num, 0, QTableWidgetItem(str(siniestro[0])))
            self.table.setItem(row_num, 1, QTableWidgetItem(str(siniestro[1])))
            self.table.setItem(row_num, 2, QTableWidgetItem(str(siniestro[2])))

        self.table.cellDoubleClicked.connect(self.view_details)

    def view_details(self, row, column):
        folio = self.table.item(row, 0).text()
        query = """
        SELECT fecha, hora, eco, id_chofer, culpable, tipo_pago, foto_general, foto_frontal, foto_trasera, foto_lateral_izquierdo, foto_lateral_derecho, descripcion, estatus
        FROM Siniestros WHERE folio = %s
        """
        self.db.execute_query(query, (folio,))
        siniestro = self.db.fetch_all()[0]

        details_dialog = QDialog(self)
        details_dialog.setWindowTitle(f"Siniestro {folio}")

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.addRow("Fecha:", QLabel(str(siniestro[0])))
        form_layout.addRow("Hora:", QLabel(str(siniestro[1])))
        form_layout.addRow("Económico:", QLabel(str(siniestro[2])))
        form_layout.addRow("ID Chofer:", QLabel(str(siniestro[3])))
        form_layout.addRow("Culpable:", QLabel("Sí" if siniestro[4] else "No"))
        form_layout.addRow("Tipo de Pago:", QLabel(str(siniestro[5])))
        form_layout.addRow("Descripción:", QLabel(siniestro[11]))
        form_layout.addRow("Estatus:", QLabel(siniestro[12]))

        layout.addLayout(form_layout)

        photo_layout = QHBoxLayout()
        photos = [siniestro[6], siniestro[7], siniestro[8], siniestro[9], siniestro[10]]
        for photo in photos:
            if photo:
                label = QLabel(self)
                pixmap = QPixmap()
                pixmap.loadFromData(photo)
                label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
                label.mousePressEvent = lambda event, p=pixmap: self.show_full_image(p)
                photo_layout.addWidget(label)

        layout.addLayout(photo_layout)

        close_button = QPushButton('Cerrar', details_dialog)
        close_button.clicked.connect(details_dialog.accept)
        close_button.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(close_button)

        details_dialog.setLayout(layout)
        details_dialog.exec_()

    def show_full_image(self, pixmap):
        image_dialog = QDialog(self)
        image_dialog.setWindowTitle("Imagen Completa")

        layout = QVBoxLayout()
        label = QLabel(self)
        label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
        layout.addWidget(label)

        close_button = QPushButton('Cerrar', image_dialog)
        close_button.clicked.connect(image_dialog.accept)
        close_button.setStyleSheet("background-color: rgb(111, 108, 120);")
        layout.addWidget(close_button)

        image_dialog.setLayout(layout)
        image_dialog.exec_()
