# videobridge

## Description

Streaming live digital FPV footage from your DJI goggles to share with friends
is a lot of fun, but it can be a clunky, slow, and battery-punishing affair
with most of the existing tools and mobile devices.

This tool, in conjunction with the excellent
[mediamtx](https://github.com/bluenviron/mediamtx) package, aims to make that 
process a little smoother.  By avoiding transcoding and unnecessary buffering, 
it provides a maximum quality, minimal latency video stream to your browser or
broadcasting software (e.g. OBS) running on the same host or over the network.

[!IMPORTANT]
**Warning:** This code is very much a work in progress.


## Installation

**TODO:** python venv setup, module installation, etc.

**TODO:** install and configure mediamtx, set up service to autostart (download
and configure golang env if necessary to build mediamtx)

**TODO:** install ffmpeg and libusb-1.0-0-dev


## Usage

Upon startup, videobridge will search the USB bus for a set of DJI FPV Goggles,
open the USB bulk video input interface, and send the DJI DUML command to
initiate video streaming.

Once the compressed stream (AVC or HEVC elementary stream) starts arriving from
the goggles, videobridge will wait until the first complete SPS (sequence
parameter set) header arrives.  This SPS NALU is roughly equivalent to the 
start of an I-frame; all NAL units can be decoded without access to any data
arriving before the SPS NALU.  If stream synchronization fails, or the video
stream ends, videobridge will resume searching until a valid stream is found.

Once the stream is opened and synchronized, videobridge uses `ffmpeg` to
send the video data to a local mediamtx instance over RTSP (8554/tcp).
The mediamtx server then re-encapsulates and streams the video to clients.

[!NOTE]
*No more worrying about what order you plug things in!  videobridge will
automatically reconnect when your quad resumes sending video.*
(DJI FPV Goggles v2 have been tested, v1 should work also... Goggles 2 and
Integra with H.265 may work, but still needs testing.)

Multiple local or network clients can connect to mediamtx over any supported
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
the ITU specifications,
