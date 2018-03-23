# Dylan Dvorachek
# V00863468
# CSC361 A3

import pcapy
import sys
import socket
from struct import *
import datetime
from collections import OrderedDict

data = OrderedDict()

def parse_payload(header, payload):
    time = header.getts()
    
    iph = unpack('!BBHHHBBH4s4s', payload[14:34])
    
    iph_len = (iph[0] & 0xF) * 4
    
    ttl = iph[5]
    protocol = iph[6]
    s_addr = socket.inet_ntoa(iph[8])
    d_addr = socket.inet_ntoa(iph[9])
    print("ttl:{} protocol:{} s_addr:{} d_addr:{}".format(ttl, protocol, s_addr, d_addr))
    
    if protocol == 1:
        print("ICMP")
        
    
#    tcphead = payload[iph_len+14:iph_len+34]
#    tcph = unpack('!HHLLBBHHH', tcphead)
#    s_port = tcph[0]
#    d_port = tcph[1]
#    tcp_len = tcph[4] >> 4
    
#    data_sent = header.getlen() - (14 + iph_len + tcp_len * 4)
    
#    flags = tcph[5]
#    fin = flags & 0x01
#    syn = (flags & 0x02) >> 1
#    rst = (flags & 0x04) >> 2
#    psh = (flags & 0x08) >> 3
    
#    window = tcph[6]
    


def main(argv):
    try:
        cap = pcapy.open_offline(argv[1])
    except:
        print("Failed to open the specified cap file")
        exit(1)
        
    header, payload = cap.next()
    
    while header:
     #   print("header {}".format(header))
     #   print("payload {}".format(payload))
        parse_payload(header, payload)
        (header, payload) = cap.next()


if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Requires an additional argument specifying a cap file")
        exit(1)
    main(sys.argv)
