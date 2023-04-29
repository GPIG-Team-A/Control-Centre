import sys
import pyqtgraph as pg
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QMenu, QToolBar, QAction,QSpinBox, QAction, QLabel, QDockWidget, QVBoxLayout,QLineEdit,QWidget,QPushButton ,QStackedLayout  ,QGraphicsView
from PyQt5.QtGui import QPixmap, QIntValidator,QPainter, QBrush, QPen
# Import imageio
import imageio
import digital_twin.environment
from digital_twin.rover import Rover
# Import numpy
import numpy

from digital_twin.constants import *
import numpy

import digital_twin.constants
import digital_twin.environment
from digital_twin.environment import Environment
from digital_twin.rover import Rover
from digital_twin.threadproc import RoverCommandThread
from digital_twin.rover_commands import create_rover_instructions_from_path, save_rover_instructions_as_json, RoverCommandType
from digital_twin.environment_interface import image_to_environment
import sys

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
path = []

class Grid(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(800, 900)
        self.columns = 400
        self.rows = 300
        self.squareSize = TILE_WIDTH

        # some random objects
        self.objects = [
            (10, 20), 
            (11, 21), 
            (12, 20), 
            (12, 22), 
        ]

    def resizeEvent(self, event):
        # compute the square size based on the aspect ratio, assuming that the
        # column and row numbers are fixed
        reference = self.width() * self.rows / self.columns
        if reference > self.height():
            # the window is larger than the aspect ratio
            # use the height as a reference (minus 1 pixel)
            self.squareSize = (self.height() - 1) / self.rows
        else:
            # the opposite
            self.squareSize = (self.width() - 1) / self.columns

    def paintEvent(self, event):
        global env, path
        qp = QPainter(self)
        # translate the painter by half a pixel to ensure correct line painting
        qp.translate(.5, .5)
        qp.setRenderHints(qp.Antialiasing)

        width, height = env.size()
        # we need to add 1 to draw the topmost right/bottom lines too
       # print(height)
        # create a smaller rectangle
        objectSize = TILE_WIDTH
        margin = self.squareSize* .1
        objectRect = QRectF(margin, margin, objectSize, objectSize)
        nodeRect = QRectF(margin, margin, objectSize/2, objectSize/2)
        
        for y in range(int(height)):
            for x in range(int(width)):
                # Gets the tile's position in the GUI
                posX = TILE_START_X + x * (TILE_WIDTH + 2)
                posY = TILE_START_Y + y * (TILE_HEIGHT + 2)

                # Gets the type of the tile, this has a colour corresponding to it
                tileType = env.get_tile(x, y)
              #  print("{x} {y}")
                if tileType is None:
                    tileType = digital_twin.environment.EnvType.EMPTY

                # Draws the tile
                qp.drawLine(posX, posY, posX + TILE_WIDTH, posY)
                qp.drawLine(posX, posY, posX , posY + TILE_HEIGHT)
                if(tileType == digital_twin.environment.EnvType.OBSTACLE):
                    
                    qp.setBrush(Qt.red)
                    qp.drawRect(objectRect.translated(
                        posX,posY) )

            

        qp.setBrush(Qt.green)
        for i in range(len(path) - 1):
            pos_1 = path[i]
            pos_2 = path[i + 1]
            x = [TILE_START_X + (pos_1[0] + 0.5) * (TILE_WIDTH + 2), TILE_START_X + (pos_2[0] + 0.5) * (TILE_WIDTH + 2)]
            y = [TILE_START_Y + (pos_1[1] + 0.5) * (TILE_HEIGHT + 2),TILE_START_Y + (pos_2[1] + 0.5) * (TILE_HEIGHT + 2)]
            qp.drawLine(int(x[0]),int(y[0]),int(x[1]),int(y[1]))
            qp.drawEllipse(nodeRect.translated(
                x[0] - 0.25*((TILE_WIDTH + 2)),y[0] - 0.25*((TILE_WIDTH + 2))))
            qp.drawEllipse(nodeRect.translated(
                x[1] - 0.25*((TILE_WIDTH + 2)),y[1] - 0.25*((TILE_WIDTH + 2))))
        qp.end()

class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None, ):
        """Initializer."""
        super().__init__(parent)
        

        self.setWindowTitle("Python Menus & Toolbars")
        self.setFixedSize(1000, 900)
        self.centralWidget = QLabel("Hello, World")
        self.centralWidget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setCentralWidget(self.centralWidget)
        self._createActions()
        self._createMenuBar()
        self._createToolBars()
        self._createDockWindow()
        self.add_grid()
      #  self.displayGrid()
        #self.test()
        timer = QTimer(self)
        timer.timeout.connect(self.add_grid)
        timer.start(1000)
        


    def _createDockWindow(self):
        dockWidget = QDockWidget(str("Dock Widget"), self)
        dockWidget.setAllowedAreas(Qt.LeftDockWidgetArea |
                                           Qt.RightDockWidgetArea)
        
        layout = QVBoxLayout()
        #layout.addWidget(QLabel("font size"))
        xEditBox = QLineEdit()
        xEditBox.setPlaceholderText("Number of runs")
        xEditBox.setValidator( QIntValidator(1,100000) )
        layout.addWidget(xEditBox)
        
        layout.addWidget(QPushButton("Run"))

        
        widg = QWidget()
        widg.setLayout(layout)

        dockWidget.setWidget(widg)
        dockWidget.setGeometry(100, 0, 200, 30)

        self.addDockWidget(Qt.LeftDockWidgetArea, dockWidget)

    def _createActions(self):
        # Creating action using the first constructor
        self.newAction = QAction(self)
        self.newAction.setText("&New")
        # Creating actions using the second constructor
        self.openAction = QAction("&Open...", self)
        self.saveAction = QAction("&Save", self)
        self.exitAction = QAction("&Exit", self)
        self.copyAction = QAction("&Copy", self)
        self.pasteAction = QAction("&Paste", self)
        self.cutAction = QAction("C&ut", self)
        self.helpContentAction = QAction("&Help Content", self)
        self.aboutAction = QAction("&About", self)
        
        
    def _createToolBars(self):
        # Using a title
        fileToolBar = self.addToolBar("File")
        # Using a QToolBar object
        editToolBar = QToolBar("Edit", self)
        self.addToolBar(editToolBar)
        # Using a QToolBar object and a toolbar area
        helpToolBar = QToolBar("Help", self)
        self.addToolBar(Qt.LeftToolBarArea, helpToolBar)
        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setFocusPolicy(Qt.NoFocus)
        label = QLabel("font size")
        editToolBar.addWidget(label)
        editToolBar.addWidget(self.fontSizeSpinBox)

    def _createMenuBar(self):
        menuBar = self.menuBar()
        self.setMenuBar(menuBar)
        # Creating menus using a QMenu object
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.exitAction)
        # Creating menus using a title
        editMenu = menuBar.addMenu("&Edit")
        helpMenu = menuBar.addMenu("&Help")
    
    
    def draw_path(self):
        global path
        gv = pg.GraphicsView();

        w = pg.GraphicsLayout()
      #  p2 = w.addPlot(row=0, col=0)
        p1 = w.addPlot(row=0, col=0,colspan=2, rowspan=2)
        v = p1.getViewBox()
        gv.setCentralWidget(w)
        p1.setAspectLocked()
        v.setAspectLocked()
        v.invertY()
        print(f"gen nedpath {len(path)}")
        for i in range(len(path) - 1):
            pos_1 = path[i]
            pos_2 = path[i + 1]
            x = [TILE_START_X + (pos_1[0] + 0.5) * (TILE_WIDTH + 2), TILE_START_X + (pos_2[0] + 0.5) * (TILE_WIDTH + 2)]
            y = [TILE_START_Y + (pos_1[1] + 0.5) * (TILE_HEIGHT + 2),TILE_START_Y + (pos_2[1] + 0.5) * (TILE_HEIGHT + 2)]
            p1.plot(x,y,pen=pg.mkPen('b', width=5))
        img = pg.ImageItem(imageio.v2.imread("resources/env.png"),axisOrder='row-major')
        img.setZValue(-100)
       # p1.showAxRect(v.viewRect())
        v.addItem(img)
        p1.invertY(True)
        
       # p1.invertY(True)
        self.setCentralWidget(gv)
        #p1.setXLink



    def add_grid(self):
        g = Grid()
        self.setCentralWidget(g)
        
