"""
The GUI handler of the system
"""

import sys
import threading
import ctypes

import numpy
from PyQt5.QtCore import QRectF, Qt, pyqtSignal, QCoreApplication, QEvent, QSize
from PyQt5.QtWidgets import QApplication, \
    QLabel, QMainWindow, QMenu, QFileDialog, QToolBar, QSpinBox, \
    QAction, QDockWidget, QVBoxLayout, QLineEdit, QWidget, QPushButton, QMessageBox
from PyQt5.QtGui import QIntValidator, QPainter, QImage, QPixmap, QDoubleValidator, QIcon

from digital_twin.rover import Rover
from digital_twin.rover_simulation import simulate
from digital_twin import constants
from digital_twin.environment import EnvType
from digital_twin.threadproc import RoverCommandThread
from digital_twin.rover_commands import create_rover_instructions_from_path, \
    rover_instructions_to_json
from digital_twin.environment_interface import image_to_environment
from spike_com.spike import SpikeHandler
from discord_integration.discord import upload_log_file
import additional_windows

MY_APP_ID = 'gooogle.wallacerover.controlcentre.1.0.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(MY_APP_ID)

# Constants
SCREEN_WIDTH = 1000
""" The width of the GUI in pixels"""
SCREEN_HEIGHT = 900
""" The height of the GUI in pixels """
TILE_START_X = 10
""" The starting x coordinate of the tile map """
TILE_START_Y = 10
""" The starting y coordinate of the tile map """

WIN_TITLE = "Gromit's Command Centre"
# TILE_WIDTH = 20
# """ The width of each tile in pixels """
# TILE_HEIGHT = 20
# """ The height of each tile in pixels """


def get_rover_image(painter: QPainter, image: QImage, rover: Rover):
    """
    :param painter: The current GUI painter
    :param image: The image of the rover
    :param rover: The rover being displayed
    :return: The image of the rover at the correct orientation
    """

    transform = painter.transform().rotateRadians(rover.get_direction() + numpy.pi / 2)
    pixmap = QPixmap(image)
    pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
    return pixmap.toImage()


