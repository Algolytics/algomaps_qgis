import os
import time

from qgis.core import (
    Qgis,
    QgsProject,
    QgsTask,
    QgsMessageLog,
    QgsCoordinateTransform,
    QgsField, QgsFeature, QgsVectorLayer,
    QgsGeometry, QgsPointXY
    )
from qgis.gui import QgisInterface

from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QObject, pyqtSignal

from .algomaps_qgis_dockwidget import AlgoMapsPluginDockWidget

DEBUG_MODE = True  # Verbose messages
TEMP_OUT_CSV = 'temp.csv'  # Ścieżka do pliku csv z wystandaryzowanymi i zgeokodowanymi adresami


# def _read_csv(csv_path, header_type=None, sep=None, quotechar='"'):
#     import pandas as pd
#     import pandas.errors
#     from .csv_utils import identify_header, get_file_line_count
#
#     # try:
#     #     header_type = identify_header(csv_path)
#     # except:
#     #     QgsMessageLog.logMessage(f"IDENTIFY HEADER ERROR", 'AlgoMaps', Qgis.MessageLevel.Warning)
#     #     return None
#
#     # Open CSV file into pandas DataFrame
#
#     try:
#         df = pd.read_csv(csv_path, header=header_type, engine='python', sep=None)
#     except pandas.errors.ParserError as e:
#         try:
#             df = pd.read_csv(csv_path, header=header_type, engine='python', sep=None, escapechar='\\')
#         except pandas.errors.ParserError as e:
#             try:
#                 df = pd.read_csv(csv_path, header=header_type, engine='python', sep=None, escapechar='\\', on_bad_lines='warn')
#                 QgsMessageLog.logMessage(f"CSV contains errors, skipped these lines", 'AlgoMaps', Qgis.MessageLevel.Warning)
#             except:
#                 QgsMessageLog.logMessage(f"READ CSV ERROR", 'AlgoMaps', Qgis.MessageLevel.Critical)
#                 return None
#     except:
#         QgsMessageLog.logMessage(f"ERROR", 'AlgoMaps', Qgis.MessageLevel.Warning)
#         return None
#
#     return df


