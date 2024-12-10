from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox, QHBoxLayout,  QLineEdit
from PyQt5.QtCore import Qt
import psycopg2
import sys
import os

class DatabaseConnection:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="tu_db",
            user="tu_usuario",
            password="tu_contraseña",
            host="localhost"
        )
        self.cursor = self.connection.cursor()

class DelChoForm(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Choferes")
        self.setStyleSheet("font-size: 16px;")
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
                
                chofer_text = f"{row[0]} - {row[1]} {row[2]} {row[3]}"
                apodo_text = f'"{row[4]}"' if row[4] else ''

                chofer_label = QLabel(chofer_text)
                chofer_label.setStyleSheet("font-size: 16px;")
                chofer_label.setFixedHeight(25)

                apodo_label = QLabel(apodo_text)
                apodo_label.setStyleSheet("color: red; font-size: 16px;")
                apodo_label.setFixedHeight(25)

                delete_btn = QPushButton("ELIMINAR")
                delete_btn.setStyleSheet("background-color: rgb(255, 0, 0); font-size: 16px;")
                delete_btn.setFixedSize(100, 50)
                delete_btn.clicked.connect(lambda ch, row=row: self.inactivate_item(row[0], row[1], row[2], row[3]))
                
                item_layout.addWidget(chofer_label)
                item_layout.addWidget(apodo_label)
                item_layout.addWidget(delete_btn)
                
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

    def inactivate_item(self, item_id, nombre, apellido_paterno, apellido_materno):
        try:
            reply = QMessageBox.question(self, 'Inactivar Chofer', 
                                         '¿Estás seguro de que quieres inactivar este Chofer?', 
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Actualizar el estatus del chofer a 'INACTIVO'
                query_update = "UPDATE empleado_chofer SET estatus = 'INACTIVO' WHERE id_chofer = %s"
                self.db.cursor.execute(query_update, (item_id,))
                
                self.db.connection.commit()  # Confirmar la inactivación

                QMessageBox.information(self, 'Éxito', 'Chofer inactivado correctamente', QMessageBox.Ok)
                self.load_data()  # Recargar los datos después de la inactivación

        except psycopg2.Error as e:
            self.db.connection.rollback()  # Revertir los cambios si ocurre un error en la base de datos
            print(f"Error durante la inactivación del Chofer: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudo inactivar el Chofer: {e}', QMessageBox.Ok)
        except Exception as e:
            print(f"Error inesperado: {e}")
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
