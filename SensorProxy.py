import asyncio
from bleak import BleakClient, BleakError, BleakGATTCharacteristic


GATT_CHAR_UUID_HEART_RATE = 1
GATT_CHAR_UUID_POWER = 2
GATT_CHAR_UUID_CSC = 3


class SensorProxy:
    def __init__(self, sensor_address, gatt_char_uuids_map: dict, pair=False, connection_retries=3):
        self.sensor_address = sensor_address
        self.gatt_char_uuids_map = gatt_char_uuids_map
        self.pair = pair
        self.connection_retries = connection_retries
        self.running = False

        self.last_hr_value = 0
        self.last_power_value = 0
        self.last_speed_value = 0
        self.last_cadence_value = 0
        self.last_total_distance_value = 0

        self.last_cwr_reading = 0
        self.last_cwr_time_reading = 0
        self.last_ccr_reading = 0
        self.last_ccr_time_reading = 0

    async def start(self):
        self.running = True
        n_tries = 0
        try:
            while n_tries <= self.connection_retries and self.running:
                if n_tries > 0:
                    print(f"{self.sensor_address}| retrying connection ({n_tries})")
                n_tries += 1
                async with BleakClient(self.sensor_address) as ble_client:
                    print(f"{self.sensor_address}| connected")
                    if self.pair:
                        paired = await ble_client.pair()
                        print(f"{self.sensor_address}| paired = {paired}")
                    if GATT_CHAR_UUID_HEART_RATE in self.gatt_char_uuids_map:
                        print(f"{self.sensor_address}| reading heart rate data")
                        await ble_client.start_notify(self.gatt_char_uuids_map[GATT_CHAR_UUID_HEART_RATE], self.store_hr_value)
                    if GATT_CHAR_UUID_POWER in self.gatt_char_uuids_map:
                        print(f"{self.sensor_address}| reading power data")
                        await ble_client.start_notify(self.gatt_char_uuids_map[GATT_CHAR_UUID_POWER], self.store_power_value)
                    if GATT_CHAR_UUID_CSC in self.gatt_char_uuids_map:
                        print(f"{self.sensor_address}| reading speed & cadence data")
                        await ble_client.start_notify(self.gatt_char_uuids_map[GATT_CHAR_UUID_CSC], self.store_csc_values)
                    while self.running:
                        await asyncio.sleep(0.5)
        except BleakError as e:
            print(f"{self.sensor_address}| connection error: {e}")

    def stop(self):
        print(f"{self.sensor_address}| stopping")
        self.running = False

    def store_hr_value(self, sender: BleakGATTCharacteristic, data: bytearray):
        relevant_data = data[:2]
        relevant_data[0] = 0
        self.last_hr_value = int.from_bytes(relevant_data, 'big')
        print(f"HR: {self.last_hr_value}")

    def store_power_value(self, sender: BleakGATTCharacteristic, data: bytearray):
        relevant_data = data[2:4]
        self.last_power_value = int.from_bytes(relevant_data, 'little')
        print(f"Power: {self.last_power_value}")

    def store_csc_values(self, sender: BleakGATTCharacteristic, data: bytearray):
        print(f"CSC DATA: {data}")
        cwr_data = data[1:5]
        cwr_time_data = data[5:7]
        ccr_data = data[7:9]
        ccr_time_data = data[9:11]

        new_cwr_reading = int.from_bytes(cwr_data, 'little')
        new_cwr_time_reading = int.from_bytes(cwr_time_data, 'little')
        self.last_total_distance_value = new_cwr_reading*2109/1000000
        self.last_speed_value = (new_cwr_reading - self.last_cwr_reading)*2109/(new_cwr_time_reading - self.last_cwr_time_reading)*3.6
        self.last_cwr_reading = new_cwr_reading
        self.last_cwr_time_reading = new_cwr_time_reading
        print(f"Dist: {self.last_total_distance_value}")
        print(f"Speed: {self.last_speed_value}")

        new_ccr_reading = int.from_bytes(ccr_data, 'little')
        new_ccr_time_reading = int.from_bytes(ccr_time_data, 'little')
        self.last_cadence_value = (new_ccr_reading - self.last_ccr_reading)/(new_ccr_time_reading - self.last_ccr_time_reading)*60000
        self.last_ccr_reading = new_ccr_reading
        self.last_ccr_time_reading = new_ccr_time_reading
        print(f"Cadence: {self.last_cadence_value}")


# async def testrun():
#     print("start")
#     # test = SensorProxy("C4:0D:01:89:C9:9F", {GATT_CHAR_UUID_POWER: '00002a63-0000-1000-8000-00805f9b34fb'}, pair=True)
#     # test = SensorProxy("C4:0D:01:89:C9:9F", {GATT_CHAR_UUID_CSC: '00002a5b-0000-1000-8000-00805f9b34fb'}, pair=True)
#     test = SensorProxy("C4:0D:01:89:C9:9F", {
#         GATT_CHAR_UUID_CSC: '00002a5b-0000-1000-8000-00805f9b34fb',
#         GATT_CHAR_UUID_POWER: '00002a63-0000-1000-8000-00805f9b34fb'}, pair=True)
#     test_task = asyncio.create_task(test.start())
#     print("sleeping")
#     sleep_task = asyncio.create_task(asyncio.sleep(60))
#     await sleep_task
#     print("done sleeping")
#     test.stop()
#     await test_task
#     print("done")
#
# asyncio.run(testrun())
