from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
from add_est_tan_form import AddEstTanForm
from add_sum_tan_form import AddSumTanForm
from info_tan import InfoTan

class DieselWindow(QMainWindow):
    def __init__(self, db):
        super(DieselWindow, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Diesel')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        # Espacio flexible para centrar los botones
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.check_AddEstTanForm_button = QPushButton('Agregar Estado del tanque', self)
        self.check_AddEstTanForm_button.clicked.connect(self.show_add_est_tan_form)
        self.check_AddEstTanForm_button.setStyleSheet('background-color: rgb(88, 129, 216 );; color: white;')
        self.check_AddEstTanForm_button.setMinimumWidth(200)  # Asegura un ancho mínimo
        self.check_AddEstTanForm_button.setMaximumWidth(300)  # Limita el ancho máximo
        layout.addWidget(self.check_AddEstTanForm_button, alignment=Qt.AlignCenter)

        self.check_SumTanForm_button = QPushButton('Suministro tanque', self)
        self.check_SumTanForm_button.clicked.connect(self.show_add_sum_tan_form)
        self.check_SumTanForm_button.setStyleSheet('background-color: rgb(88, 129, 216 );; color: white;')
        self.check_SumTanForm_button.setMinimumWidth(200)  # Asegura un ancho mínimo
        self.check_SumTanForm_button.setMaximumWidth(300)  # Limita el ancho máximo
        layout.addWidget(self.check_SumTanForm_button, alignment=Qt.AlignCenter)

        self.check_info_tan_button = QPushButton('Info tanque', self)
        self.check_info_tan_button.clicked.connect(self.show_info_tan)
        self.check_info_tan_button.setStyleSheet('background-color: rgb(88, 129, 216 );; color: white;')
        self.check_info_tan_button.setMinimumWidth(200)  # Asegura un ancho mínimo
        self.check_info_tan_button.setMaximumWidth(300)  # Limita el ancho máximo
        layout.addWidget(self.check_info_tan_button, alignment=Qt.AlignCenter)


        # Espacio flexible después de los botones
        layout.addItem(spacer)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def show_add_est_tan_form(self):
        self.add_est_tan_form = AddEstTanForm(self.db)
        self.add_est_tan_form.show()
    
    def show_add_sum_tan_form(self):
        self.add_sum_tan_form = AddSumTanForm(self.db)
        self.add_sum_tan_form.show()

    def show_info_tan(self):
        self.info_tan = InfoTan(self.db)
        self.info_tan.show()
