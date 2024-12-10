from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class EmpleadoInfoWindow(QDialog):
    def __init__(self, empleado_data, parent=None):
        super(EmpleadoInfoWindow, self).__init__(parent)
        self.empleado_data = empleado_data
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Información del Empleado')
        self.resize(300, 400)

        layout = QVBoxLayout()

        for key, value in self.chofer_data.items():
            label = QLabel(f"{key}: {value}", self)
            layout.addWidget(label)

        close_button = QPushButton('Cerrar', self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)