if __name__ == "__main__":

    env = image_to_environment(2.5, 2.5, image_filename="resources/env.png")
    #env.set_start_end((5, 39), None)

    start_pos, end_pos = env.get_start_end()

    rover = Rover((start_pos[0] + 0.5) * METERS_PER_TILE,
                  (start_pos[1] + 0.5) * METERS_PER_TILE, -numpy.pi / 2)
    env.set_rover(rover)

    cmd_thread = RoverCommandThread(rover)
    cmd_thread.start()

    rover_command = cmd_thread.get_rover_command()
    
    mean_power = 50.01724137931034
    stdev = 0.8806615716635956

    tst = [(mean_power + numpy.random.normal(0, stdev), -mean_power + numpy.random.normal(0, stdev)) for _ in range(28)]

    max_speed = 1

    speeds = [(x[0] /100 * max_speed, -x[1] / 100 * max_speed) for x in tst]

    rover_cmds = [(RoverCommandType.RPMS, x, 0.1) for x in speeds]

    #formatted_instructs =save_rover_instructions_as_json(rover_cmds)

    for cmd_type, value, t in rover_cmds:
        rover_command.add_command(cmd_type, value, t)


    width, height = env.size()
    path = env.get_path()
    
    app = QApplication(sys.argv)
    win = Window()
  #  win.draw_grid()
    win.show()

    sys.exit(app.exec_())
