#!/usr/bin/env python3
"""
 Copyright (c) 2019 Intel Corporation
 Copyright (c) 2021 Katsuya Hyodo
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import json
from argparse import ArgumentParser, SUPPRESS
from pathlib import Path

import cv2
import numpy as np

from modules.inference_engine import InferenceEngine
from modules.draw import Plotter3d, draw_poses
from modules.parse_poses import parse_poses


def rotate_poses(poses_3d, R, t):
    R_inv = np.linalg.inv(R)
    for pose_id in range(poses_3d.shape[0]):
        pose_3d = poses_3d[pose_id].reshape((-1, 4)).transpose()
        pose_3d[0:3] = np.dot(R_inv, pose_3d[0:3] - t)
        poses_3d[pose_id] = pose_3d.transpose().reshape(-1)

    return poses_3d


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Lightweight 3D human pose estimation demo. Press esc to exit, "p" to (un)pause video or process next image.',
        add_help=False
    )
    args = parser.add_argument_group('Options')
    args.add_argument(
        '-h',
        '--help',
        action='help',
        default=SUPPRESS,
        help='Show this help message and exit.'
    )
    args.add_argument(
        '-m',
        '--model',
        help='Required. Path to an .xml file with a trained model.',
        type=Path,
        required=True
    )
    args.add_argument(
        '-i',
        '--input',
        required=True,
        help='Required. An input to process. The input must be a single image, a folder of images, video file or camera id.'
    )
    args.add_argument(
        '-o',
        '--output',
        required=False,
        help='Optional. Name of the output file(s) to save.'
    )
    args.add_argument(
        '-limit',
        '--output_limit',
        required=False,
        default=1000,
        type=int,
        help='Optional. Number of frames to store in output. If 0 is set, all frames are stored.'
    )
    args.add_argument(
        '-d',
        '--device',
        help='Optional. Specify the target device to infer on: CPU, GPU, HDDL or MYRIAD. The demo will look for a suitable plugin for device specified (by default, it is CPU).',
        type=str, default='CPU'
    )
    args.add_argument(
        '--height_size',
        help='Optional. Network input layer height size.',
        type=int,
        default=256
    )
    args.add_argument(
        '--fx',
        type=np.float32,
        default=-1,
        help='Optional. Camera focal length.'
    )
    args = parser.parse_args()

    stride = 8
    inference_engine = InferenceEngine(args.model, args.device, stride)
    canvas_3d = np.zeros((480, 640, 3), dtype=np.uint8)
    plotter = Plotter3d(canvas_3d.shape[:2])
    rgb_windows_name = '3D Human Pose Estimation'
    canvas_3d_window_name = 'Canvas 3D'
    cv2.namedWindow(rgb_windows_name, cv2.WINDOW_NORMAL)
    cv2.namedWindow(canvas_3d_window_name)
    cv2.setMouseCallback(canvas_3d_window_name, Plotter3d.mouse_callback)

    file_path = Path(__file__).parent / 'data/extrinsics.json'
    with open(file_path, 'r') as f:
        extrinsics = json.load(f)
    R = np.array(extrinsics['R'], dtype=np.float32)
    t = np.array(extrinsics['t'], dtype=np.float32)

    try:
        cap = cv2.VideoCapture(int(args.input))
    except:
        cap = cv2.VideoCapture(args.input)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    ret, frame = cap.read()
    if frame is None:
        raise RuntimeError("Can't read an image from the input")

    video_writer = cv2.VideoWriter()
    if args.output and not video_writer.open(
        args.output,
        cv2.VideoWriter_fourcc(*'MJPG'),
        cap.fps(),
        (frame.shape[1], frame.shape[0])
    ):
        raise RuntimeError("Can't open video writer")

    base_height = args.height_size
    fx = args.fx

    frames_processed = 0
    delay = 1
    esc_code = 27
    p_code = 112
    space_code = 32
    mean_time = 0

    while frame is not None:
        current_time = cv2.getTickCount()
        input_scale = base_height / frame.shape[0]
        scaled_img = cv2.resize(frame, dsize=None, fx=input_scale, fy=input_scale)
        if fx < 0:  # Focal length is unknown
            fx = np.float32(0.8 * frame.shape[1])

        inference_result = inference_engine.infer(scaled_img)
        poses_3d, poses_2d = parse_poses(inference_result, input_scale, stride, fx)
        edges = []
        if len(poses_3d) > 0:
            poses_3d = rotate_poses(poses_3d, R, t)
            poses_3d_copy = poses_3d.copy()
            x = poses_3d_copy[:, 0::4]
            y = poses_3d_copy[:, 1::4]
            z = poses_3d_copy[:, 2::4]
            poses_3d[:, 0::4], poses_3d[:, 1::4], poses_3d[:, 2::4] = -z, x, -y

            poses_3d = poses_3d.reshape(poses_3d.shape[0], 19, -1)[:, :, 0:3]
            edges = (Plotter3d.SKELETON_EDGES + 19 * np.arange(poses_3d.shape[0]).reshape((-1, 1, 1))).reshape((-1, 2))
        plotter.plot(canvas_3d, poses_3d, edges)

        draw_poses(frame, poses_2d)
        current_time = (cv2.getTickCount() - current_time) / cv2.getTickFrequency()
        if mean_time == 0:
            mean_time = current_time
        else:
            mean_time = mean_time * 0.95 + current_time * 0.05
        cv2.putText(
            frame,
            f'FPS: {int(1 / mean_time * 10) / 10}',
            (40, 80),
            cv2.FONT_HERSHEY_COMPLEX,
            1,
            (0, 0, 255)
        )

        frames_processed += 1
        if video_writer.isOpened() and (args.output_limit <= 0 or frames_processed <= args.output_limit):
            video_writer.write(frame)

        cv2.imshow(canvas_3d_window_name, canvas_3d)
        cv2.imshow(rgb_windows_name, frame)

        key = cv2.waitKey(1)
        if key == esc_code:  # ESC
            break
        ret, frame = cap.read()

