# human-pose-estimation-3d-python-cpp

- RealSenseD435 (RGB) 480x640 + CPU Corei9 45 FPS (Depth is not used)

![ezgif com-gif-maker (16)](https://user-images.githubusercontent.com/33194443/139964887-97c322ed-acfd-436d-b2a6-f9ae1364704a.gif)

## 1. Run
### 1-1. RealSenseD435 (RGB) 480x640 + CPU Corei9 45 FPS (Depth is not used)
```bash
$ xhost +local: && \
docker run -it --rm \
-v `pwd`:/home/user/workdir \
-v /tmp/.X11-unix/:/tmp/.X11-unix:rw \
--device /dev/video0:/dev/video0:mwr \
--device /dev/video1:/dev/video1:mwr \
--device /dev/video2:/dev/video2:mwr \
--device /dev/video3:/dev/video3:mwr \
--device /dev/video4:/dev/video4:mwr \
--device /dev/video5:/dev/video5:mwr \
--net=host \
-e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
-e DISPLAY=$DISPLAY \
--privileged \
ghcr.io/pinto0309/openvino2tensorflow:latest
```
```bash
$ python3 human_pose_estimation_3d_demo.py \
--model models/openvino/FP16/human-pose-estimation-3d-0001_bgr_480x640.xml \
--device CPU \
--input 4
```
### 1-2. RealSenseD435 (RGB) 480x640 + iGPU (OpenCL)
```bash
$ xhost +local: && \
docker run -it --rm \
-v `pwd`:/home/user/workdir \
-v /tmp/.X11-unix/:/tmp/.X11-unix:rw \
--device /dev/video0:/dev/video0:mwr \
--device /dev/video1:/dev/video1:mwr \
--device /dev/video2:/dev/video2:mwr \
--device /dev/video3:/dev/video3:mwr \
--device /dev/video4:/dev/video4:mwr \
--device /dev/video5:/dev/video5:mwr \
--net=host \
-e LIBVA_DRIVER_NAME=iHD \
-e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
-e DISPLAY=$DISPLAY \
--privileged \
ghcr.io/pinto0309/openvino2tensorflow:latest
```
```bash
$ python3 human_pose_estimation_3d_demo.py \
--model models/openvino/FP16/human-pose-estimation-3d-0001_bgr_480x640.xml \
--device GPU \
--input 4
```
### 1-3. General USB Camera 480x640 + CPU
```bash
$ xhost +local: && \
docker run -it --rm \
-v `pwd`:/home/user/workdir \
-v /tmp/.X11-unix/:/tmp/.X11-unix:rw \
--device /dev/video0:/dev/video0:mwr \
--net=host \
-e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
-e DISPLAY=$DISPLAY \
--privileged \
ghcr.io/pinto0309/openvino2tensorflow:latest
```
```bash
$ python3 human_pose_estimation_3d_demo.py \
--model models/openvino/FP16/human-pose-estimation-3d-0001_bgr_480x640.xml \
--device GPU \
--input 0
```
## 2. Build
```bash
$ PYTHON_PREFIX=$(python3 -c "import sys; print(sys.prefix)") \
&& PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')") \
&& PYTHON_INCLUDE_DIRS=${PYTHON_PREFIX}/include/python${PYTHON_VERSION}

$ NUMPY_INCLUDE_DIR=$(python3 -c "import numpy; print(numpy.get_include())")

$ mkdir -p pose_extractor/build && cd pose_extractor/build

$ cmake \
-DPYTHON_INCLUDE_DIRS=${PYTHON_INCLUDE_DIRS} \
-DNUMPY_INCLUDE_DIR=${NUMPY_INCLUDE_DIR} ..

$ make && cp pose_extractor.so ../.. && cd ../..
```

## 3. Reference
1. https://github.com/openvinotoolkit/open_model_zoo/tree/2021.4.1/demos/human_pose_estimation_3d_demo/python
2. https://docs.openvino.ai/2021.4/omz_models_model_human_pose_estimation_3d_0001.html
