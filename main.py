"""
    UI Main Entrance
"""
import sys
import numpy
from PyQt5.QtCore import QRectF, Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, \
    QLabel, QMainWindow, QMenu,QFileDialog, QToolBar, QSpinBox, \
    QAction, QDockWidget, QVBoxLayout,QLineEdit,QWidget,QPushButton, QMessageBox
from PyQt5.QtGui import QIntValidator, QPainter
from digital_twin.rover import Rover
from digital_twin import constants
from digital_twin.environment import EnvType
from digital_twin.threadproc import RoverCommandThread
from digital_twin.rover_commands import create_rover_instructions_from_path,\
    rover_instructions_to_json, RoverCommandType
from digital_twin.environment_interface import image_to_environment
from spike_com.spike import SpikeHandler
from discord_integration.discord import upload_log_file

# Constants
SCREEN_WIDTH = 1000
""" The width of the GUI in pixels"""
SCREEN_HEIGHT = 900
""" The height of the GUI in pixels """
TILE_START_X = 10
""" The starting x coordinate of the tile map """
TILE_START_Y = 10
""" The starting y coordinate of the tile map """
TILE_WIDTH = 20
""" The width of each tile in pixels """
TILE_HEIGHT = 20
""" The height of each tile in pixels """

class Grid(QWidget):
    """ Visual representation of an environment """

    SCALE = 0.7

    def __init__(self, environment, **kwargs):
        super().__init__(**kwargs)
        self.setFixedSize(800, 800)
        self.columns = 400
        self.rows = 300
        self.square_size = TILE_WIDTH
        self.environment = environment

        # some random objects
        self.objects = [
            (10, 20),
            (11, 21),
            (12, 20),
            (12, 22),
        ]
    def paintEvent(self, _): # pylint: disable=C0103
        """
            Paint the Grid
        """
        painter = QPainter(self)
        # translate the painter by half a pixel to ensure correct line painting
        painter.translate(.5, .5)
        painter.setRenderHints(painter.Antialiasing)

        width, height = self.environment.size()
        # we need to add 1 to draw the topmost right/bottom lines too
       # print(height)
        # create a smaller rectangle
        object_size = TILE_WIDTH
        margin = self.square_size* .1
        object_rect = QRectF(margin, margin, object_size, object_size)
        node_rect = QRectF(margin, margin, object_size/2, object_size/2)
        
        for y in range(int(height - 1)):
            for x in range(int(width - 1)):
                # Gets the tile's position in the GUI
                pos_x = TILE_START_X + x * (TILE_WIDTH + 2)
                pos_y = TILE_START_Y + y * (TILE_HEIGHT + 2)

                # Gets the type of the tile, this has a colour corresponding to it
                tile_type = self.environment.get_tile(x, y)
              #  print("{x} {y}")
                if tile_type is None:
                    tile_type = EnvType.EMPTY
                # Draws the tile
                painter.drawLine(pos_x, pos_y, pos_x + TILE_WIDTH, pos_y)
                painter.drawLine(pos_x, pos_y, pos_x , pos_y + TILE_HEIGHT)
                if tile_type == EnvType.OBSTACLE:
                    painter.setBrush(Qt.red)
                    painter.drawRect(object_rect.translated(pos_x,pos_y))

        painter.setBrush(Qt.green)
        path = self.environment.get_path()
        for i in range(len(path) - 1):
            pos_1 = path[i]
            pos_2 = path[i + 1]
            x = [TILE_START_X + (pos_1[0] + 0.5) * (TILE_WIDTH + 2), 
                 TILE_START_X + (pos_2[0] + 0.5) * (TILE_WIDTH + 2)]
            y = [TILE_START_Y + (pos_1[1] + 0.5) * (TILE_HEIGHT + 2),
                 TILE_START_Y + (pos_2[1] + 0.5) * (TILE_HEIGHT + 2)]
            painter.drawLine(int(x[0]),int(y[0]),int(x[1]),int(y[1]))
            painter.drawEllipse(node_rect.translated(
                x[0] - 0.25*((TILE_WIDTH + 2)),y[0] - 0.25*((TILE_WIDTH + 2))))
            painter.drawEllipse(node_rect.translated(
                x[1] - 0.25*((TILE_WIDTH + 2)),y[1] - 0.25*((TILE_WIDTH + 2))))
        painter.end()

