# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import sys

import aria.sdk as aria

import cv2
import numpy as np
from collections import deque

from common import ctrl_c_handler, quit_keypress, update_iptables

from projectaria_tools.core.calibration import (
    device_calibration_from_json_string,
    distort_by_calibration,
    get_linear_camera_calibration,
)
from projectaria_tools.core.sensor_data import ImageDataRecord

from pylsl import StreamInfo, StreamOutlet, StreamInlet, local_clock, resolve_byprop


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--interface",
        dest="streaming_interface",
        type=str,
        required=True,
        help="Type of interface to use for streaming. Options are usb or wifi.",
        choices=["usb", "wifi"],
    )
    parser.add_argument(
        "--update_iptables",
        default=False,
        action="store_true",
        help="Update iptables to enable receiving the data stream, only for Linux",
    )
    parser.add_argument(
        "--profile",
        dest="profile_name",
        type=str,
        default="profile18",
        required=False,
        help="Profile to be used for streaming.",
    )
    parser.add_argument(
        "--device-ip", help="IP address to connect to the device over wifi"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.update_iptables and sys.platform.startswith("linux"):
        update_iptables()

    #  Optional: Set SDK's log level to Trace or Debug for more verbose logs. Defaults to Info
    aria.set_log_level(aria.Level.Info)

    # 1. Create DeviceClient instance, setting the IP address if specified
    device_client = aria.DeviceClient()

    client_config = aria.DeviceClientConfig()
    if args.device_ip:
        client_config.ip_v4_address = args.device_ip
    device_client.set_client_config(client_config)

    # 2. Connect to the device
    device = device_client.connect()

    # 3. Retrieve the device streaming_manager and streaming_client
    streaming_manager = device.streaming_manager
    streaming_client = streaming_manager.streaming_client

    # 4. Use a custom configuration for streaming
    streaming_config = aria.StreamingConfig()
    streaming_config.profile_name = args.profile_name
    # Note: by default streaming uses Wifi
    if args.streaming_interface == "usb":
        streaming_config.streaming_interface = aria.StreamingInterface.Usb
    streaming_config.security_options.use_ephemeral_certs = True
    streaming_manager.streaming_config = streaming_config

    # 5. Get sensors calibration
    sensors_calib_json = streaming_manager.sensors_calibration()
    sensors_calib = device_calibration_from_json_string(sensors_calib_json)
    rgb_calib = sensors_calib.get_camera_calib("camera-rgb")

    dst_calib = get_linear_camera_calibration(512, 512, 150, "camera-rgb")

    # 6. Start streaming
    streaming_manager.start_streaming()

    # 7. Configure subscription to listen to Aria's RGB stream.
    config = streaming_client.subscription_config
    config.subscriber_data_type = aria.StreamingDataType.Rgb
    streaming_client.subscription_config = config

    # 8. Create and attach the visualizer and start listening to streaming data
    class StreamingClientObserver:
        def __init__(self):
            self.rgb_image = None

        def on_image_received(self, image: np.array, record: ImageDataRecord):
            self.rgb_image = image

    observer = StreamingClientObserver()
    streaming_client.set_streaming_client_observer(observer)
    streaming_client.subscribe()

    # 9. Render the streaming data until we close the window
    rgb_window = "Aria RGB"
    undistorted_window = "Undistorted RGB"
    marker_window = "Detected marker window"
    
    """cv2.namedWindow(marker_window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(marker_window, 512, 512)
    cv2.setWindowProperty(marker_window, cv2.WND_PROP_TOPMOST, 1)
    cv2.moveWindow(marker_window, 1500, 50)"""
    
    # Define the dictionary and parameters
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()

    # Create the ArUco detector
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    # id of centermost detected marker
    center_id = deque([-1]*20)
    
    #setup LSL stream
    name = "DetectedMarkers"
    type = "marker_id"
    n_channels = 1
    srate = 10
    uid = "1WM09370051264"  #SN of Aria glasses
    
    # first create a new stream info
    info = StreamInfo(name, type, n_channels, srate, "int32", uid)
    
    # now attach some meta-data (in accordance with XDF format,
    # see also https://github.com/sccn/xdf/wiki/Meta-Data)
    chns = info.desc().append_child("channels")
    ch_labels = ["marker id"]
    for label in ch_labels:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("unit", "/")
        ch.append_child_value("type", "marker_id")
    info.desc().append_child_value("manufacturer", "Project Aria")
    cap = info.desc().append_child("cap")
    cap.append_child_value("name", "Aria")
    cap.append_child_value("size", "1")
    cap.append_child_value("labelscheme", "10-20")
    
    # next make an outlet
    outlet = StreamOutlet(info)
    
    print("now sending data...")
    start_time = local_clock()
    
    """# listen to the same stream
    print("looking for a marker id stream...")
    streams = resolve_byprop("type", "marker_id")

    # create a new inlet to read from the stream
    inlet = StreamInlet(streams[0])"""
    
    with ctrl_c_handler() as ctrl_c:
        while not (quit_keypress() or ctrl_c):
            if observer.rgb_image is not None:
                rgb_image = cv2.cvtColor(observer.rgb_image, cv2.COLOR_BGR2RGB)

                # Apply the undistortion correction
                undistorted_rgb_image = distort_by_calibration(
                    rgb_image, dst_calib, rgb_calib
                )
                
                # Convert the image to grayscale
                gray = cv2.cvtColor(undistorted_rgb_image, cv2.COLOR_BGR2GRAY)

                # Detect the markers
                corners, ids, rejected = detector.detectMarkers(gray)
                #print("Detected markers:", ids)

                if ids is not None:
                    img_size = undistorted_rgb_image.shape
                    for i in range(len(ids)):
                        corner_points = corners[i][0]  # Get the four corner points
                        center_x = np.mean(corner_points[:, 0])  # Average X coordinates
                        center_y = np.mean(corner_points[:, 1])  # Average Y coordinates
                        center = (int(center_x), int(center_y))
                        
                        center_id.rotate(-1)
                        if 0.35*img_size[0] <= center_y <= 0.45*img_size[0] and 0.45*img_size[1] <= center_x <= 0.55*img_size[1]:
                            center_id[-1] = int(ids[i][0])
                        else:
                            center_id[-1] = -1
                    #print("Center id: ", center_id)
                    
                    #check if center_id has stayed the same for the past 20 samples
                    if center_id == deque([center_id[-1]]*20) and center_id[-1] != -1:
                        print("Chosen marker id: ", center_id[-1])
                        center_id = deque([-1]*20)  #reset buffer so we don't get multiple confirmations
                        print('\a')     #make alert noise to confirm marker choice

                        # Draw the marker center
                        #cv2.circle(undistorted_rgb_image, center, 5, (0, 0, 255), -1)
                        
                    #cv2.aruco.drawDetectedMarkers(undistorted_rgb_image, corners, ids)
                    #cv2.imshow(marker_window, np.rot90(undistorted_rgb_image, -1))
                    
                    """sample, timestamp = inlet.pull_sample()
                    print(timestamp, sample)"""
                else:
                    center_id.rotate(-1)
                    center_id[-1] = -1

                timestamp = local_clock()   #get current timestamp (not needed?)
                outlet.push_sample([center_id[-1]])    #push sample

                observer.rgb_image = None

    # 10. Unsubscribe from data and stop streaming
    print("Stop listening to image data")
    streaming_client.unsubscribe()
    streaming_manager.stop_streaming()
    device_client.disconnect(device)


if __name__ == "__main__":
    main()
