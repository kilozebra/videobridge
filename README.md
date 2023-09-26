# videobridge

> [!IMPORTANT]
> This code is very much a work in progress.


## Description

Streaming live digital FPV footage from your DJI goggles to share with friends
is a lot of fun, but it can be a clunky, slow, and battery-punishing affair
with most of the existing tools and mobile devices.

This tool, in conjunction with the excellent
[mediamtx](https://github.com/bluenviron/mediamtx) package, aims to make that 
process a little smoother.  By avoiding transcoding and unnecessary buffering, 
it provides a maximum quality, minimal latency video stream to your browser or
broadcasting software (e.g. OBS) running on the same host or over the network.


## Prerequisites

* Python 3 (python3, python3-venv, python3-pip)
* ffmpeg ([documentation](https://ffmpeg.org/documentation.html))
* libusb-1.0 ([documentation](https://libusb.info/))

## Installation

1. Install python3, python3-venv, ffmpeg, and libusb-1.0 (might be
 `libusb` [OS X], `libusb-1.0-0` [Debian], etc.) using your system package manager.

   $ sudo apt install python3 python3-venv python3-pip ffmpeg libusb-1.0-0`

2. Install `mediamtx` using the [documentation](https://github.com/bluenviron/mediamtx#installation)
in that repository.  The rest of this process assumes that you have used the
default configuration and port numbers.  If a pre-built binary is unavailable
for your platform (e.g. arm64/aarch64), you may need to build mediamtx from
source using an appropriate golang environment.

3. (*Optional*) Configure mediamtx to [start on boot](https://github.com/bluenviron/mediamtx#start-on-boot).

4. Set up a Python 3 venv for the installation (will automatically create
parent directories as needed).

  $ sudo python3 -m venv /opt/videobridge/env

5. Copy code to install directory.

  $ sudo cp -r * /opt/videobridge

6. Install Python dependencies in the virtual environment.

  $ sudo /opt/videobridge/env/bin/python3 -m pip install -r /opt/videobridge/requirements.txt
  Collecting pyusb
    Downloading pyusb-1.2.1-py3-none-any.whl (58 kB)
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58.4/58.4 kB ? eta 0:00:00
  Installing collected packages: pyusb
  Successfully installed pyusb-1.2.1

7. (*Optional*) If you installed to somewhere other than `/opt/videobridge`.
modify the `DIR` variable in `run-videobridge.sh`.

For more information about Python 3 virtual environments, see the
[documentation](https://docs.python.org/3/library/venv.html).


## Usage

If `mediamtx` is not running already, start it.  Then start `videobridge`:

  $ sudo /opt/videobridge/run-videobridge.sh

Output from `videobridge` and `ffmpeg` will be mixed on stderr.

> [!NOTE]
> To avoid running as root, use a [udev](https://www.man7.org/linux/man-pages/man7/udev.7.html)
> rule to make the DJI Goggles accessible by a non-root user and/or group.

In a WebRTC-capable browser, go to `http://IP_ADDRESS:8889/live/djifpv`
(replace `IP_ADDRESS` with the address the device running mediamtx).

Power up your goggles, plug them in, and connect a battery to your craft.
After a few seconds, you should see the video appear in your browser.

For more playback protocol and client options, see the [Read from the server](https://github.com/bluenviron/mediamtx#read-from-the-server)
section of the mediamtx documentation.


## Details

Upon startup, `videobridge` will search the USB bus for a set of DJI FPV Goggles,
open the USB bulk video input interface, and send the DJI DUML command to
initiate video streaming.

Once the compressed stream (AVC or HEVC elementary stream) starts arriving from
the goggles, `videobridge` will wait until the first complete SPS (sequence
parameter set) header arrives.  This SPS NALU is roughly equivalent to the 
start of an I-frame; all subsequent NAL units can be decoded without access to
any data arriving before the SPS NALU.  If stream synchronization fails, or the
video stream ends, `videobridge` will resume searching until a valid stream is
found.

Once the stream is opened and synchronized, `videobridge` uses `ffmpeg` to
send the video data to a local `mediamtx` instance over RTSP (8554/tcp).
The `mediamtx` server then re-encapsulates and streams the video to clients.

> [!NOTE]
> *No more worrying about what order you plug things in!  `videobridge` will
> automatically reconnect when your air unit resumes sending video.*

(DJI FPV Goggles v2 have been tested, v1 should work also... Goggles 2 and
Integra with H.265 may work, but still require testing.)

Multiple local or network clients can connect to `mediamtx` over any supported
protocol (including HLS, RTMP, WebRTC, etc.) and stream the video data
with no transcoding or extra delay.  Depending on the local video decode and
display hardware that is available, a local client may even display the stream
in near real-time over an HDMI port or on a connected laptop display for a live
on-board preview.


## Credits / Prior Art

This work would not have been possible without the excellent open source
contributions from the [fpv-wtf team](https://github.com/fpv-wtf/) and their
[voc-poc](https://github.com/fpv-wtf/voc-poc/) demo code, as well as the
[FPV Out Club](https://github.com/fpvout).  These groups paved the way with
their discovery of the DUML command to enable the USB bulk video endpoint.

For help with stream synchronization and H.264/AVC and H.265/HEVC NAL (network
abstraction layer) unit parsing, I relied on the ITU's standards documents:
[ITU-T Rec. H.264 (08/2021)](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-H.264-202108-I!!PDF-E&type=items)
([archived](https://web.archive.org/web/20230424014548/https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-H.264-202108-I!!PDF-E&type=items))
(section 7.4, pages 63-67) and
[ITU-T Rec. H.265 (08/2021)](https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-H.265-202108-I!!PDF-E&type=items)
([archived](https://web.archive.org/web/20211118144215/https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-H.265-202108-I!!PDF-E&type=items))
(section 7.4, pages 64-68).
[Yumi Chan's blog](https://yumichan.net/video-processing/video-compression/introduction-to-h264-nal-unit/)
([archived](https://web.archive.org/web/20230330054552/https://yumichan.net/video-processing/video-compression/introduction-to-h264-nal-unit/))
has an outstanding overview of NALUs in plain English if you're confused by
the ITU specifications.
