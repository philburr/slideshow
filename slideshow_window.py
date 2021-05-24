import os, os.path
import random, sys, time
import cec

from PyQt4.QtGui import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QDesktopWidget
from PyQt4.QtGui import QPixmap, QGraphicsPixmapItem, QAction, QKeySequence, QPainter
from PyQt4.QtGui import QVBoxLayout, QWidget, QSizePolicy, QFrame, QBrush, QColor, QFont, QFontMetrics
from PyQt4.QtCore import QTimer, QObject, QSize, Qt, QRectF

from gi.repository import GExiv2, GLib

from google_photos_sync import GooglePhotos
from slideshow_frame import SlideshowFrame

from PIL import Image, IptcImagePlugin
import exifread
import xml.etree.ElementTree as ET

import threading, subprocess

class MainWindow(QMainWindow):
    def __init__(self, view, scene, root, *args):
        QMainWindow.__init__(self, view)
        self.desktop_size = QDesktopWidget().screenGeometry()

        self.resize(self.desktop_size.width(), self.desktop_size.height())

        self.view= view
        self.scene= scene
        self.root = root

        self.cell_spacing = 10.0
        self.columns = 3
        self.rows = 2
        self.cell_rects = []

        winSize = self.desktop_size
        self.frame_width = (winSize.width() - self.cell_spacing * (self.columns + 1)) / self.columns
        self.frame_height = (winSize.height() - self.cell_spacing * (self.rows + 1)) / self.rows

        for row in range(self.rows):
            for col in range(self.columns):
                x = self.cell_spacing * (col + 1) + self.frame_width * col
                y = self.cell_spacing * (row + 1) + self.frame_height * row
                self.cell_rects.append(QRectF(x, y, self.frame_width, self.frame_height))

        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.scene.setSceneRect(QRectF(0, 0, winSize.width(), winSize.height()))

        self.frames = None
        self.current = None
        self.index = 0

        self.lock = threading.Lock()
        self.new_frames = None

        self.updateAlbum()

    def read_metadata(self, filename):
        try:
            image = Image.open(filename)
            iptc = IptcImagePlugin.getiptcinfo(image)
            metadata = {k.strip():v.strip() for (k,v) in [kv.decode("utf-8").split(':') for kv in iptc[(2, 25)]]}
            return metadata
        except Exception as ex:
            try:
                tags = None
                with open(filename, 'rb') as image_file:
                    tags = exifread.process_file(image_file, debug=True)

                if tags and 'Image ApplicationNotes' in tags:
                    xml = str(tags['Image ApplicationNotes'])
                    xml = ET.fromstring(xml)
                    items = xml.findall('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                    items = [item.text.split(':') for item in items]
                    items = [(a.strip(), b.strip()) for a, b in items]
                    metadata = dict(items)
                    return metadata

            except Exception as ex2:
                pass

        return None

    def scan(self):
        new_files = []
        for r, dirs, files in os.walk(os.path.abspath(self.root)):
            for name in files:
                if os.path.splitext(name)[1].lower() in ('.jpg', '.png', '.jpeg'):
                    new_files.append(os.path.join(r, name))

        metadata = {}
        for fname in new_files:
            try:
                md = self.read_metadata(fname)
                if 'Name' in md:
                    metadata[fname] = md
            except:
                pass

        new_files = self.sort(new_files, metadata)
        frames = []
        for filename in new_files:
            frame = SlideshowFrame(self, QRectF(0, 0, self.frame_width, self.frame_height), filename, metadata.get(filename))
            frames.append(frame)

        with self.lock:
            self.new_frames = frames

    def sort(self, new_files, metadata):
        with_metadata = [(metadata[filename], filename) for filename in new_files if filename in metadata]
        without_metadata = [filename for filename in new_files if not filename in metadata]

        with_last_name = [(meta['Name'].split()[-1], filename) for meta, filename in with_metadata]
        with_last_name.sort()
        return [filename for meta, filename in with_last_name] + without_metadata

    def updateAlbum(self, *args):
        if GooglePhotos(self.root).sync() or not self.frames:
            print('Updating Album')
            self.scan()
            print('Done')


    def nextImageSet(self):
        with self.lock:
            if self.new_frames:
                self.frames = self.new_frames
                self.new_frames = None
                self.index = 0

        if self.frames:
            self.current = [self.frames[(self.index + i) % len(self.frames)] for i in range(self.rows * self.columns)]
            self.index = (self.index + self.rows * self.columns) % len(self.frames)

    def nextImage(self, *args):
        if self.current:
            for frame in self.current:
                frame.hide()

        self.nextImageSet()

        if self.current:
            for frame, position in zip(self.current, self.cell_rects):
                frame.move(position.x(), position.y())
                frame.show()

