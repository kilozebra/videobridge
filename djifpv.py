from collections import namedtuple
import usb.core
import usb.util
import re
import sys

device = None
interface = None

def start():
	global device
	global interface

	device = find_device()
	interface = setup_device(device)

	magic = b'RMVT'
	try:
		write_interface(device, interface, magic)
	except IOError as e:
		print("Failed to write trigger bytes to interface, no stream available: {}".format(e), file=sys.stderr)
		#raise

	return seek_nalu(device, interface)

def stop():
	global device
	global interface

	usb.util.dispose_resources(device)
	interface = None
	device = None

def read():
	global device
	global interface

	if not device or not interface:
		raise ValueError("Can't read from unsynchronized object, call start method to synchronize")
	return read_interface(device, interface)

def find_device():
	dev = usb.core.find(idVendor=0x2ca3, idProduct=0x1f)
	if dev is None:
		raise IOError("Can't find device");
	return dev

def setup_device(dev):
	cfg = dev.get_active_configuration()
	intf = cfg[(3,0)] ## DJI Bulk video is on Interface 3
	usb.util.claim_interface(dev, intf)
	# endpoint_out, endpoint_in = intf
	return intf

def read_interface(dev, intf):
	return dev.read(intf[1].bEndpointAddress, intf[1].wMaxPacketSize)

def write_interface(dev, intf, data):
	return dev.write(intf[0], data, intf.bInterfaceNumber)

def seek_nalu(dev, intf):
	sync = False
	parsed = 0
	held = None
	nal_delim = b"\x00\x00\x01"
	header_len = 2
	while not sync:
		if parsed > 10000000:
			raise ValueError("No sync primitive found")

		try:
			data = read_interface(dev, intf)
			parsed += len(data)

			## Add piece of the last chunk to find NALU delimiters crossing the chunk boundary
			if held:
				chunk = held + data
			else:
				chunk = data

			for match in re.finditer(nal_delim, chunk):
				## Read 2 butes after NAL unit delimiter to determine unit type
				header_start = match.start() + len(nal_delim)
				header = int.from_bytes(chunk[header_start:header_start + header_len], "big")
				sync = nal_unit(header)

				if sync:
					return chunk[match.start():]

				## Hold over the last part of the chunk
				held = chunk[-(len(nal_delim) + header_len):]
		except usb.core.USBTimeoutError:
			raise

def nal_unit(header):
	forbidden_bit = (0x8000 & header) >> 15

	## H.264/AVC NAL header parsing
	# https://web.archive.org/web/20170403144107/http://www-ee.uta.edu/dip/courses/ee5356/H264systems.pdf
	# Page 63
	# https://yumichan.net/video-processing/video-compression/introduction-to-h264-nal-unit/
	#
	# 0		unspecified
	# 1		coded slice of non-IDR picture
	# 2		coded slice data partition A
	# 3		coded slice data partition B
	# 4		coded slice data partition C
	# 5		coded slice of IDR picture
	# 6		SEI / Supplemental Enhancement Information
	# 7		SPS / Sequence Parameter Set
	# 8		PPS / Picture Parameter Set
	# 9		AUD / Access Unit Delimiter
	# 10		EOS / End of sequence
	# 11		EOB / End of bitstream
	# 12		Filler data of stream
	# 13..23	Reserved
	# 24..31	Unspecified
	avc_idc = (0x6000 & header) >> 13
	avc_unit_type = (0x1f00 & header) >> 8;
	if forbidden_bit == 0 and avc_idc == 3 and avc_unit_type == 7:
		#print("avc header: {}, forbidden_bit: {}, avc_idc: {}, avc_unit_type: {}".format(header, forbidden_bit, avc_idc, avc_unit_type))
		print("AVC SPS found!", file=sys.stderr)
		return True

	## H.265/HEVC NAL header parsing
	# file:///U:/docs/T-REC-H.265-202108-I!!PDF-E.pdf
	# page 66
	# 32		VPS
	# 33		SPS
	# 34		PPS
	# 35		AUD
	# 36		EOS
	# 37		EOB
	evc_unit_type = (0x7f00 & header) >> 9;
	evc_lid = (0x01f8 & header) >> 3;
	evc_tid = (0x0007 & header)
	if forbidden_bit == 0 and evc_unit_type == 33:
		#print("evc hea3 der: {}, forbidden_bit: {}, evc_unit_type: {}, evc_lid: {}, evc_tid: {}".format(header, forbidden_bit, evc_unit_type, evc_lid, evc_tid))
		print("EVC SPS found!", file=sys.stderr)
		return True

	## No valid stream found
	return False
	


