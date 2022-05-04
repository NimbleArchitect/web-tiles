#!/usr/bin/env python3

# pip3 install PyQt6 PyQt6-WebEngine

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtPrintSupport import *
from PyQt6.QtWebEngineCore import *
from PyQt6.QtCore import Qt
import PyQt6
import webbrowser
import platform
import sys
import os

def run_app():
    app = QApplication(sys.argv)
    app.setApplicationName("web-tiles")
    app.setOrganizationName("NimbleArchitect")

    window = MainWindow()
    window.show()
    excode = app.exec()
    window.close()
    # print("finished")
    sys.exit(excode)


class MainWindow(QMainWindow):
    lockStep = False
    reload_actions = []
    tileurl_actions = []

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)
        self.web_widget = WebWindow(self) 
        self.setCentralWidget(self.web_widget)
        self.tile_count = len(self.web_widget.webTiles)

        action_menu = self.menuBar().addMenu("&Action")

        reload_btn = QAction(QIcon(os.path.join('images', 'arrow-circle-315.png')), "Reload all", self)
        reload_btn.setStatusTip("force web page reload of all tiles")
        reload_btn.triggered.connect(self.web_widget.page_reload)
        action_menu.addAction(reload_btn)

        reset_layout_btn = QAction(QIcon(os.path.join('images', 'arrow-circle-315.png')), "Reset Layout", self)
        reset_layout_btn.setStatusTip("Reset layout view back to defaults")
        reset_layout_btn.triggered.connect(self.web_widget.resetView)
        action_menu.addAction(reset_layout_btn)

        show_4_tiles_btn = QAction(QIcon(os.path.join('images', 'arrow-circle-315.png')), "Togle 4 tiles", self)
        show_4_tiles_btn.setStatusTip("Toggle 4 tile layout")
        show_4_tiles_btn.triggered.connect(self.toggle4tiles)
        action_menu.addAction(show_4_tiles_btn)

        lock_tiles_btn = QAction(QIcon(os.path.join('images', 'arrow-circle-315.png')), "Tile lock", self)
        lock_tiles_btn.setStatusTip("Lock tiles so they move together")
        lock_tiles_btn.triggered.connect(self.locktiles)
        if QSettings().contains("lockstep"):
            if QSettings().value("lockstep") == True:
                self.locktiles()
        action_menu.addAction(lock_tiles_btn)

        self.reload_menu = action_menu.addMenu("&Reload")
        self.tiles_menu = self.menuBar().addMenu("&Tiles")
        for i in range(self.tile_count):
            self.addTileMenuItems(i)

    def addTileMenuItems(self, i):
        exists =  i in self.reload_actions
        if exists == True:
            return

        n = str(i + 1)
        self.reload_actions.insert(i,None)
        self.reload_actions[i] = QAction(QIcon(os.path.join('images', 'arrow-circle-315.png')), "Tile " + n, self)
        self.reload_actions[i].setStatusTip("Reload tile " + n)
        self.reload_actions[i].triggered.connect(self.web_widget.webTiles[i].reload)
        if i >= self.tile_count:
            self.reload_actions[i].setVisible(False)
        self.reload_menu.addAction(self.reload_actions[i])

        self.tileurl_actions.insert(i,None)
        self.tileurl_actions[i] = QAction(QIcon(os.path.join('images', 'arrow-circle-315.png')), "Tile " + n + " url", self)
        self.tileurl_actions[i].setStatusTip("set url for tile " + n)
        self.tileurl_actions[i].triggered.connect(self.web_widget.webTiles[i].askInput)
        if i >= self.tile_count:
            self.tileurl_actions[i].setVisible(False)
        self.tiles_menu.addAction(self.tileurl_actions[i])
        
    def close(self):
        self.web_widget.close()
    
    def locktiles(self):
        if self.lockStep == True:
            self.lockStep = False
            QSettings().setValue("lockstep", False)
        else:
            self.lockStep = True
            QSettings().setValue("lockstep", True)
        self.web_widget.lockSplitters(self.lockStep)

    def toggle4tiles(self):
        settings = QSettings()
        if settings.contains("show4tiles"):
            settings.remove("show4tiles")
            settings.sync()
            self.web_widget.removeSplit3()
            if len(self.web_widget.webTiles) >= 4:
                act_list = self.reload_menu.actions()
                print(act_list)
                self.reload_menu.actions()[3].setVisible(False)
                self.tiles_menu.actions()[3].setVisible(False)
        else:
            settings.setValue("show4tiles", True)
            settings.sync()
            self.web_widget.addSplit3()
            self.addTileMenuItems(3)
            if len(self.web_widget.webTiles) >= 4:
                act_list = self.reload_menu.actions()
                print(act_list)
                self.reload_menu.actions()[3].setVisible(True)
                self.tiles_menu.actions()[3].setVisible(True)


class WebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.parentprofile = profile

    def acceptNavigationRequest(self, url,  _type, isMainFrame):
        # print("$$", url.toString(), _type, isMainFrame)
        if _type == self.NavigationType.NavigationTypeLinkClicked:
            # print("Opening:", url.toString())
            webbrowser.get().open(url.toString())
        return True

    def createWindow(self, mode):
        self.external_view = QWebEngineView()
        external_page = WebEnginePage(self.parentprofile, self.external_view)
        self.external_view.setPage(external_page)
        return self.external_view.page()


class EngineView(QWebEngineView):
    _html_msg = """<!DOCTYPE html>
<html><head>
<style>
.center {{
  text-align: center;
  position: fixed;
  width: 100%;
}}
</style>
</head>
<body>
<div class="center">
<h2>{}</h2>
select "{} url" from the tiles menu to set a webpage
</div>
</body></html>"""
    def __init__(self, storename, tile_text):
        super(EngineView, self).__init__()
        self.name = storename

        profile = PyQt6.QtWebEngineCore.QWebEngineProfile(storename, self)
        self.webpage = WebEnginePage(profile, self)
        self.webpage.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

        self.setPage(self.webpage)
        self.page().profile().defaultProfile().setPersistentCookiesPolicy(PyQt6.QtWebEngineCore.QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        settings = QSettings()
        val = settings.value(storename)
        if val == None:
            self.setHtml(self._html_msg.format(tile_text, tile_text))
        else:
            self.setUrl(QUrl(val))
    
    def onFeaturePermissionRequested(self, url, feature):
        if feature in (
                PyQt6.QtWebEngineCore.QWebEnginePage.Feature.MediaAudioCapture, 
                PyQt6.QtWebEngineCore.QWebEnginePage.Feature.MediaVideoCapture, 
                PyQt6.QtWebEngineCore.QWebEnginePage.Feature.MediaAudioVideoCapture,
                PyQt6.QtWebEngineCore.QWebEnginePage.Feature.Notifications,
                PyQt6.QtWebEngineCore.QWebEnginePage.Feature.DesktopVideoCapture,
                PyQt6.QtWebEngineCore.QWebEnginePage.Feature.DesktopAudioVideoCapture,
            ):
            self.page().setFeaturePermission(url, feature, PyQt6.QtWebEngineCore.QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
        else:
            self.setFeaturePermission(url, feature, PyQt6.QtWebEngineCore.QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)

    def askInput(self):
        input_text = ""
        if len(self.url().toString()) >= 1:
            urltxt = self.url().toString()
            if urltxt.startswith("data:text/html") == False:
                input_text = urltxt

        box = InputBox().Ask(input_text)
        if box != "":
            self.setUrl(QUrl(box))
            settings = QSettings()
            settings.setValue(self.name, box)
    
    def close(self):
        del self.webpage


class WindowSplit(QSplitter):
    func = None
    widgetsadded = False
    myparent = None

    def __init__(self, parent):
        super(WindowSplit, self).__init__(parent)
        self.splitterMoved.connect(self.moveIt)
        self.myparent = parent

    def settingName(self, name):
        self.settingsName = name

    def loadSettings(self):
        settings = QSettings()
        val = settings.value(self.settingsName)
        if val != None:
            # print(">>", val)
            if platform.system() == "Darwin":
                self.setSizes(val)
            elif platform.system() == "Linux":
                intVal = []
                for v in val:
                    intVal.append(int(v))
                self.setSizes(intVal)
            else:
                print("** Unknown OS {} **".format(platform.system()))

    def saveSettings(self):
        settings = QSettings()
        settings.setValue(self.settingsName, self.sizes())
    
    def resetView(self):
        if self.orientation() == Qt.Orientation.Horizontal:
            hh = self.size().height() /2
            self.setSizes([int(hh),int(hh)])
        else:
            hw = self.size().width() /2
            self.setSizes([int(hw),int(hw)])
    
    def connect(self, funcname):
        self.func = funcname

    def moveIt(self, x,y):
        if self.func == None:
            return
        self.func(x,y)
        


class WebWindow(QWidget):
    webTiles = []
    show4Tiles = False
    split1 = None
    split2 = None
    split3 = None
    

    def __init__(self, parent):
        super(WebWindow, self).__init__(parent)
        # super().__init__()
        self.setWindowTitle("web tiles")

        self.webTiles = [
            EngineView("tile-store1", "Tile 1"),
            EngineView("tile-store2", "Tile 2"),
            EngineView("tile-store3", "Tile 3"),
        ]


        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Set the layout on the application's window
        # split 1 is the left hand horizontal split
        self.split1 = WindowSplit(Qt.Orientation.Vertical)
        self.split1.settingName("split1")
        self.split1.addWidget(self.webTiles[0])
        self.split1.addWidget(self.webTiles[1])
        self.split1.loadSettings()
        
        
        # split2 is the middle vertical split
        self.split2 = WindowSplit(Qt.Orientation.Horizontal)
        self.split2.settingName("split2")
        self.split2.addWidget(self.split1)

        if QSettings().contains("show4tiles"):
            print("+++ all four")
            self.show4Tiles = True
            if len(self.webTiles) < 4:
                self.webTiles.append(EngineView("tile-store4", "Tile 4"))
            # split 3 creates the right hand horizontal split
            self.split3 = self.createSplit3()
            #now add split3 to the right hand panel this creates a 4 tile view
            self.split2.addWidget(self.split3)
        else:
            self.show4Tiles = False
             # fill the whole right hand tile with tile number 3
            # split2.addWidget(webTiles[2])
            self.split2.addWidget(self.webTiles[2])

        # split2.loadSettings()
        self.split2.loadSettings()

        self.layout.addWidget(self.split2)
        self.setLayout(self.layout)

    def createSplit3(self):
        split = WindowSplit(Qt.Orientation.Vertical)
        split.settingName("split3")
        split.addWidget(self.webTiles[2])
        split.addWidget(self.webTiles[3])
        split.loadSettings()
        return split

    def addSplit3(self):
        self.show4Tiles = True
        if len(self.webTiles) < 4:
            self.webTiles.append(EngineView("tile-store4", "Tile 4"))
        
        self.split3 = self.createSplit3()
        self.split2.addWidget(self.split3)
        self.split2.loadSettings()
    
    def removeSplit3(self):
        self.show4Tiles = False
        self.split3.saveSettings()
        self.split2.saveSettings()
        self.split2.replaceWidget(1, self.webTiles[2])

    def page_reload(self):
        # print("reload called")
        for t in self.webTiles:
           t.reload()
        
    def resetView(self):
        if self.show4Tiles:
            self.split3.resetView()
        self.split2.resetView()
        self.split1.resetView()

    def close(self):
        if self.show4Tiles:
            self.split3.saveSettings()
        self.split2.saveSettings()
        self.split1.saveSettings()
        
        for i in self.webTiles:
            i.close()
    
    def lockSplitters(self, state):
        if state == False:
            self.split1.connect(None)
            if self.split3 != None:
                self.split3.connect(None)
        else:
            self.split1.connect(self.moveWith)

    def moveWith(self, x, y):
        if self.split3 == None:
            return

        if self.show4Tiles:
            self.split3.moveSplitter(x,y)
        


class InputBox(QInputDialog):
    def __init__(self, parent=None):
        super(InputBox, self).__init__(parent)
        self.resize(500,115) 

    def Ask(self, text):
        self.setLabelText("Enter a full vaild Url:") 
        self.setTextValue(text)
        ret = self.exec()
        if ret == 1:
            if self.textValue() != text:
                return self.textValue()

        return ""


if __name__ == "__main__":
    run_app()