from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget

import sys


class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Another Window")
        layout.addWidget(self.label)


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