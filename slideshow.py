import os, os.path, subprocess
import random, sys, time

from PyQt4.QtGui import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QDesktopWidget
from PyQt4.QtGui import QPixmap, QGraphicsPixmapItem, QAction, QKeySequence, QPainter
from PyQt4.QtGui import QVBoxLayout, QWidget, QSizePolicy, QFrame, QBrush, QColor, QFont, QFontMetrics
from PyQt4.QtCore import QTimer, QObject, QSize, Qt, QRectF

from slideshow_window import MainWindow
from tv import TV

def slideshow():

    folder = None
    time = None
    args = sys.argv[:1]

    for arg in sys.argv[2:]:
        if arg.startswith("--"):
            args.append(arg)
            continue
        if not folder:
            folder = arg
            continue
        time = arg

    if folder is None or time is None:  # awwww :)
        print("""usage: %s ROOT SECONDS
ROOT points to the root directory where the images are going to be picked up.
SECONDS is the time between images.""" % sys.argv[0])
        sys.exit(1)

    sys.argv = args

    cursor = Qt.BlankCursor

    app= QApplication(sys.argv)
    win= QMainWindow()

    QApplication.setOverrideCursor(cursor)
    QApplication.changeOverrideCursor(cursor)

    scene= QGraphicsScene()

    view= QGraphicsView(scene, win)
    view.setFrameShadow(QFrame.Plain)
    view.setFrameStyle(QFrame.NoFrame)
    view.show()

    brush = QBrush(QColor(0, 0, 0))
    brush.setStyle(Qt.SolidPattern)
    view.setBackgroundBrush(brush)

    runner= MainWindow(view, scene, folder)

    timer = QTimer(app)
    timer.timeout.connect(runner.nextImage)
    timer.start(float(time)*1000)
    QTimer.singleShot(200, runner.nextImage)

    timer2 = QTimer(app)
    timer2.timeout.connect(runner.updateAlbum)
    timer2.start(60*60*1000)

    win.setCentralWidget(view)

    win.showFullScreen()

    tv = TV()

    app.exec_()

    tv.stop()

def main():
    if sys.argv[1] == 'subprocess':
        slideshow()
        return

    folder = None
    time = None
    args = sys.argv[:1]

    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            args.append(arg)
            continue
        if not folder:
            folder = arg
            continue
        time = arg

    if folder is None or time is None:  # awwww :)
        print("""usage: %s ROOT SECONDS
ROOT points to the root directory where the images are going to be picked up.
SECONDS is the time between images.""" % sys.argv[0])
        sys.exit(1)

    args = ['python3'] + sys.argv[:1] + ['subprocess'] + sys.argv[1:]
    while True:
        subprocess.run(args, capture_output=False)

if __name__=='__main__':
    main()
