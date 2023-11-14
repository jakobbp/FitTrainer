import random
import time
import datetime

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.activity_message import ActivityMessage
from fit_tool.profile.messages.device_info_message import DeviceInfoMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.profile_type import FileType, Manufacturer, Sport, Event, EventType

DATA_POINT_TIME = 1
DATA_POINT_HEART_RATE = 2
DATA_POINT_POWER = 3
DATA_POINT_CADENCE = 4
DATA_POINT_SPEED = 5
DATA_POINT_DISTANCE = 6


class FitWriter:
    def __init__(self):
        self.file_name = None
        self.file_open = False
        self.output_file = None
        self.start_time = None

    def start_writing(self, file_name):
        print(f"Started writing: {file_name}")
        if self.file_open:
            self.stop_writing()
        self.file_name = file_name
        self.output_file = FitFileBuilder(auto_define=True, min_string_size=50)
        self.file_open = True

        start_time = round(datetime.datetime.now().timestamp() * 1000)
        self.start_time = start_time

        # FIle ID Message
        id_message = FileIdMessage()
        id_message.type = FileType.ACTIVITY
        id_message.manufacturer = Manufacturer.DEVELOPMENT.value
        id_message.product = 0
        id_message.time_created = start_time
        self.output_file.add(id_message)

        # Device Info Message
        dev_info_message = DeviceInfoMessage()
        dev_info_message.manufacturer = Manufacturer.DEVELOPMENT.value
        dev_info_message.product = 0
        dev_info_message.time_created = start_time
        dev_info_message.product_name = "JBP Trainer"
        dev_info_message.timestamp = start_time
        self.output_file.add(dev_info_message)

        # Start Timer Message
        start_message = EventMessage()
        start_message.event = Event.TIMER
        start_message.event_type = EventType.START
        start_message.timestamp = start_time
        self.output_file.add(start_message)

    def add_record(self, data_map):
        if self.file_open:
            print(f"Adding record: {data_map}")
            record_message = RecordMessage()
            record_message.timestamp = round(datetime.datetime.now().timestamp() * 1000)
            if DATA_POINT_TIME in data_map:
                # record_message.timestamp = data_map[DATA_POINT_TIME]
                record_message.timestamp = round(data_map[DATA_POINT_TIME] * 1000)
            if DATA_POINT_HEART_RATE in data_map:
                record_message.heart_rate = data_map[DATA_POINT_HEART_RATE]
            if DATA_POINT_POWER in data_map:
                record_message.power = data_map[DATA_POINT_POWER]
            if DATA_POINT_CADENCE in data_map:
                record_message.cadence = data_map[DATA_POINT_CADENCE]
            if DATA_POINT_SPEED in data_map:
                record_message.speed = data_map[DATA_POINT_SPEED]
            if DATA_POINT_DISTANCE in data_map:
                record_message.distance = data_map[DATA_POINT_DISTANCE]
            self.output_file.add(record_message)

    def stop_writing(self):
        print(f"Stopping writing: {self.file_name}")
        if self.output_file is not None:
            stop_time = round(datetime.datetime.now().timestamp() * 1000)

            # Stop Timer Message
            start_message = EventMessage()
            start_message.event = Event.TIMER
            start_message.event_type = EventType.STOP
            start_message.timestamp = stop_time
            self.output_file.add(start_message)

            # Lap Message
            lap_message = LapMessage()
            lap_message.start_time = self.start_time
            lap_message.total_elapsed_time = stop_time - self.start_time
            lap_message.total_timer_time = stop_time - self.start_time
            lap_message.timestamp = stop_time
            self.output_file.add(lap_message)

            # Session Message
            session_message = SessionMessage()
            session_message.start_time = self.start_time
            session_message.total_elapsed_time = stop_time - self.start_time
            session_message.total_timer_time = stop_time - self.start_time
            session_message.timestamp = stop_time
            session_message.sport = Sport.CYCLING
            self.output_file.add(session_message)

            # Activity Message
            activity_message = ActivityMessage()
            activity_message.start_time = self.start_time
            activity_message.total_elapsed_time = stop_time - self.start_time
            activity_message.total_timer_time = stop_time - self.start_time
            activity_message.timestamp = stop_time
            activity_message.sport = Sport.CYCLING
            activity_message.num_sessions = 1
            activity_message.local_timestamp = int(stop_time/1000)
            self.output_file.add(activity_message)

            # Write Fit File
            if self.file_name is None:
                self.file_name = "unknown.fit"
            self.output_file.build().to_file(self.file_name)
        self.file_open = False


# fw = FitWriter()
# # test_files = ["testfile1.fit", "testfile2.fit"]
# test_files = ["testfile1.fit"]
# for file_name in test_files:
#     fw.start_writing(file_name)
#     t0 = time.time()
#     for i in range(30):
#         hr = random.randint(120, 150)
#         power = random.randint(150, 180)
#         record_data = {
#             DATA_POINT_TIME: round(datetime.datetime.now().timestamp() * 1000),
#             DATA_POINT_HEART_RATE: hr,
#             DATA_POINT_POWER: power
#         }
#         fw.add_record(record_data)
#         print(f"Adding record: {record_data}")
#         time.sleep(1 - ((time.time()-t0) % 1))
#     fw.stop_writing()
#
# print("done")
