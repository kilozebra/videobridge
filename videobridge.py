## global imports
from distutils.spawn import find_executable

import errno
import os
import signal
import subprocess
import sys
import time
import usb

## local imports
import djifpv

sink_uri = "rtsp://127.0.0.1:8554/live/djifpv"

ffmpeg_path = find_executable("ffmpeg")
ffm_cmd = [ 'ffmpeg',
		'-hide_banner',			## suppress config banner
		'-fflags', 'nobuffer',		## disable buffering
		'-flags', 'low_delay',		## minmize delay
		'-i', '-',			## read from stdin
		'-c:v', 'copy',			## don't transcode, just copy frames
		'-f', 'rtsp',			## use RTSP over TCP
		'-rtsp_transport', 'tcp'
	]

def info(count):
	## Periodically emit some statistics on the amount of data processed
	info.sent += count
	if info.loop and not info.loop % 1000:
		now = time.time()
		print("{:.2f} MB copied ({:.2f} Mb/s)     ".format(info.sent / 1024 / 1024, info.sent / 131072 / (now - info.last)), file=sys.stderr)
		info.last = now
		info.sent = 0
	info.loop = info.loop + 1
info.loop = info.sent = 0
info.last = time.time()


def do_stream():
	ffm = None

	try:
		## Initialize the DJI goggle video pipeline and get first data block
		data = djifpv.start()

		## Copy data until the video stops flowing
		while data:
			if ffm is None:
				ffm = subprocess.Popen(ffm_cmd + [sink_uri], stdin=subprocess.PIPE, text=False, executable=ffmpeg_path, bufsize=0)
			ffm.stdin.write(data)
			# info(len(data))
			data = djifpv.read()

		## Tear down the goggle connection
		djifpv.stop()
	except Exception as e:
		if isinstance(e, IOError):
			if e.errno == errno.ETIMEDOUT:
				## Video read timed out, no stream available.
				djifpv.stop()
			elif e.errno == errno.EIO:
				print("Goggles disconnected: {}".format(e), file=sys.stderr)
			elif e.errno == errno.ENODEV:
				print("Goggles not found: {}".format(e), file=sys.stderr)
			elif e.errno == errno.EBUSY:
				print("Goggle device busy: {}".format(e), file=sys.stderr)
				djifpv.stop()
			elif e.errno == errno.EPIPE:
				print("ffmpeg exited: {}".format(e), file=sys.stderr)
				djifpv.stop()
			else:
				print("Unable to initialize bulk USB endpoint: {}".format(e), file=sys.stderr)

			## Stop ffmpeg
			if ffm is not None:
				ffm.kill()
				ffm.wait()
		else:
			raise

while True:
	do_stream()
	time.sleep(1)