class Window(QMainWindow):
    """Main Window."""

    update_rover_status = pyqtSignal(bool)

    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
 
        self.environment = None
        self.grid = None
        self.spike_handler = SpikeHandler()
        self.setWindowTitle("Python Menus & Toolbars")
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.central_widget = QLabel("Load an Environment: File -> Open")
        self.central_widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setCentralWidget(self.central_widget)
        self._build_ui()

    def closeEvent(self, _): # pylint: disable=C0103
        """
            Called when window closes
        """
        # Disconnect our spike handler
        self.spike_handler.disconnect()

    def _build_ui(self):
        """
            Build the UI components
        """
        # Create Dock Window
        dock_widget = QDockWidget(str("Dock Widget"), self)
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea |
                                           Qt.RightDockWidgetArea)

        layout = QVBoxLayout()
        edit_box = QLineEdit()
        edit_box.setPlaceholderText("Number of runs")
        edit_box.setValidator( QIntValidator(1,100000) )
        layout.addWidget(edit_box)

        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run_rover_main)
        layout.addWidget(run_button)
        widg = QWidget()
        widg.setLayout(layout)

        dock_widget.setWidget(widg)
        dock_widget.setGeometry(100, 0, 200, 30)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

        self.new_action = QAction(self)
        self.open_action = QAction("&Open...", self)
        self.open_action.triggered.connect(self.open_load_environment_dialog)
        self.save_action = QAction("&Save", self)
        self.exit_action = QAction("&Exit", self)

        # rover actions
        self.connect_action = QAction("&Connect To Rover",self)
        self.connect_action.triggered.connect(self._connect_to_rover)

        # Create Toolbars
        # Using a QToolBar object
        edit_tool_bar = QToolBar("Edit", self)
        self.addToolBar(edit_tool_bar)
        # Using a QToolBar object and a toolbar area
        help_tool_bar = QToolBar("Help", self)
        self.addToolBar(Qt.LeftToolBarArea, help_tool_bar)
        self.font_size_spin_box = QSpinBox()
        self.font_size_spin_box.setFocusPolicy(Qt.NoFocus)
        label = QLabel("font size")
        edit_tool_bar.addWidget(label)
        edit_tool_bar.addWidget(self.font_size_spin_box)

        self.rover_status_label = QLabel("Rover Status: Offline")
        edit_tool_bar.addWidget(self.rover_status_label)

        # Create Menu Bars
        menu_bar = self.menuBar()
        self.setMenuBar(menu_bar)
        # Creating menus using a QMenu object
        file_menu = QMenu("&File", self)
        menu_bar.addMenu(file_menu)
        file_menu.addAction(self.connect_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.exit_action)
        # Creating menus using a title
        edit_menu = menu_bar.addMenu("&Edit")
        self.log_dump_action = QAction("&Log Dump", self)
        self.log_dump_action.triggered.connect(self.log_dump)
        edit_menu.addAction(self.log_dump_action)
        self.update_rover_action = QAction("&Update Rover", self)
        self.update_rover_action.triggered.connect(self.update_rover)
        edit_menu.addAction(self.update_rover_action)
    
    def update_rover(self):
        """
            Update rover files
        """
        self.spike_handler.update_rover_files()
        self._show_message_box(QMessageBox.Information, "Updated!", 
                               "Check logs for complete output")
    
    def log_dump(self):
        """
            Dump rover logs
        """
        log = self.spike_handler.get_log()
        if log:
            upload_log_file(log)
            print("Uploading log file...")

    def open_load_environment_dialog(self):
        """
            Open interaction dialog to open a new environment png file
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, 
            "Select Environment Image File", "","All Files (*)", options=options)
        if file_name:
            self.load_environment(file_name)

    def add_grid(self, environment):
        """
            Add a Grid for the given Environment
        """
        self.grid = Grid(environment)
        self.setCentralWidget(self.grid)
    
    def load_environment(self, image_filename):
        """
            Load an environment into the UI
        """
        self.environment = image_to_environment(2.5, 2.5, image_filename=image_filename)

        start_pos, _ = self.environment.get_start_end()

        rover = Rover((start_pos[0] + 0.5) * constants.METERS_PER_TILE,
                    (start_pos[1] + 0.5) * constants.METERS_PER_TILE, -numpy.pi / 2)
        self.environment.set_rover(rover)

        # Load the grid UI
        self.add_grid(self.environment)
    
    def _show_message_box(self, icon, title, text):
        """
            Show message box with given icon, title, and text
        """
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(title)
        msg.setWindowTitle(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _connect_to_rover(self):
        """
            Attempt to connect to rover and update the UI
        """
        def _signal_callback(connected):
            if connected:
                self._show_message_box(QMessageBox.Information, "Connected!", "Connected to Rover")
            else:
                self._show_message_box(QMessageBox.Warning, "Failed!", "Failed to Connect to Rover")
            self.rover_status_label.setText(f"Rover Status: {'Online' if connected else 'Offline'}")
        self.rover_status_label.setText("Rover Status: Connecting...")
        self.update_rover_status.connect(_signal_callback)
        self.spike_handler.connect(self.update_rover_status.emit)
        

    def run_rover_main(self):
        """
            Execute the Rover Commands
        """
        # Get the rover from our environment
        rover = self.environment.get_rover()

        # Start rover command thread
        cmd_thread = RoverCommandThread(rover)
        cmd_thread.start()
        rover_command = cmd_thread.get_rover_command()
        
        # Bunch of stuff I no understand
        mean_power = 50.01724137931034
        stdev = 0.8806615716635956
        tst = [(mean_power + numpy.random.normal(0, stdev), 
                -mean_power + numpy.random.normal(0, stdev)) for _ in range(28)]
        max_speed = 1
        speeds = [(x[0] /100 * max_speed, -x[1] / 100 * max_speed) for x in tst]
        rover_cmds = [(RoverCommandType.RPMS, x, 0.1) for x in speeds]
        for cmd_type, value, time in rover_cmds:
            rover_command.add_command(cmd_type, value, time)

        # Get rover commands to send to physical rover
        path = self.environment.get_path()
        rover_commands = create_rover_instructions_from_path(path, rover.get_direction())
        formatted_instructs = rover_instructions_to_json(rover_commands)
        print("Sending instructions...")
        self.spike_handler.send_instructions(formatted_instructs)
        self._show_message_box(QMessageBox.Information, "Instructions Sent", "Instructions Sent!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())