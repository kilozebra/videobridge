# videobridge

## Description

Streaming live digital FPV footage from your DJI goggles to share with friends
is a lot of fun, but it can be a clunky, slow, and battery-punishing affair with
most of the existing tools and mobile devices.

This tool, in conjunction with the excellent
[mediamtx](https://github.com/bluenviron/mediamtx) package, aims to make that 
process a little smoother.  By avoiding transcoding and unnecessary buffering, 
it provides a maximum quality, minimal latency video stream to your browser or
broadcasting software (e.g. OBS) running on the same host or over the network.

**NOTE:** This code is very much a work in progress.


## Installation

**TODO:** python venv setup, module installation, etc.

**TODO:** install and configure mediamtx, set up service to autostart (download and configure golang env if necessary to build mediamtx)

**TODO:** install ffmpeg and libusb-1.0-0-dev

**TODO:** infinite-retry wrapper or unit files


## Usage

Upon startup, videobridge will search the USB bus for a set of DJI FPV Goggles,
look for a video signal from the air unit, and then begin feeding that signal
to the local mediamtx server (RTSP on port 8554).

(DJI FPV Goggles v2 have been tested, v1 should work also... Goggles 2 and Integra with
H.265 still need some NALU processing changes and testing).

**NOTE:** In the current version, if the goggles are unavailable, or a video
stream is not currently being received, or is not H.264, the code will exit
almost immediately with an exception.  For the time being, this needs to be run
inside an infinite loop, like a simple shell script or a service manager with no
retry backoff/failure counter.

Multiple local or network clients can connect to mediamtx over any supported
protocol (including HLS, RTMP, WebRTC, etc.) and stream the original video data
with no transcoding or extra delay.


## Credits / Prior Art

**TODO:** wtfos, fpvout, etc.  also reference materials for H.264 and H.265 NALU processing
