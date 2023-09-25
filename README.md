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


## Usage

Upon startup, videobridge will search the USB bus for a set of DJI FPV Goggles,
look for a video signal from the air unit, and then begin feeding that signal
to the local mediamtx server (RTSP on port 8554).  It will continue retrying
until a valid video stream can be detected.  When the video stream ends, videobridge
will resume searching.  No more worrying about what order you plug things into 
the goggles -- videobridge will find your feed once it's live.

(DJI FPV Goggles v2 have been tested, v1 should work also... Goggles 2 and Integra with
H.265 may work, but still need testing.)

Multiple local or network clients can connect to mediamtx over any supported
protocol (including HLS, RTMP, WebRTC, etc.) and stream the original video data
with no transcoding or extra delay.  Depending on the local video decode and display
hardware that is available, a local client can even display the stream in near real-time
over an HDMI port or on a connected laptop display for a live preview.


## Credits / Prior Art

**TODO:** wtfos, fpvout, etc.  also reference materials for H.264 and H.265 NALU processing
