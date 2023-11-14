import sys
import time
import datetime
import asyncio
from PyQt5 import QtGui, QtCore, uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from threading import Timer

import SensorProxy
import FitWriter


class TrainerOverlayWindow(QMainWindow):
    def __init__(self, show_hr=True, show_power=True, show_cadence=True, show_speed=True, show_distance=True):
        QMainWindow.__init__(self)
        self.setWindowTitle("JBP Trainer")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setGeometry(
            QtWidgets.QStyle.alignedRect(
                QtCore.Qt.LeftToRight,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop,
                QtCore.QSize(320, 240),
                QtWidgets.qApp.desktop().availableGeometry()
        ))
        self.setStyleSheet("QLabel{font-size: 16pt; color: #00FF00; font-family: 'Courier New', monospace; font-weight: bold;}")

        self.show_hr = show_hr
        self.show_power = show_power
        self.show_cadence = show_cadence
        self.show_speed = show_speed
        self.show_distance = show_distance

        widget_y = 8
        widget_step = 32
        self.label_ctrl = QtWidgets.QLabel(self)
        self.label_ctrl.setStyleSheet("background-color: #00FF00;")
        self.label_ctrl.resize(widget_y, widget_y)
        self.label_ctrl.move(0, 0)

        self.label_time = QtWidgets.QLabel(" Time: 00:00:00", self)
        self.label_time.move(8, widget_y)
        self.label_time.adjustSize()
        widget_y += widget_step

        if show_hr:
            self.label_hr = QtWidgets.QLabel("   HR: ---BPM", self)
            self.label_hr.move(8, widget_y)
            self.label_hr.adjustSize()
            widget_y += widget_step

        if show_power:
            self.label_power = QtWidgets.QLabel("Power: ---W", self)
            self.label_power.move(8, widget_y)
            self.label_power.adjustSize()
            widget_y += widget_step

        if show_cadence:
            self.label_cad = QtWidgets.QLabel("  Cad: ---RPM", self)
            self.label_cad.move(8, widget_y)
            self.label_cad.adjustSize()
            widget_y += widget_step

        if show_speed:
            self.label_speed = QtWidgets.QLabel("Speed: --.-km/h", self)
            self.label_speed.move(8, widget_y)
            self.label_speed.adjustSize()
            widget_y += widget_step

        if show_distance:
            self.label_dist = QtWidgets.QLabel(" Dist: ---.--km", self)
            self.label_dist.move(8, widget_y)
            self.label_dist.adjustSize()

        self.recording = False
        self.start_time = 0
        self.update_gui_timer = None
        self.write_data_timer = None

        self.hr_sensor = None
        self.power_sensor = None
        self.cadence_sensor = None
        self.speed_sensor = None
        self.distance_sensor = None
        connect_sensors_timer = Timer(0.1, self.connect_sensors)
        connect_sensors_timer.start()

        print("end constructor")

    def update_gui_loop(self):
        while self.recording:
            self.label_time.setText(" Time: {}".format(self.get_elapsed_time()))
            if self.show_hr:
                self.label_hr.setText("   HR: {}".format(self.get_current_hr()))
            if self.show_power:
                self.label_power.setText("Power: {}".format(self.get_current_power()))
            if self.show_cadence:
                self.label_cad.setText("  Cad: {}".format(self.get_current_cadence()))
            if self.show_speed:
                self.label_speed.setText("Speed: {}".format(self.get_current_speed()))
            if self.show_distance:
                self.label_dist.setText(" Dist: {}".format(self.get_distance_travelled()))
            time.sleep(0.5)

    def connect_sensors(self):
        garmin_hr_belt = SensorProxy.SensorProxy("F4:86:48:60:E7:0D", {
            SensorProxy.GATT_CHAR_UUID_HEART_RATE: '00002a37-0000-1000-8000-00805f9b34fb'
            })
        tacx_flow = SensorProxy.SensorProxy("C4:0D:01:89:C9:9F", {
            # SensorProxy.GATT_CHAR_UUID_CSC: '00002a5b-0000-1000-8000-00805f9b34fb',
            SensorProxy.GATT_CHAR_UUID_POWER: '00002a63-0000-1000-8000-00805f9b34fb'
            })
        if self.show_hr:
            self.hr_sensor = garmin_hr_belt
        if self.show_power:
            self.power_sensor = tacx_flow
        if self.show_cadence:
            self.cadence_sensor = tacx_flow
        if self.show_speed:
            self.speed_sensor = tacx_flow
        if self.show_distance:
            self.distance_sensor = tacx_flow
        asyncio.run(self.start_sensor_tasks([garmin_hr_belt, tacx_flow]))

    def write_data(self):
        fit_writer = FitWriter.FitWriter()
        output_file = f"{datetime.datetime.now().strftime('%Y-%m-%dT%H_%M_%S')}.fit"
        fit_writer.start_writing(output_file)
        t0 = time.time()
        while self.recording:
            data_map = {}
            # data_map[FitWriter.DATA_POINT_TIME] = time.time()
            data_map[FitWriter.DATA_POINT_TIME] = datetime.datetime.now().timestamp()
            if self.hr_sensor is not None:
                data_map[FitWriter.DATA_POINT_HEART_RATE] = self.hr_sensor.last_hr_value
            if self.power_sensor is not None:
                data_map[FitWriter.DATA_POINT_POWER] = self.power_sensor.last_power_value
            if self.cadence_sensor is not None:
                data_map[FitWriter.DATA_POINT_CADENCE] = self.cadence_sensor.last_cadence_value
            if self.speed_sensor is not None:
                data_map[FitWriter.DATA_POINT_SPEED] = self.speed_sensor.last_speed_value
            if self.distance_sensor is not None:
                data_map[FitWriter.DATA_POINT_DISTANCE] = self.distance_sensor.last_total_distance_value
            fit_writer.add_record(data_map)
            time.sleep(1 - ((time.time()-t0) % 1))
        fit_writer.stop_writing()

    def mousePressEvent(self, event):
        if self.recording:
            self.stop_recording()
        elif event.buttons() == QtCore.Qt.MouseButton.RightButton:
            self.save_and_quit()
        else:
            self.start_recording()

    def start_recording(self):
        self.recording = True
        self.start_time = time.time()
        self.label_ctrl.setStyleSheet("background-color: #FF0000;")
        self.update_gui_timer = Timer(0.1, self.update_gui_loop)
        self.update_gui_timer.start()
        self.write_data_timer = Timer(0.1, self.write_data)
        self.write_data_timer.start()

    def stop_recording(self):
        self.recording = False
        self.label_ctrl.setStyleSheet("background-color: #00FF00;")

    def save_and_quit(self):
        self.hr_sensor.stop()
        self.power_sensor.stop()
        QtWidgets.qApp.quit()

    async def start_sensor_tasks(self, sensors):
        sensor_tasks = []
        for sensor in sensors:
            sensor_tasks.append(asyncio.create_task(sensor.start()))
            print(f"added task for sensor {sensor.sensor_address}")
        for sensor_task in sensor_tasks:
            await sensor_task
            print(f"ended task for a sensor")

    def get_elapsed_time(self):
        if self.start_time == 0:
            return "00:00:00"
        time_elapsed = time.time() - self.start_time
        ts = int(time_elapsed % 60)
        tm = int(time_elapsed / 60)
        th = int(time_elapsed / 3600)
        return f"{th:02d}:{tm:02d}:{ts:02d}"

    def get_current_hr(self):
        return f"{self.hr_sensor.last_hr_value}BPM"

    def get_current_power(self):
        return f"{self.power_sensor.last_power_value}W"

    def get_current_cadence(self):
        return f"{round(self.cadence_sensor.last_cadence_value)}RPM"

    def get_current_speed(self):
        return f"{self.speed_sensor.last_speed_value:.{2}f}km/h"

    def get_distance_travelled(self):
        return f"{self.distance_sensor.last_total_distance_value:.{2}f}km"


if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay_window = TrainerOverlayWindow(show_cadence=False, show_speed=False, show_distance=False)
    overlay_window.show()
    app.exec_()