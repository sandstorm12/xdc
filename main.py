import xdc
import bleak
import yaml
import numpy as np


def on_device_report(message_id, message_bytes):
    # parse the message bytes as a characteristic
    parsed = xdc.DeviceReportCharacteristic.from_bytes(message_bytes)
    print(parsed)


def on_medium_payload_report(message_id, message_bytes):
    message_bytes = message_bytes[:28]

    print(message_bytes[:28], len(message_bytes[:28]))
    if len(message_bytes) > 20:
        data_segments = np.dtype([
                ('timestamp', np.uint32),
                ('euler_x', np.float32),
                ('euler_y', np.float32),
                ('euler_z', np.float32),
                ('free_acceleration_x', np.float32),
                ('free_acceleration_y', np.float32),
                ('free_acceleration_z', np.float32),
            ])
        human_readable_data = np.frombuffer(message_bytes, dtype=data_segments)
        formatted_data = str([x for x in human_readable_data.tolist()[0]][:-1])[1:-1]
        # formatted_data = self.bluetooth_device_address + ", " + formatted_data
        print(formatted_data)


def start(devices):
    dot = bleak.backends.device.BLEDevice(devices[0])

    # xdc.identify(dot)

    cc = xdc.ControlCharacteristic.from_bytes(b"\x01\x01\x10")

    with xdc.Dot(dot) as device:
        device.control_write(cc)
    
    async def arun():
        async with xdc.Dot(dot) as device:
            
            # asynchronously subscribe to notifications
            await device.adevice_report_start_notify(on_device_report)
            # await device.along_payload_start_notify(on_long_payload_report)
            await device.amedium_payload_start_notify(on_medium_payload_report)
            # await device.ashort_payload_start_notify(on_short_payload_report)

            # sleep for some amount of time, while pumping the message queue
            #
            # note: this differs from python's `sleep` function, because it doesn't cause the
            #       calling (asynchronous) thread to entirely sleep - it still processes any
            #       notifications that come in, unlike the synchronous API
            await asyncio.sleep(10)

            # (optional): unsubscribe to the notifications
            await device.adevice_report_stop_notify()
            await device.along_payload_stop_notify()
            await device.amedium_payload_stop_notify()
            await device.ashort_payload_stop_notify()

    # start running the async task from the calling thread (by making the calling thread fully
    # pump the event loop until the task is complete)

    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(arun())


def read_devices():
    with open("config.yaml") as handle:
        config = yaml.safe_load(handle)

    devices = config['devices']

    return devices


if __name__ == '__main__':
    devices = read_devices()
    
    start(devices)