class BatchGeocoder(QgsTask):
    def __init__(self, csv_path: str, column_roles: list, iface: QgisInterface,
                 dock_handle: AlgoMapsPluginDockWidget = None, qproj: QgsProject = None, dq_user: str = '',
                 dq_token: str = '', flags: dict = None, save_csv_path: str | None = None,
                 header_type: str | None = None, add_to_map: bool = True, sep: str = None, quote: str = '"'):
        super().__init__("AlgoMaps batch geocoding", QgsTask.CanCancel)

        self.csv_path = csv_path
        self.column_roles = column_roles

        # UI variables
        self.iface = iface
        self.dock_handle = dock_handle
        self.qproj = qproj

        # DQ settings
        self.dq_user = dq_user
        self.dq_token = dq_token
        self.job_name = 'ALGOMAPS QGIS'
        self.flags = flags if flags else {}

        # CSV params
        self.header_type = header_type
        self.save_csv_path = save_csv_path
        self.quotechar = quote
        self.sep = sep

        # Other
        self.add_to_map = add_to_map

        # Output placeholders
        self.report_dq = None
        self.exception = None
        self.df_results = None  # Output from DQ

        if self.dock_handle:
            self.dock_handle.btn_cancel_batch.clicked.connect(self.cancel)

        if Qgis.versionInt() > 33800:
            from qgis.PyQt.QtCore import QMetaType
            self._field_string_type = QMetaType.QString
            self._field_int_type = QMetaType.Int
            self._field_long_type = QMetaType.LongLong
            self._field_short_type = QMetaType.Short
            self._field_double_type = QMetaType.Double
            self._field_bool_type = QMetaType.Bool
        else:
            from qgis.PyQt.QtCore import QVariant
            self._field_string_type = QVariant.String
            self._field_int_type = QVariant.Int
            self._field_long_type = QVariant.LongLong
            self._field_short_type = QVariant.Int
            self._field_double_type = QVariant.Double
            self._field_bool_type = QVariant.Bool

    def _prepare_dq_job(self, job_name, flags, fields):

        from dq import DQClient, JobConfig

        dq = DQClient('https://app.dataquality.pl',
                      user=self.dq_user,
                      token=self.dq_token)

        job_config = JobConfig(job_name)
        job_config.module_std(address=1)
        job_config.extend(geocode=True,
                          diagnostic=True,
                          gus=flags.get('gus', False),
                          teryt=flags.get('teryt', False),
                          building_info=flags.get('buildinfo', False))#, area_characteristic=True)

        i = 0
        for column, role in fields.items():
            job_config.input_column(i, name=column, function=role)
            if DEBUG_MODE:
                QgsMessageLog.logMessage(f"job_config.input_column({i}, name={column}, function={role})",
                                         tag='AlgoMaps',
                                         level=Qgis.MessageLevel.Info)
            i += 1
        return dq, job_config

    def _dtype_to_qt_type(self, dtype):
        import numpy as np
        # Mapping dictionary
        dtype_to_qttype = {
            np.dtype('int64'): self._field_long_type,
            np.dtype('int32'): self._field_int_type,
            np.dtype('int16'): self._field_short_type,
            np.dtype('float64'): self._field_double_type,
            np.dtype('float32'): self._field_double_type,
            np.dtype('float16'): self._field_double_type,
            np.dtype('str_'): self._field_string_type,
            np.dtype('O'): self._field_string_type,
            np.dtype('bool'): self._field_bool_type
        }
        try:
            return dtype_to_qttype[dtype]
        except KeyError:
            return self._field_string_type
        except:
            raise

    def _add_to_map(self, df, job_name=''):

        fields_definitions = [QgsField(x, self._dtype_to_qt_type(t)) for x, t in df.dtypes.items()]

        # Add dataframe to layer
        layer_name = job_name

        # Create layer if not exists
        vl = QgsVectorLayer("Point?crs=epsg:4326", layer_name, "memory")
        self.qproj.addMapLayer(vl)

        pr = vl.dataProvider()

        pr.addAttributes([*fields_definitions])
        vl.updateFields()

        # Create feature
        def df_to_feature(row):
            try:
                lon = row["out_wsp_x"]
                lat = row["out_wsp_y"]

                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))

                # Set feature fields as layer fields
                f.setFields(vl.fields())

                # Populate fields values
                # TODO: NaNs
                for key, value in row.items():
                    f.setAttribute(key, value)

                pr.addFeature(f)
                return True
            except:
                return False

        df.apply(df_to_feature, axis=1)

        # Update layer
        vl.updateFields()
        vl.updateExtents()

        # Zoom to layer extent TODO?
        canvas = self.iface.mapCanvas()
        qproj = QgsProject.instance()
        dest_crs = qproj.crs()
        transform_context = qproj.transformContext()

        xform = QgsCoordinateTransform(vl.crs(), dest_crs, transform_context)
        canvas.setExtent(xform.transform(vl.extent()))
        canvas.refresh()

    def run(self):
        import csv
        import pandas as pd
        if DEBUG_MODE:
            QgsMessageLog.logMessage("READ CSV...", 'AlgoMaps', level=Qgis.MessageLevel.Info)

        # df = _read_csv(self.csv_path, self.header_type, self.sep, self.quotechar)

        # Read the csv file
        df = None
        try:
            df = pd.read_csv(self.csv_path, header=self.header_type, sep=self.sep, quotechar=self.quotechar,
                             escapechar='\\', engine='python')
        except pd.errors.ParserError as e:
            try:
                df = pd.read_csv(self.csv_path, header=self.header_type, sep=self.sep, engine='python',
                                 quotechar=self.quotechar, escapechar='\\',
                                 on_bad_lines='warn')  # TODO: function [partial(...)] instead of warn -> msgBox
                QgsMessageLog.logMessage(f"CSV contains some errors, skipped these lines", 'AlgoMaps',
                                         Qgis.MessageLevel.Warning)
            except pd.errors.ParserWarning as e:
                QgsMessageLog.logMessage(f"Skip line", 'AlgoMaps',
                                         Qgis.MessageLevel.Warning)
            except Exception:
                QgsMessageLog.logMessage(f"READ CSV ERROR", 'AlgoMaps',
                                         Qgis.MessageLevel.Critical)
                return None
        except Exception as e:
            QgsMessageLog.logMessage(f"UNKNOWN ERROR: {e}", 'AlgoMaps',
                                     Qgis.MessageLevel.Critical)
            return None

        if self.isCanceled():
            return False

        # DataFrame is empty
        if df is None:
            self.exception = 'Error while opening CSV file'
            return False

        # DataFrame processing
        if DEBUG_MODE:
            QgsMessageLog.logMessage("PROCESS DATAFRAME...", 'AlgoMaps', level=Qgis.MessageLevel.Info)

        if 'ID_REKORDU' not in self.column_roles:  # Use pandas index if ID_REKORDU is not present
            df = df.reset_index(drop=False)
            self.column_roles.insert(0, 'ID_REKORDU')

        col_names = list(df.columns)
        cols_dict = dict(zip(col_names, self.column_roles))

        from datetime import datetime
        self.job_name = f'ALGOMAPS QGIS test {str(datetime.now())}'
        dq, job_config = self._prepare_dq_job(self.job_name, self.flags, cols_dict)

        wejscie_dq = df.to_csv(None, sep=",", quotechar='"', encoding="utf-8",
                               quoting=csv.QUOTE_ALL, index=False)  # Jako string do importu w DQ-Client

        if self.isCanceled():
            return False

        # Send to DQ
        if DEBUG_MODE:
            QgsMessageLog.logMessage("SEND TO DQ...", 'AlgoMaps', level=Qgis.MessageLevel.Info)
        try:
            job = dq.submit_job(job_config, input_data=wejscie_dq)
        except Exception as e:
            self.exception = e
            return False

        QgsMessageLog.logMessage(f"Total elements (correct records) in csv: {len(df)}",
                                 tag='AlgoMaps',
                                 level=Qgis.MessageLevel.Info)

        # Wait for batch results
        timeout = 3600   # 1 hr
        sleep_time = 10  # [s]
        i = 0
        max_i = int(timeout / sleep_time)

        # Check DQ job status loop
        while True:
            if self.isCanceled():
                dq.cancel_job(job.id)
                return False

            state = dq.job_state(job.id)

            if state == 'FINISHED_PAID':  # Standaryzacja OK
                break

            elif state == 'FAILED':  # Brak środków na koncie / błąd
                QgsMessageLog.logMessage(f'FAILED', 'AlgoMaps', Qgis.MessageLevel.Critical)
                self.exception = 'DQ Status: FAILED'
                return False

            if i > max_i:  # Proces trwa zbyt długo
                QgsMessageLog.logMessage(f'TIMEOUT', 'AlgoMaps', Qgis.MessageLevel.Critical)
                self.exception = 'DQ Timeout'
                return False

            i += 1
            time.sleep(sleep_time)

        # Job finished
        try:
            if self.isCanceled():
                return False

            report = dq.job_report(job.id)
            if DEBUG_MODE:
                QgsMessageLog.logMessage(f'Report: {report.results}', 'AlgoMaps')

            if state == "FINISHED_PAID":
                QgsMessageLog.logMessage(f'Qualiy issues: {report.quality_issues}', 'AlgoMaps')
                QgsMessageLog.logMessage("Eksportuję zgeokodowane dane...", 'AlgoMaps')
                dq.job_results(job.id, TEMP_OUT_CSV)
                self.report_dq = report
            else:
                # TODO: retry
                return False

            if self.isCanceled():
                return False

            import pandas as pd
            self.df_results = pd.read_csv(TEMP_OUT_CSV)

            # Move to user's CSV or else remove the temporary CSV
            if self.save_csv_path:
                os.replace(TEMP_OUT_CSV, self.save_csv_path)
                QgsMessageLog.logMessage(f"Zapisano plik {self.save_csv_path}",
                                         'AlgoMaps',
                                         Qgis.MessageLevel.Info)
            else:
                os.remove(TEMP_OUT_CSV)
            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage("SUKCES.", 'AlgoMaps', Qgis.MessageLevel.Success)
            if self.dock_handle:
                import json
                job_report_str = str(self.report_dq).replace("'", '"')
                job_report_json = json.loads(job_report_str)
                self.dock_handle.txt_output_batch.setText(
                    json.dumps(job_report_json, indent=4, ensure_ascii=False).encode('utf8').decode())

            if self.add_to_map:
                self._add_to_map(self.df_results, self.job_name)  # TODO

        else:
            if self.isCanceled():
                QgsMessageLog.logMessage("CANCELED", 'AlgoMaps', Qgis.MessageLevel.Warning)
                if self.dock_handle:
                    self.dock_handle.txt_output_batch.setText('Zatrzymano przetwarzanie')
            elif self.exception is None:
                QgsMessageLog.logMessage("ERROR", 'AlgoMaps', Qgis.MessageLevel.Warning)
                if self.dock_handle:
                    self.dock_handle.txt_output_batch.setText('ERROR UNKNOWN')
            else:
                QgsMessageLog.logMessage(f"Exception {self.exception}", 'AlgoMaps', Qgis.MessageLevel.Warning)
                if self.dock_handle:
                    self.dock_handle.txt_output_batch.setText(f'Exception: \n{self.exception}')

        if self.dock_handle:
            self.dock_handle.progress_batch.setVisible(False)
            self.dock_handle.btn_cancel_batch.setVisible(False)
            self.dock_handle.btn_batch_process.setEnabled(True)
            self.dock_handle.btn_batch_process.setText('Rozpocznij przetwarzanie')

    def cancel(self):
        QgsMessageLog.logMessage('Task was canceled', 'AlgoMaps', Qgis.Info)
        super().cancel()
