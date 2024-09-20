import time
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
DEBUG_MODE = True  # Verbose messages


def _read_csv(csv_path):
    import pandas as pd
    import pandas.errors
    from .csv_utils import identify_header, get_file_line_count

    try:
        header_type = identify_header(csv_path)
    except:
        QgsMessageLog.logMessage(f"IDENTIFY HEADER ERROR", 'AlgoMaps', Qgis.MessageLevel.Warning)
        return None

    # Open CSV file into pandas DataFrame

    try:
        df = pd.read_csv(csv_path, header=header_type, engine='python', sep=None)
    except pandas.errors.ParserError as e:
        try:
            df = pd.read_csv(csv_path, header=header_type, engine='python', sep=None, escapechar='\\')
        except pandas.errors.ParserError as e:
            try:
                df = pd.read_csv(csv_path, header=header_type, engine='python', sep=None, escapechar='\\', on_bad_lines='warn')
            except:
                QgsMessageLog.logMessage(f"READ DF ERROR", 'AlgoMaps', Qgis.MessageLevel.Warning)
                return None
    except:
        QgsMessageLog.logMessage(f"ERROR", 'AlgoMaps', Qgis.MessageLevel.Warning)
        # TODO message
        return None

    return df


class BatchGeocoder(QgsTask):
    def __init__(self, csv_path, column_roles, iface, dq_user, dq_token, dock_handle=None, save_to_csv=False, add_to_map=True):
        super().__init__("AlgoMaps batch geocoding", QgsTask.CanCancel)
        self.csv_path = csv_path
        self.column_roles = column_roles
        self.iface = iface
        self.dq_user = dq_user
        self.dq_token = dq_token
        self.dock_handle = dock_handle
        self.report_dq = None
        self.exception = None

        self.save_to_csv = save_to_csv
        self.add_to_map = add_to_map

        if self.dock_handle:
            self.dock_handle.dockwidget.btn_cancel_batch.clicked.connect(self.cancel)

        if Qgis.versionInt() > 33800:
            from qgis.PyQt.QtCore import QMetaType
            self._field_string_type = QMetaType.QString
            self._field_int_type = QMetaType.Int
            self._field_double_type = QMetaType.Double
        else:
            from qgis.PyQt.QtCore import QVariant
            self._field_string_type = QVariant.String
            self._field_int_type = QVariant.Int
            self._field_double_type = QVariant.Double

    def _prepare_dq_job(self, job_name, flags, fields):
        import time
        from datetime import datetime

        from dq import DQClient, JobConfig

        dq = DQClient('https://app.dataquality.pl',
                      user=self.dq_user,
                      token=self.dq_token)

        job_config = JobConfig(job_name + str(datetime.now()))
        job_config.module_std(address=1)
        job_config.extend(gus=False, geocode=True, diagnostic=True, teryt=True, building_info=False)

        i = 0
        for column, role in fields.items():
            job_config.input_column(i, name=column, function=role)
            if DEBUG_MODE:
                QgsMessageLog.logMessage(f"job_config.input_column({i}, name={column}, function={role})",
                                         tag='AlgoMaps',
                                         level=Qgis.MessageLevel.Info)
            i += 1
        return dq, job_config

    def _add_to_map(self, df):
        pass

    def run(self):
        import dq
        import csv

        QgsMessageLog.logMessage("SEND TO DQ...", 'AlgoMaps', level=Qgis.MessageLevel.Info)

        output_dq_csv = 'temp.csv'  # Ścieżka do pliku csv z wystandaryzowanymi i zgeokodowanymi adresami
        df = _read_csv(self.csv_path)

        # DataFrame is empty
        if df is None:
            return False

        #
        col_names = list(df.columns)
        cols_dict = dict(zip(col_names, self.column_roles))

        flags = [True, False, False, False]  # TODO: from checkbox
        dq, job_config = self._prepare_dq_job('ALGOMAPS QGIS test', flags, cols_dict)

        wejscie_dq = df.to_csv(None, sep=",", encoding="utf-8",
                               quoting=csv.QUOTE_ALL, index=False)  # Jako string do importu w DQ-Client

        try:
            job = dq.submit_job(job_config, input_data=wejscie_dq)
        except Exception as e:
            self.exception = e
            return False

        QgsMessageLog.logMessage(f"Total elements in csv: {len(df)}", 'AlgoMaps', Qgis.MessageLevel.Info)

        # Wait for batch results
        timeout = 3600   # 1 hr
        sleep_time = 10  # [s]
        i = 0
        max_i = int(timeout / sleep_time)

        while True:
            if self.isCanceled():
                dq.cancel_job(job.id)
                return False

            state = dq.job_state(job.id)

            if state == 'FINISHED_PAID':  # Standaryzacja OK
                break

            elif state == 'FAILED':  # Brak środków na koncie / błąd
                QgsMessageLog.logMessage(f'FAILED', 'AlgoMaps', Qgis.MessageLevel.Critical)
                return False

            if i > max_i:  # Proces trwa zbyt długo
                QgsMessageLog.logMessage(f'TIMEOUT', 'AlgoMaps', Qgis.MessageLevel.Critical)
                return False

            i += 1
            time.sleep(sleep_time)  # 1 minuta

        try:
            report = dq.job_report(job.id)
            QgsMessageLog.logMessage(f'Report: {report.results}', 'AlgoMaps')
            if state == "FINISHED_PAID":
                QgsMessageLog.logMessage(f'Qualiy issues: {report.quality_issues}', 'AlgoMaps')
                QgsMessageLog.logMessage("Eksportuję zgeokodowane dane...", 'AlgoMaps')
                dq.job_results(job.id, output_dq_csv)
                self.report_dq = report.results
            else:
                return False

            import pandas as pd
            self.df_results = pd.read_csv(output_dq_csv)
            # self.results_txt =
            return True
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage("SUKCES.", 'AlgoMaps', Qgis.MessageLevel.Success)
            if self.dock_handle:
                self.dock_handle.dockwidget.txt_output_batch.setText(str(self.report_dq))

            if self.add_to_map:
                self._add_to_map(self.df_results)  # TODO

        else:
            if self.isCanceled():
                QgsMessageLog.logMessage("CANCELED", 'AlgoMaps', Qgis.MessageLevel.Warning)
                if self.dock_handle:
                    self.dock_handle.dockwidget.txt_output_batch.setText('CANCELED?')
            elif self.exception is None:
                QgsMessageLog.logMessage("ERROR?.", 'AlgoMaps', Qgis.MessageLevel.Warning)
                if self.dock_handle:
                    self.dock_handle.dockwidget.txt_output_batch.setText('ERROR?')
            else:
                QgsMessageLog.logMessage(f"Exception {self.exception}", 'AlgoMaps', Qgis.MessageLevel.Warning)
                if self.dock_handle:
                    self.dock_handle.dockwidget.txt_output_batch.setText(f'{self.exception}')

        if self.dock_handle:
            self.dock_handle.dockwidget.progress_batch.setVisible(False)
            self.dock_handle.dockwidget.btn_cancel_batch.setVisible(False)
            self.dock_handle.dockwidget.btn_batch_process.setEnabled(True)
            self.dock_handle.dockwidget.btn_batch_process.setText('Rozpocznij przetwarzanie')

    def cancel(self):
        QgsMessageLog.logMessage('Task was canceled', 'AlgoMaps', Qgis.Info)
        super().cancel()
