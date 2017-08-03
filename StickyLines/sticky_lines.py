# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StickyLines
                                 A QGIS plugin
 Redraw lines to follow existing lines of another layer
                              -------------------
        begin                : 2017-08-02
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Guillaume Silvent
        email                : guillaume.silvent@hotmail.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4 import QtCore
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QColor
# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from sticky_lines_dockwidget import StickyLinesDockWidget
import os.path

#ADDED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from qgis.core import QgsMapLayerRegistry, QgsMapLayer, QGis, QgsVectorLayer
import qgis


class StickyLines:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'StickyLines_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&StickyLines')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'StickyLines')
        self.toolbar.setObjectName(u'StickyLines')

        #print "** INITIALIZING StickyLines"

        self.pluginIsActive = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('StickyLines', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/StickyLines/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Make lines follow other line layer'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #MY CODE---------------------------------------------------------------
        self.hideGeometries()
        
        #print "** CLOSING StickyLines"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        
        #MY CODE---------------------------------------------------------------
        self.hideGeometries()
        
        #print "** UNLOAD StickyLines"
        
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&StickyLines'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING StickyLines"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = StickyLinesDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
            
            
        #MY CODE_______________________________________________________________
        self.tempLayer=None
        self.loadLineLayers()#chargement des couches lignes
        
        #connections des boutons-----------------------------------------------
        self.dockwidget.loadLayersButton.clicked.connect(
                self.loadLineLayers)
        self.dockwidget.editActiveButton.clicked.connect(
                lambda: self.selectActiveLayer(self.dockwidget.editCombo))
        self.dockwidget.modelActiveButton.clicked.connect(
                lambda: self.selectActiveLayer(self.dockwidget.modelCombo))
        self.dockwidget.startButton.clicked.connect(
                lambda: self.calculateGeometries(False))
        self.dockwidget.showGeometryButton.clicked.connect(
                lambda: self.calculateGeometries(True))
        self.dockwidget.hideGeometryButton.clicked.connect(
                lambda: self.hideGeometries(True))
        #refresh dock
        self.dockwidget.editCombo.currentIndexChanged.connect(
                self.countFeatures)
        self.dockwidget.modelCombo.currentIndexChanged.connect(
                self.countFeatures)
        self.dockwidget.editSelectedCheck.clicked.connect(
                self.countFeatures)
        self.dockwidget.modelSelectedCheck.clicked.connect(
                self.countFeatures)
            
        #connection signals Qgis-----------------------------------------------
        #QgsMapLayerRegistry.instance().layersWillBeRemoved.connect(self.loadLineLayers)
        #QgsMapLayerRegistry.instance().layerWasAdded.connect(self.loadLineLayers)
        
    def loadLineLayers(self):
        #nettoyage des combobox------------------------------------------------
        self.dockwidget.editCombo.clear()
        self.dockwidget.modelCombo.clear()
        #ajout des couches lignes aux combobox---------------------------------
        layers = self.iface.legendInterface().layers()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType(
                    ) in [QGis.Line]:
                self.dockwidget.editCombo.addItem( layer.name(), layer )
                self.dockwidget.modelCombo.addItem( layer.name(), layer )
                #deconnexion puis connexion de la selection--------------------
                QtCore.QObject.disconnect(
                            layer,QtCore.SIGNAL("selectionChanged()"),self.countFeatures)
                layer.selectionChanged.connect(self.countFeatures)
        self.countFeatures()
        
    def countFeatures(self,qtsignal=False):
        #recup des couches-----------------------------------------------------
        modelLayer=self.dockwidget.modelCombo.itemData(
                self.dockwidget.modelCombo.currentIndex())
        editLayer=self.dockwidget.editCombo.itemData(
                self.dockwidget.editCombo.currentIndex())
        
        if editLayer!=None and modelLayer!=None:
            #recup des entites-------------------------------------------------
            if self.dockwidget.modelSelectedCheck.isChecked():
                modelFeatures=modelLayer.selectedFeatures()
            else:
                modelFeatures=[feature for feature in modelLayer.getFeatures()]
            if self.dockwidget.editSelectedCheck.isChecked():
                editFeatures=editLayer.selectedFeatures()
            else:
                editFeatures=[feature for feature in editLayer.getFeatures()]
            
            #mise a jour des labels------------------------------------------------
            self.dockwidget.modelCountLabel.setText(str(len(modelFeatures))+' entites')
            self.dockwidget.editCountLabel.setText(str(len(editFeatures))+' entites')
    
    
    def selectActiveLayer(self,combobox=None):
        try:
            self.loadLineLayers()
            active=self.iface.activeLayer()
            indexActive=combobox.findData(active)
            if active.geometryType() != QGis.Line :
                raise Exception('not a line layer')
            combobox.setCurrentIndex(indexActive)
        except:
            QMessageBox.information(self.dockwidget,
                                    'erreur',
                                    "La couche active n'est pas une couche Lignes")
            
    def refresh_layers(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()
    
    def showGeometries(self,geoms):
        self.hideGeometries()
        geomType='LineString'
        #if geom.wkbType()==QGis.WKBPolygon:
        #    geomType='Polygon'
        #...
        crsId=self.iface.mapCanvas().mapRenderer().destinationCrs().authid()
        self.tempLayer=QgsVectorLayer(geomType+'?crs='+crsId, 'stickyLinesTemp' , "memory")
        for geom in geoms:
            feature=qgis.core.QgsFeature()
            feature.setGeometry(geom)
            self.tempLayer.dataProvider().addFeatures([feature])
            feature=None
        symbols = self.tempLayer.rendererV2().symbols()
        symbol = symbols[0]
        symbol.setColor(QColor.fromRgb(255,0,130))
        symbol.setWidth(1.5)
        QgsMapLayerRegistry.instance().addMapLayer(self.tempLayer, False)
        #ajoutercouche
        qgis.core.QgsProject.instance().layerTreeRoot().insertChildNode(
                0, qgis.core.QgsLayerTreeLayer(self.tempLayer))
        #mettre couche au dessus
    
    def hideGeometries(self,qtsignal=False):
        try:
            if type(self.tempLayer)==qgis.core.QgsVectorLayer:
                QgsMapLayerRegistry.instance().removeMapLayer(self.tempLayer)
                self.tempLayer=None
        except:
            pass
            
    def calculateGeometries(self,seulementGeometries=False):
        
        geoms=[]
        buffer=self.dockwidget.bufferSpin.value()
        
        #recup des couches-----------------------------------------------------
        modelLayer=self.dockwidget.modelCombo.itemData(
                self.dockwidget.modelCombo.currentIndex())
        editLayer=self.dockwidget.editCombo.itemData(
                self.dockwidget.editCombo.currentIndex())
        
        #recup des entites-----------------------------------------------------
        if self.dockwidget.modelSelectedCheck.isChecked():
            modelFeatures=modelLayer.selectedFeatures()
        else:
            modelFeatures=[feature for feature in modelLayer.getFeatures()]
        if self.dockwidget.editSelectedCheck.isChecked():
            editFeatures=editLayer.selectedFeatures()
        else:
            editFeatures=[feature for feature in editLayer.getFeatures()]
        
        if len(modelFeatures)==0 or len(editFeatures)==0:
            QMessageBox.information(None,
                    'annulation',
                    "pas de lignes a traiter")
            return
            
        
        #fabrication de la trace a suivre--------------------------------------
        traceModel=modelFeatures[0].geometry()
        for modelLayer in modelFeatures:
            traceModel=traceModel.combine(modelLayer.geometry())
        if traceModel.wkbType() not in [QGis.WKBLineString] :
            QMessageBox.information(None,
                    'annulation',
                    "Les lignes modeles ne se touchent pas ou la geometrie"+
                    " \nn'est pas valide, annulation du traitement")
            return
        lineModel=traceModel.asPolyline()
        
        #calcul des nouvelles traces-------------------------------------------
        for editFeature in editFeatures:
            lineEdit=editFeature.geometry().asPolyline()
            newLine=[]
            for i,point in enumerate(lineEdit):
                def followModel():
                    if i<len(lineEdit)-1:
                        tup2=traceModel.closestSegmentWithContext(lineEdit[i+1])
                        if tup[2]<=tup2[2]:
                            liste=enumerate(lineModel)
                            debut=tup[2]
                            fin=tup2[2]
                        else:
                            liste=reversed(list(enumerate(lineModel)))
                            debut=tup2[2]
                            fin=tup[2]
                        for i2,point2 in liste:
                            tup3=editFeature.geometry().closestSegmentWithContext(point2)
                            if i2>=debut and i2<fin and i==tup3[2]-1 and qgis.core.QgsDistanceArea().measureLine(point2, tup3[1])<buffer:
                                newLine.append(point2)
                tup=traceModel.closestSegmentWithContext(point)
                if qgis.core.QgsDistanceArea().measureLine(point, tup[1])>buffer:
                    newLine.append(point)
                    tup2=editFeature.geometry().closestSegmentWithContext(tup[1])
                    if tup2[2]-1==i:
                        followModel()
                else:
                    newLine.append(tup[1])
                    followModel()
                        
            trace=qgis.core.QgsGeometry.fromPolyline(newLine)
            
            #MISE A JOUR-------------------------------------------------------
            if seulementGeometries==False:
                self.showGeometries(geoms=[trace])
                reponse=QMessageBox.question(self.dockwidget,
                                             'confirmer',
                                             'confirmer le changement de geometrie',
                                             QMessageBox.Yes,
                                             QMessageBox.No)
                self.hideGeometries()
                if reponse==QMessageBox.Yes :
                    editLayer.dataProvider().changeGeometryValues({editFeature.id(): trace})
                    self.refresh_layers()
                    QMessageBox.information(None,
                        'succes',
                        "Geometrie changee avec succes!")
                else:
                    QMessageBox.information(None,
                        'annulation',
                        "Traitement annule pour cette geometrie")
            
            #GEOMETRIES--------------------------------------------------------
            geoms.append(trace)
        if seulementGeometries==True:
            self.showGeometries(geoms=geoms)