class Grid(QWidget):
    """ Visual representation of an environment """

    SCALE = 0.7

    def __init__(self, environment, **kwargs):
        super().__init__(**kwargs)

        self.setAutoFillBackground(True)

        pallet = self.palette()
        pallet.setColor(self.backgroundRole(), Qt.gray)
        self.setPalette(pallet)

        self.setFixedSize(800, 800)
        self.columns = 400
        self.rows = 300
        self.environment = environment
        self.square_size = int(numpy.min([
            (self.width() - TILE_START_X) / self.environment.size()[0] - 2,
            (self.height() - TILE_START_Y) / self.environment.size()[1] - 2
        ]))

        # some random objects
        self.objects = [
            (10, 20),
            (11, 21),
            (12, 20),
            (12, 22),
        ]

    def paintEvent(self, _):  # pylint: disable=C0103
        """
            Paint the Grid
        """
        self.square_size = int(numpy.min([
            (self.width() - TILE_START_X) / self.environment.size()[0] - 2,
            (self.height() - TILE_START_Y) / self.environment.size()[1] - 2
        ]))

        painter = QPainter(self)

        # translate the painter by half a pixel to ensure correct line painting
        painter.translate(.5, .5)
        painter.setRenderHints(painter.Antialiasing)

        width, height = self.environment.size()
        # we need to add 1 to draw the topmost right/bottom lines too
        # print(height)
        # create a smaller rectangle
        object_size = self.square_size
        margin = self.square_size * .1
        object_rect = QRectF(margin, margin, object_size, object_size)
        node_rect = QRectF(margin, margin, object_size / 2, object_size / 2)

        for y in range(int(height)):
            for x in range(int(width)):
                # Gets the tile's position in the GUI
                pos_x = TILE_START_X + x * (self.square_size + 2)
                pos_y = TILE_START_Y + y * (self.square_size + 2)

                # Gets the type of the tile, this has a colour corresponding to it
                tile_type = self.environment.get_tile(x, y)
                #  print("{x} {y}")
                if tile_type is None:
                    tile_type = EnvType.EMPTY
                # Draws the tile
                # painter.drawLine(pos_x, pos_y, pos_x + self.square_size, pos_y)
                # painter.drawLine(pos_x, pos_y, pos_x, pos_y + self.square_size)
                if tile_type == EnvType.OBSTACLE:
                    painter.setBrush(Qt.red)
                    painter.drawRect(object_rect.translated(pos_x, pos_y))

        painter.setBrush(Qt.green)
        _, (goal_pos_x, goal_pos_y) = self.environment.get_start_end()
        goal_pos_x, goal_pos_y = TILE_START_Y + goal_pos_x * (self.square_size + 2), \
                                 TILE_START_Y + goal_pos_y * (self.square_size + 2)
        painter.drawRect(object_rect.translated(goal_pos_x, goal_pos_y))

        path = self.environment.get_path(should_generate=False)

        if path is not None:
            for i in range(len(path) - 1):
                pos_1 = path[i]
                pos_2 = path[i + 1]
                x = [TILE_START_X + (pos_1[0] + 0.5) * (self.square_size + 2),
                     TILE_START_X + (pos_2[0] + 0.5) * (self.square_size + 2)]
                y = [TILE_START_Y + (pos_1[1] + 0.5) * (self.square_size + 2),
                     TILE_START_Y + (pos_2[1] + 0.5) * (self.square_size + 2)]
                painter.drawLine(int(x[0]), int(y[0]), int(x[1]), int(y[1]))
                painter.drawEllipse(node_rect.translated(
                    x[0] - 0.25 * ((self.square_size + 2)), y[0] - 0.25 * ((self.square_size + 2))))
                painter.drawEllipse(node_rect.translated(
                    x[1] - 0.25 * ((self.square_size + 2)), y[1] - 0.25 * ((self.square_size + 2))))

        rover = self.environment.get_rover()

        if rover is not None:
            rover_x, rover_y = rover.get_location()

            rover_dims = constants.DISTANCE_BETWEEN_MOTORS * (self.square_size + 2) \
                         / constants.METERS_PER_TILE

            rover_map_x = ((self.square_size + 2) / constants.METERS_PER_TILE) * rover_x \
                          + TILE_START_X - rover_dims / 2
            rover_map_y = ((self.square_size + 2) / constants.METERS_PER_TILE) * rover_y \
                          + TILE_START_Y - rover_dims / 2

            rover_rect = QRectF(rover_map_x, rover_map_y, rover_dims, rover_dims)

            painter.drawImage(rover_rect, get_rover_image(painter,
                                                          QImage("resources/Rover.png"), rover))

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
        self.setWindowTitle(WIN_TITLE)
        self.setMinimumSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.central_widget = QPushButton("Click to load an environment")
        self.central_widget.clicked.connect(self.open_load_environment_dialog)
        #self.central_widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setCentralWidget(self.central_widget)
        self.loaded_env = False
        self._build_ui()

    def closeEvent(self, _):  # pylint: disable=C0103
        """
            Called when window closes
        """
        # Disconnect our spike handler
        if self.spike_handler.connected:
            self.spike_handler.disconnect()
        if self.sound_board:
            self.sound_board.close()

    def eventFilter(self, source, event):  # pylint: disable=C0103
        """
        Handles the window's events

        :param source: The source of the event called
        :param event: The event being called
        """
        # Keycode of the ENTER key
        enter_key = 16777220

        # Keypress events
        if event.type() == QEvent.KeyPress:
            # Editing the Starting Direction Textbox
            if source is self._start_dir_edit_box:
                if event.key() == enter_key:
                    angle = numpy.pi * int(self._start_dir_edit_box.text()) / 180

                    self.environment.set_start_direction(angle)
                    self.environment.get_rover().set_angle(angle)
                    self.grid.repaint()

            # Editing the Ending Direction Textbox
            if source is self._end_dir_edit_box:
                if event.key() == enter_key:
                    angle = numpy.pi * int(self._end_dir_edit_box.text()) / 180

                    self.environment.set_end_direction(angle)

        return super().eventFilter(source, event)

    def _build_ui(self):
        """
            Build the UI components
        """
        self._start_dir_edit_box = QLineEdit()
        self._end_dir_edit_box = QLineEdit()
        self._run_num_edit_box = QLineEdit()
        self._max_fail_prob_edit_box = QLineEdit()
        self._setup_dock_window()


        self.new_action = QAction(self)
        self.open_action = QAction("&Open...", self)
        self.open_action.triggered.connect(self.open_load_environment_dialog)
        self.save_action = QAction("&Save", self)
        self.exit_action = QAction("&Exit", self)

        # rover actions
        self.connect_action = QAction("&Connect To Rover", self)
        self.connect_action.triggered.connect(self._connect_to_rover)

        # Create Toolbars
        # Using a QToolBar object
        edit_tool_bar = QToolBar("Edit", self)
        self.addToolBar(edit_tool_bar)
        # Using a QToolBar object and a toolbar area
        help_tool_bar = QToolBar("Help", self)
        self.addToolBar(Qt.LeftToolBarArea, help_tool_bar)

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

        self._rover_control_dock_window()

    def _rover_control_dock_window(self):
        """
        Creates the dock window used in the GUI
        """
        dock_widget = QDockWidget(str("Rover Communication"), self)
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea |
                                    Qt.RightDockWidgetArea)
        
        layout = QVBoxLayout()

        connect_button = QPushButton("Connect to Rover")
        connect_button.clicked.connect(self._connect_to_rover)
        layout.addWidget(connect_button)

        log_dump_button = QPushButton("Dump Log")
        log_dump_button.clicked.connect(self.log_dump)
        layout.addWidget(log_dump_button)
        
        sound_board_button = QPushButton("Sound Board")
        sound_board_button.clicked.connect(self._sound_board_window)
        layout.addWidget(sound_board_button)

        widget = QWidget()
        widget.setLayout(layout)

        dock_widget.setWidget(widget)
       # dock_widget.setGeometry(100, 0, 200, 30)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

    def _sound_board_window(self):
        self.sound_board = additional_windows.AnotherWindow()
        self.sound_board.create_soundboard_ui()
        self.sound_board.show()

        pass
        #

    def _setup_dock_window(self):
        """
        Creates the dock window used in the GUI
        """
        dock_widget = QDockWidget(str("Simulation Control"), self)
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea |
                                    Qt.RightDockWidgetArea)

        layout = QVBoxLayout()

        self.image_box = QLabel("No environment loaded")

        if self.loaded_env:
            pixmap = QPixmap(self.file_name)
            self.image_box.setPixmap(pixmap)

        #layout.addWidget(self.image_box)

        self._start_dir_edit_box.setPlaceholderText("Starting Direction Angle")
        self._start_dir_edit_box.setValidator(QIntValidator(0, 360))
        self._start_dir_edit_box.installEventFilter(self)
        layout.addWidget(self._start_dir_edit_box)

        self._end_dir_edit_box.setPlaceholderText("Final Direction Angle")
        self._end_dir_edit_box.setValidator(QIntValidator(0, 360))
        self._end_dir_edit_box.installEventFilter(self)
        layout.addWidget(self._end_dir_edit_box)

        run_button = QPushButton("Run")
        run_button.clicked.connect(self.run_rover_main)
        layout.addWidget(run_button)

        self._run_num_edit_box.setPlaceholderText("Number of runs")
        self._run_num_edit_box.setValidator(QIntValidator(1, 100000))
        layout.addWidget(self._run_num_edit_box)

        self._max_fail_prob_edit_box.setPlaceholderText("Failure Probability 0 to 1")
        self._max_fail_prob_edit_box.setValidator(QDoubleValidator(0.0, 1.0, 5))
        layout.addWidget(self._max_fail_prob_edit_box)

        run_sim_button = QPushButton("Run Simulation")
        run_sim_button.clicked.connect(self.simulate_rover)
        
        layout.addWidget(run_sim_button)

        widget = QWidget()
        widget.setLayout(layout)

        dock_widget.setWidget(widget)
        dock_widget.setGeometry(100, 0, 200, 30)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

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
        if not self.check_for_environment_loaded():
            return
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
                                                   "Select Environment Image File", "./resources",
                                                   "Env Images (*env*.png)", options=options)
        if file_name:
            self.file_name = file_name
            
            self.setWindowTitle(WIN_TITLE + ": " + file_name.split("/")[-1])
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
        self.environment.set_start_direction(-numpy.pi / 2)

        start_pos, _ = self.environment.get_start_end()
        start_dir, _ = self.environment.get_start_end_directions()

        rover = Rover((start_pos[0] + 0.5) * constants.METERS_PER_TILE,
                      (start_pos[1] + 0.5) * constants.METERS_PER_TILE,
                      direction=start_dir)
        self.environment.set_rover(rover)

        # Load the grid UI
        self.add_grid(self.environment)
        self.loaded_env = (True)

    def _show_message_box(self, icon, title, text):
        """
            Show message box with given icon, title, and text
        """
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(text)
        msg.setWindowTitle(title)
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
        if not self.check_for_environment_loaded():
            return
        # Get the rover from our environment
        rover = self.environment.get_rover()

        if len(self._start_dir_edit_box.text()) > 0:
            self.environment.set_start_direction(int(self._start_dir_edit_box.text()) \
                                                 * numpy.pi / 2)

        if len(self._end_dir_edit_box.text()) > 0:
            self.environment.set_end_direction(int(self._end_dir_edit_box.text()) \
                                               * numpy.pi / 2)

        # Start rover command thread
        cmd_thread = RoverCommandThread(rover)
        cmd_thread.start()
        rover_command = cmd_thread.get_rover_command()

        start_pos, _ = self.environment.get_start_end()
        start_angle, end_angle = self.environment.get_start_end_directions()

        rover.set_position(
            ((start_pos[0] + 0.5) * constants.METERS_PER_TILE,
             (start_pos[1] + 0.5) * constants.METERS_PER_TILE))
        rover.set_angle(start_angle)

        # Get rover commands to send to physical rover
        path = self.environment.get_path()

        self.grid.repaint()

        rover_commands = create_rover_instructions_from_path(path, start_angle, end_angle)

        for cmd_type, value, time in rover_commands:
            rover_command.add_command(cmd_type, value, time)

        formatted_instructs = rover_instructions_to_json(rover_commands)

        if self.spike_handler.communication_handler is not None:
            print("Sending instructions...")
            self.spike_handler.send_instructions(formatted_instructs)
            self._show_message_box(QMessageBox.Information, "Instructions Sent",
                                   "Instructions Sent!")
        else:
            print("Physical rover not connected!")
            self._show_message_box(QMessageBox.Information, "Instructions Not Sent",
                                   "Instructions Not Sent! Reason: Physical Rover not connected!")

        while not rover_command.is_empty():
            QCoreApplication.processEvents()
            self.grid.repaint()

    def check_for_environment_loaded(self):
        if not self.loaded_env:
            print("environment not loaded")
        
        return self.loaded_env

    def simulate_rover(self):
        """
        Commences simulated trials of the rover's actions using real world information to adjust
        the path finding to be suitable for the real rover
        Uses hypothesis testing
        """
        if not self.check_for_environment_loaded():
            return
        
        run_num = int(self._run_num_edit_box.text()) \
            if len(self._run_num_edit_box.text()) > 0 else 1
        
        failure_probability = float(self._max_fail_prob_edit_box.text()) if len(self._max_fail_prob_edit_box.text()) > 0 else 0.5

        thread = threading.Thread(target=simulate,
                                  args=(self.environment,
                                        run_num,
                                        failure_probability),
                                  daemon=True)
        thread.start()

        while thread.is_alive():
            QCoreApplication.processEvents()
            self.grid.repaint()


def setup() -> int:
    """
    Sets up the main GUI

    :return: The exit code given by the GUI application
    """
    app = QApplication(sys.argv)

    app_icon = QIcon()
    app_icon.addFile("resources/Wallace.png", QSize(32, 32))
    app.setWindowIcon(app_icon)

    win = Window()
    win.show()
    return app.exec_()
