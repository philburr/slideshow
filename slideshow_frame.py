import os, os.path
import random, sys, time
import cec

from PyQt4.QtGui import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QDesktopWidget
from PyQt4.QtGui import QPixmap, QGraphicsPixmapItem, QAction, QKeySequence, QPainter
from PyQt4.QtGui import QVBoxLayout, QWidget, QSizePolicy, QFrame, QBrush, QColor, QFont, QFontMetrics
from PyQt4.QtCore import QTimer, QObject, QSize, Qt, QRectF

from gi.repository import GExiv2, GLib

class SlideshowFrame(object):
    def __init__(self, win, rect, filename, metadata):
        self.win = win
        self.rect = rect
        self.filename = filename
        self.metadata = metadata

        if self.metadata:
            self.line1 = self.metadata['Name']
            self.line2 = "%s Mission" % (self.metadata['Mission'])
            self.line3 = "%s" % (self.metadata['Time'])
        else:
            self.line1 = ""
            self.line2 = ""
            self.line3 = ""

        self.image = QGraphicsPixmapItem()
        self.win.scene.addItem(self.image)
        self.image.setTransformationMode(Qt.SmoothTransformation)

        self.use_two_lines = True

        self.fontsize1 = 32
        self.fontsize2 = 26
        self.fontsize3 = 24

        self.font1 = QFont('Times New Roman', self.fontsize1)
        self.font2 = QFont('Times New Roman', self.fontsize2)
        self.font3 = QFont('Times New Roman', self.fontsize3)

        self.title1 = self.win.scene.addText(self.line1, self.font1)
        self.title1.setDefaultTextColor(Qt.white)
        self.title1.setVisible(False)

        self.title2 = self.win.scene.addText(self.line2, self.font2)
        self.title2.setDefaultTextColor(Qt.white)
        self.title2.setVisible(False)

        self.title3 = self.win.scene.addText(self.line3, self.font3)
        self.title3.setDefaultTextColor(Qt.white)
        self.title3.setVisible(False)

        self.reservedHeight = 128
        self.padding = 20

        self.hide()

    def move(self, x, y):
        self.rect = QRectF(x, y, self.rect.width(), self.rect.height())

    def __rotate(self, metadata, origImgSize):
        # Qt only handles orientation properly from v5.5
        try:
            # try directly to get the tag, because sometimes get_tags() returns
            # tags that don't actually are in the file
            rot= metadata['Exif.Image.Orientation']
        except KeyError:
            # guess :-/
            rot= '1'

        # see http://www.daveperrett.com/images/articles/2012-07-28-exif-orientation-handling-is-a-ghetto/EXIF_Orientations.jpg
        # we have to 'undo' the rotations, so the numbers are negative
        if rot=='1':
            rotate= 0
            imgSize= origImgSize
        if rot=='8':
            rotate= -90
            imgSize= QSize(origImgSize.height(), origImgSize.width())
        if rot=='3':
            rotate= -180
            imgSize= origImgSize
        if rot=='6':
            rotate= -270
            imgSize= QSize(origImgSize.height(), origImgSize.width())

        # undo the last rotation and apply the new one
        self.image.setRotation(rotate)

        return imgSize

    def __zoomFit(self, imgSize):

        reservedHeight = self.reservedHeight + self.padding * 2

        hZoom = self.rect.width() / imgSize.width()
        vZoom = (self.rect.height() - reservedHeight) / imgSize.height()
        scale = min(hZoom, vZoom)

        self.image.setScale(scale)

        width = imgSize.width() * scale
        height = imgSize.height() * scale
        self.image.setPos((self.rect.width() - width)/2 + self.rect.x(), (self.rect.height() - reservedHeight - height) / 2 + self.rect.y())


    def layoutText(self):
        reservedHeight = self.reservedHeight + self.padding
        vertical_spacing = (self.reservedHeight - self.title1.boundingRect().height() - self.title2.boundingRect().height() - self.title3.boundingRect().height())/3

        x = (self.rect.width() - self.title1.boundingRect().width()) / 2
        y = self.rect.height() - reservedHeight + vertical_spacing
        self.title1.setPos(x + self.rect.x(), y + self.rect.y())

        x = (self.rect.width() - self.title2.boundingRect().width()) / 2
        y = self.rect.height() - reservedHeight + vertical_spacing * 2 + self.title1.boundingRect().height()
        self.title2.setPos(x + self.rect.x(), y + self.rect.y())

        x = (self.rect.width() - self.title3.boundingRect().width()) / 2
        y = self.rect.height() - reservedHeight + vertical_spacing * 3 + self.title1.boundingRect().height() + self.title2.boundingRect().height()
        self.title3.setPos(x + self.rect.x(), y + self.rect.y())

    def show(self):
        img = QPixmap(self.filename)

        try:
            metadata = GExiv2.Metadata(self.filename)
        except GLib.Error as e:
            print(repr(e))
            return

        self.image.setPixmap(img)
        self.image.setScale(1.0)
        self.image.setRotation(0)

        imgSize = self.__rotate(metadata, img.size())
        self.__zoomFit(imgSize)
        self.layoutText()

        self.title1.setVisible(True)
        self.title2.setVisible(True)
        self.title3.setVisible(True)
        self.image.setVisible(True)

    def hide(self):
        self.title1.setVisible(False)
        self.title2.setVisible(False)
        self.title3.setVisible(False)
        self.image.setVisible(False)

    def showImage(self, file, md):
        self.metadata = md

        try:
            metadata = GExiv2.Metadata(file)
        except GLib.Error as e:
            print(repr(e))
            return

        img= QPixmap(file)

        self.image.setPixmap(img)
        self.image.setScale(1.0)
        self.image.setRotation(0)

        imgSize= self.__rotate(metadata, img.size())
        
        self.__zoomFit(imgSize)
        self.layoutMetadata()


