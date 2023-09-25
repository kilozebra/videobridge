from collections import namedtuple
import usb.core
import usb.util
import re
import sys

device = None
interface = None

def start():
	"""Initializes goggle USB device, sends DUML command requesting bulk video, and synchronizes to
	the first complete frame (Sequence Parameter Set).

	Returns:
	Array of bytes containing the first synchronized chunk of data (starts with NAL delimiter)
	"""

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
	"""Release USB device and discard pyusb resources."""
	global device
	global interface

	usb.util.dispose_resources(device)
	interface = None
	device = None

def read():
	"""Read data from a stream that has already been synchronized.

	Returns:
	bytes-like object containing the next chunk of video stream data

	Raises:
	ValueError -- stream is not yet synchronized
	"""
	global device
	global interface

	if not device or not interface:
		raise ValueError("Can't read from unsynchronized object, call start method to synchronize")
	return read_interface(device, interface)

def find_device():
	"""Find DJI FPV Goggles USB device.

	Returns:
	dev -- usb.core.Device handle to goggles

	Raises:
	IOError -- No device matching DJI Goggle USB identifiers
	"""

	## :TODO: Does this work with Goggles 2 and Integra?
	dev = usb.core.find(idVendor=0x2ca3, idProduct=0x1f)
	if dev is None:
		raise IOError("Can't find device");
	return dev

def setup_device(dev):
	"""Set up USB configuration for a set of detected goggles.  Open the USB bulk video endpoint
	and claim the associated interface.

	Keyword arguments:
	dev -- usb.core.Device handle to goggles

	Returns:
	usb.core.Interface associated with bulk video endpoint.
	"""

	cfg = dev.get_active_configuration()
	intf = cfg[(3,0)] ## DJI Bulk video is on Interface 3
	usb.util.claim_interface(dev, intf)
	# endpoint_out, endpoint_in = intf
	return intf

def read_interface(dev, intf):
	"""Convenience wrapper for usb.core.Device.read()

	Keyword arguments:
	dev -- usb.core.Device handle to goggles
	intf -- usb.core.Interface handle to the USB bulk video endpoint
	"""
	return dev.read(intf[1].bEndpointAddress, intf[1].wMaxPacketSize)

def write_interface(dev, intf, data):
	"""Convenience wrapper for usb.core.Device.write()

	Keyword arguments:
	dev -- usb.core.Device handle to goggles
	intf -- usb.core.Interface handle to the USB bulk video endpoint
	data -- bytes-like object
	"""
	return dev.write(intf[0], data, intf.bInterfaceNumber)

def seek_nalu(dev, intf, max_bytes=int(10e6)):
	"""Seek the USB bulk video input stream to find the first SPS NALU.  This marks a point
	in the stream where all subsequent NALUs can be decoded without any information prior
	to the SPS NALU.  This will let downstream tools like ffmpeg cleanly detect the elementary
	stream parameters without resynchronizing.

	Keyword arguments:
	dev -- usb.core.Device handle to goggles
	intf -- usb.core.Interface handle to the USB bulk video endpoint
	max_bytes -- int maximum number of bytes to read before giving up (<= 0 means try forever) (default: 10M)

	Returns:
	An array of bytes containing the first synchronized chunk of data from the stream (starts with SPS NALU delimiter)

	Raises:
	ValueError -- no SPS NALU found after reading max_bytes from the interface
	usb.core.USBTimeoutError -- goggle communication lost, probably unplugged
	"""

	sync = False
	parsed = 0
	held = None
	nal_delim = b"\x00\x00\x01"
	header_len = 2
	while not sync:
		if max_bytes > 0 and parsed >= max_bytes:
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
				## Read 2 bytes after NAL unit delimiter to determine unit type
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
	"""Decode header from an H.264 or H.265 Network Abstraction Layer Unit (NALU) and
	check if its type is SPS (Sequence Parameter Set).

	Keyword arguments:
	header -- the NAL unit header as a 16 bit int

	Returns:
	True if NAL unit type is SPS
	False if NAL unit type is not SPS
	"""

	forbidden_bit = (0x8000 & header) >> 15

	## H.264/AVC NAL header parsing
	# https://yumichan.net/video-processing/video-compression/introduction-to-h264-nal-unit/
	# https://web.archive.org/web/20230424014548/https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-H.264-202108-I!!PDF-E&type=items
	# pages 63-67
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
	# https://web.archive.org/web/20211118144215/https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-H.265-202108-I!!PDF-E&type=items
	# pages 64-68
	# 32		VPS
	# 33		SPS
	# 34		PPS
	# 35		AUD
	# 36		EOS
	# 37		EOB
	hevc_unit_type = (0x7f00 & header) >> 9;
	hevc_lid = (0x01f8 & header) >> 3;
	hevc_tid = (0x0007 & header)
	if forbidden_bit == 0 and hevc_unit_type == 33:
		#print("hevc header: {}, forbidden_bit: {}, hevc_unit_type: {}, hevc_lid: {}, hevc_tid: {}".format(header, forbidden_bit, hevc_unit_type, hevc_lid, hevc_tid))
		print("HEVC SPS found!", file=sys.stderr)
		return True

	## Type is not SPS
	return False
	


