from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
import psycopg2

class Create_User(QWidget):
    def __init__(self, db, parent=None):
        super(Create_User, self).__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Usuario')
        self.resize(400, 300)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.username = QLineEdit(self)
        form_layout.addRow('Nombre de Usuario:', self.username)

        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)  # Ocultar la contraseña
        form_layout.addRow('Contraseña:', self.password)

        # Obtener los roles desde la base de datos
        self.roles = self.fetch_roles()

        self.role_checkboxes = []
        for role in self.roles:
            checkbox = QCheckBox(role, self)
            self.role_checkboxes.append(checkbox)
            form_layout.addRow(checkbox)

        self.submit_btn = QPushButton('Agregar Usuario', self)
        self.submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(self.submit_btn)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def fetch_roles(self):
        try:
            # Lista de roles específicos que deseas mostrar
            specific_roles = [
                'administracion', 'checadores', 'diesel', 'electro_mecanica',
                'recaudo', 'siniestros', 'system', 'golpes', 'tele'
            ]
            
            # Convertir la lista de roles a una cadena de texto para usar en la consulta
            roles_list = ", ".join(f"'{role}'" for role in specific_roles)

            # Consulta para seleccionar solo los roles específicos
            query = f"""
            SELECT rolname 
            FROM pg_catalog.pg_roles 
            WHERE rolname IN ({roles_list})
            """
            
            self.db.cursor.execute(query)
            roles = [row[0] for row in self.db.cursor.fetchall()]
            return roles
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'No se pudieron obtener los roles: {e}', QMessageBox.Ok)
            return []
    def submit_form(self):
        try:
            username = self.username.text()
            password = self.password.text()
            selected_roles = [checkbox.text() for checkbox in self.role_checkboxes if checkbox.isChecked()]

            if not username or not password:
                QMessageBox.critical(self, 'Error', 'El nombre de usuario y la contraseña son obligatorios', QMessageBox.Ok)
                return

            if not selected_roles:
                QMessageBox.critical(self, 'Error', 'Debe seleccionar al menos un rol', QMessageBox.Ok)
                return

            # Crear el rol en PostgreSQL
            try:
                role_name = username  # Usar el nombre de usuario como nombre del rol
                role_password = password  # Usar la contraseña proporcionada

                # Crear el rol
                create_role_query = f"""
                CREATE ROLE {role_name} WITH LOGIN PASSWORD '{role_password}';
                """
                self.db.cursor.execute(create_role_query)

                # Otorgar permisos al rol
                grant_permissions_query = f"""
                GRANT CONNECT ON DATABASE cotaxomil TO {role_name};
                GRANT USAGE ON SCHEMA public TO {role_name};
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role_name};
                """
                self.db.cursor.execute(grant_permissions_query)

                # Asignar el rol a los roles seleccionados
                for role in selected_roles:
                    grant_role_query = f"""
                    GRANT {role} TO {role_name};
                    """
                    self.db.cursor.execute(grant_role_query)

                # Insertar el nuevo usuario en la tabla de usuarios
                insert_user_query = """
                INSERT INTO usuarios (username, password) VALUES (%s, %s) RETURNING user_id
                """
                self.db.cursor.execute(insert_user_query, (username, password))
                user_id = self.db.cursor.fetchone()[0]
                self.db.connection.commit()

                # Insertar los roles asociados
                for role in selected_roles:
                    insert_user_role_query = """
                    INSERT INTO user_roles (user_id, role_name) VALUES (%s, %s)
                    """
                    self.db.cursor.execute(insert_user_role_query, (user_id, role))
                
                self.db.connection.commit()
                QMessageBox.information(self, 'Éxito', 'Usuario y rol agregados correctamente', QMessageBox.Ok)
                self.close()
            except psycopg2.Error as e:
                self.db.connection.rollback()
                QMessageBox.critical(self, 'Error', f'No se pudo agregar el rol o el usuario: {e}', QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado fuera del formulario: {e}', QMessageBox.Ok)
