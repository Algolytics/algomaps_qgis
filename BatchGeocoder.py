import urllib.request
import urllib.parse
import json

from qgis.core import (
    Qgis,
    QgsProject,
    QgsGeometry,
    QgsFeature,
    QgsTask,
    QgsMessageLog,
    QgsWkbTypes
    )

from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QObject, pyqtSignal


class BatchGeocoder(QgsTask):
    def __init__(self, csv_path, column_roles, iface, dock_handle=None):
        super().__init__("AlgoMaps batch geocoding", QgsTask.CanCancel)
        self.csv_path = csv_path
        self.column_roles = column_roles
        self.iface = iface
        self.dock_handle = dock_handle

    def run(self):
        QgsMessageLog.logMessage("SEND TO DQ...", 'AlgoMaps')
        import time
        import random

        roulette = random.randint(1, 5)
        time.sleep(1)

        if roulette == 1:
            return False

        return True

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage("SUKCES.", 'AlgoMaps', Qgis.MessageLevel.Success)
            if self.dock_handle:
                self.dock_handle.dockwidget.txt_output_batch.setText('{COŚ TU BĘDZIE}')
        else:
            QgsMessageLog.logMessage("ERROR?.", 'AlgoMaps', Qgis.MessageLevel.Warning)
            if self.dock_handle:
                self.dock_handle.dockwidget.txt_output_batch.setText('ERROR?')

        if self.dock_handle:
            self.dock_handle.dockwidget.progress_batch.setVisible(False)

    def cancel(self):
        QgsMessageLog.logMessage('Task was canceled', 'AlgoMaps', Qgis.Info)
        super().cancel()
