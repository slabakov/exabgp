"""
prefix.py

Created by Diego Garcia del Rio on 2015-03-12.
Copyright (c) 2015 Alcatel-Lucent. All rights reserved.

Based on work by Thomas Morin on mac.py
Copyright (c) 2014-2015 Orange. All rights reserved.
Copyright (c) 2014-2015 Exa Networks. All rights reserved.
"""

from exabgp.protocol.ip import IP
from exabgp.bgp.message.update.nlri.qualifier import RouteDistinguisher
from exabgp.bgp.message.update.nlri.qualifier import Labels
from exabgp.bgp.message.update.nlri.qualifier import ESI
from exabgp.bgp.message.update.nlri.qualifier import EthernetTag

from exabgp.bgp.message.update.nlri import NLRI
from exabgp.bgp.message.update.nlri.evpn.nlri import EVPN

from exabgp.bgp.message.notification import Notify


# ------------ EVPN Prefix Advertisement NLRI ------------
# As described here:
# http://tools.ietf.org/html/draft-ietf-bess-evpn-prefix-advertisement-01

# +---------------------------------------+
# |      RD   (8 octets)                  |
# +---------------------------------------+
# |Ethernet Segment Identifier (10 octets)|
# +---------------------------------------+
# |  Ethernet Tag ID (4 octets)           |
# +---------------------------------------+
# |  IP Prefix Length (1 octet)           |
# +---------------------------------------+
# |  IP Prefix (4 or 16 octets)           |
# +---------------------------------------+
# |  GW IP Address (4 or 16 octets)       |
# +---------------------------------------+
# |  MPLS Label (3 octets)                |
# +---------------------------------------+
# total NLRI length is 34 bytes for IPv4 or 58 bytes for IPv6

# ======================================================================= Prefix


@EVPN.register
class Prefix (EVPN):
	CODE = 5
	NAME = "IP Prefix advertisement"
	SHORT_NAME = "PrfxAdv"

	def __init__(self, rd, esi, etag, label, ip, iplen, gwip, packed=None,nexthop=None,action=None,addpath=None):
		'''
		rd: a RouteDistinguisher
		esi: an EthernetSegmentIdentifier
		etag: an EthernetTag
		mac: a MAC
		label: a LabelStackEntry
		ip: an IP address (dotted quad string notation)
		iplen: prefixlength for ip (defaults to 32)
		gwip: an IP address (dotted quad string notation)
		'''
		EVPN.__init__(self,packed,nexthop,action,addpath)
		self.rd = rd
		self.esi = esi
		self.etag = etag
		self.ip = ip
		self.iplen = iplen
		self.gwip = gwip
		self.label = label
		self.label = label if label else Labels.NOLABEL
		self.pack()

	def __eq__ (self, other):
		return \
			NLRI.__eq__(self,other) and \
			self.CODE == other.CODE and \
			self.rd == other.rd and \
			self.etag == other.etag and \
			self.ip == other.ip and \
			self.iplen == other.iplen
		# esi, label and gwip must not be compared

	def __ne__ (self, other):
		return not self.__eq__(other)

	def __str__ (self):
		return "%s:%s:%s:%s:%s%s:%s:%s" % (
			self._prefix(),
			self.rd._str(),
			self.esi,
			self.etag,
			self.ip,
			"/%d" % self.iplen,
			self.gwip,
			self.label
		)

	def __hash__ (self):
		# esi, and label, gwip must *not* be part of the hash
		return hash("%s:%s:%s:%s" % (self.rd,self.etag,self.ip,self.iplen))

	def _pack (self):
		if not self.packed:
			value = "%s%s%s%s%s%s%s" % (
				self.rd.pack(),
				self.esi.pack(),
				self.etag.pack(),
				chr(self.iplen),
				self.ip.pack(),
				self.gwip.pack(),
				self.label.pack(),
			)
			self.packed = value
		return self.packed

	@classmethod
	def unpack (cls, exdata):
		data = exdata

		# Get the data length to understand if addresses are IPv4 or IPv6
		datalen = len(data)

		rd = RouteDistinguisher.unpack(data[:8])
		data = data[8:]

		esi = ESI.unpack(data[:10])
		data = data[10:]

		etag = EthernetTag.unpack(data[:4])
		data = data[4:]

		iplen = ord(data[0])
		data = data[1:]

		if datalen == (26 + 8):  # Using IPv4 addresses
			ip = IP.unpack(data[:4])
			data = data[4:]
			gwip = IP.unpack(data[:4])
			data = data[4:]
		elif datalen == (26 + 32):  # Using IPv6 addresses
			ip = IP.unpack(data[:16])
			data = data[16:]
			gwip = IP.unpack(data[:16])
			data = data[16:]
		else:
			raise Notify(3,5,"Data field length is given as %d, but EVPN route currently support only IPv4 or IPv6(34 or 58)" % iplen)

		label = Labels.unpack(data[:3])

		return cls(rd,esi,etag,label,ip,iplen,gwip,exdata)
