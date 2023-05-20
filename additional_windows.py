from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog, QDialogButtonBox, QLineEdit

import sys


class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()

    def create_soundboard_ui(self):
        layout = QVBoxLayout()
        self.setWindowTitle("Soundboard")
        self.buttons = {}
        self.buttons["beep"] = QPushButton("beep")
        self.buttons["R2D2 scream"] = QPushButton("R2D2 scream")
       # self.buttons["beep"].clicked.connect()
        
        for b in self.buttons:
            layout.addWidget(self.buttons[b])
        
        self.setLayout(layout)


class ConfigurationDialog(QDialog):

    def accept(self):
        print("button OK was pressed")

    def get_current_options(self):
        
        pass

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configuration Window")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()

        message = QLabel("Something happened, is that OK?")
        edit_box = QLineEdit()
        self.layout.addWidget(message)
        self.layout.addWidget(edit_box)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

