import threading

from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.bike_speed_cadence import (
    BikeSpeedCadence,
    BikeSpeedData,
    BikeCadenceData,
)
from openant.devices.heart_rate import (
    HeartRateData
)
from openant.devices.power_meter import (
    PowerData
)

from AbstractSensorProxy import AbstractSensorProxy

WHEEL_CIRCUMFERENCE_M_700CX23 = 2.096
WHEEL_CIRCUMFERENCE_M_700CX25 = 2.109
WHEEL_CIRCUMFERENCE_M_700CX28 = 2.127

DEVICE_TYPE_HEART_RATE = 1
DEVICE_TYPE_POWER = 2
DEVICE_TYPE_CSC = 3


class ANTSensorProxy(AbstractSensorProxy):
    def __init__(self, device_type: int, device_id, connection_retries=3):
        super().__init__(connection_retries)
        self.device_type = device_type
        self.device_id = device_id
        self.node = None
        self.device = None

    def start(self):
        if self.running:
            pass
        self.running = True
        n_tries = 0
        while n_tries <= self.connection_retries and self.running:
            if n_tries > 0:
                print(f"ANT+ sensor {self.device_id}| retrying connection ({n_tries})")
            n_tries += 1
            try:
                t = threading.Thread(target=self._start_sensor_thread)
                t.start()
            except Exception as e:
                print(f"ANT+ sensor {self.device_id}| error starting thread: ({e})")

    def _start_sensor_thread(self):
        while self.running:
            try:
                if self.node is None:
                    self.node = Node()
                    self.node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
                    self.device = BikeSpeedCadence(self.node, self.device_id)
                    self.device.on_found = self.on_found
                    self.device.on_device_data = self.on_device_data
                self.node.start()
            finally:
                print(f"ANT+ sensor {self.device_id}| closing ...")
                if self.device is not None:
                    self.device.close_channel()
                if self.node is not None:
                    self.node.stop()

    def stop(self):
        print(f"ANT+ sensor {self.device_id}| stopping")
        self.running = False

    def on_found(self):
        print(f"Device {self.device} found and receiving")

    def on_device_data(self, page: int, page_name: str, data):
        print(f"Data received: {data}")
        if isinstance(data, BikeCadenceData):
            cadence = data.cadence
            if cadence:
                self.last_cadence_value = cadence
                print(f"cadence: {cadence} rpm")
        elif isinstance(data, BikeSpeedData):
            speed = data.calculate_speed(WHEEL_CIRCUMFERENCE_M_700CX25)
            if speed:
                self.last_speed_value = speed
                print(f"speed: {speed:.2f} km/h")
        elif isinstance(data, PowerData):
            power = data.instantaneous_power
            if power:
                self.last_power_value = power
                print(f"power: {power} W")
        elif isinstance(data, HeartRateData):
            hr = data.heart_rate
            if hr:
                self.last_hr_value = hr
                print(f"HR: {hr} bpm")

    # def store_csc_values(self, data: ):
    #     print(f"CSC DATA: {data}")
    #     cwr_data = data[1:5]
    #     cwr_time_data = data[5:7]
    #     ccr_data = data[7:9]
    #     ccr_time_data = data[9:11]
    #
    #     new_cwr_reading = int.from_bytes(cwr_data, 'little')
    #     new_cwr_time_reading = int.from_bytes(cwr_time_data, 'little')
    #     self.last_total_distance_value = new_cwr_reading*2109/1000000
    #     self.last_speed_value = (new_cwr_reading - self.last_cwr_reading)*2109/(new_cwr_time_reading - self.last_cwr_time_reading)*3.6
    #     self.last_cwr_reading = new_cwr_reading
    #     self.last_cwr_time_reading = new_cwr_time_reading
    #     print(f"Dist: {self.last_total_distance_value}")
    #     print(f"Speed: {self.last_speed_value}")
    #
    #     new_ccr_reading = int.from_bytes(ccr_data, 'little')
    #     new_ccr_time_reading = int.from_bytes(ccr_time_data, 'little')
    #     self.last_cadence_value = (new_ccr_reading - self.last_ccr_reading)/(new_ccr_time_reading - self.last_ccr_time_reading)*60000
    #     self.last_ccr_reading = new_ccr_reading
    #     self.last_ccr_time_reading = new_ccr_time_reading
    #     print(f"Cadence: {self.last_cadence_value}")
