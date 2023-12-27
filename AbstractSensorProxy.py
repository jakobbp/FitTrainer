class AbstractSensorProxy:
    def __init__(self, connection_retries=3):
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

    def start(self):
        pass

    def stop(self):
        pass
