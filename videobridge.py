## global imports
import os
import signal
import subprocess
import sys
import time
import usb

## local imports
import djifpv

ffmpeg_path = "/usr/bin/ffmpeg"
sink_uri = "rtsp://127.0.0.1:8554/live/djifpv"

ffm_cmd = [ 'ffmpeg',
		'-hide_banner',			## suppress config banner
		'-fflags', 'nobuffer',		## disable buffering
		'-flags', 'low_delay',		## minmize delay
		'-i', '-',			## read from stdin
		'-c:v', 'copy',			## don't transcode, just copy frames
		'-f', 'rtsp',			## use RTSP over TCP
		'-rtsp_transport', 'tcp'
	]

def do_stream():
	ffm = subprocess.Popen(ffm_cmd + [sink_uri], stdin=subprocess.PIPE, text=False, executable=ffmpeg_path, bufsize=0)
	try:
		loop = 0
		csent = 0

		data = djifpv.start()
		last = time.time()

		epa = djifpv.interface[1].bEndpointAddress
		mps = djifpv.interface[1].wMaxPacketSize

		while data:
			ffm.stdin.write(data)
			## :NOTE: using only wMaxPacketSize results in terrible throughput
			data = djifpv.device.read(epa, mps << 4)

			csent += len(data)
			if loop and not loop % 5000:
				now = time.time()
				print("{:.2f} MB copied ({:.2f} Mb/s)     ".format(csent / 1024 / 1024, csent / 131072 / (now - last)), file=sys.stderr)
				last = now
				csent = 0
			loop = loop + 1

		djifpv.stop()
	except Exception as e:
		do_exit = False
		do_raise = False;

		if isinstance(e, IOError):
			if e.errno != 110:
				print("Unable to initialize bulk USB endpoint: {}".format(e), file=sys.stderr)
			else:
				djifpv.stop()
			ffm.kill()
			ffm.wait()
		else:
			raise

while True:
	do_stream()
	time.sleep(1)
