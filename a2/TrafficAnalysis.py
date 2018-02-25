import pcapy
import sys
import socket
from struct import *


def parse_payload(payload):
    # ethernet header = 14, ip header = 20
    tcphead = payload[34:54]
    print(tcphead)
    tcph = unpack('!HHLLBBHHH', tcphead)
    print(tcph)
    source = tcph[0]
    dest = tcph[1]
    seqnum = tcph[2]
    acknum = tcph[3]
    tcp_len = tcph[4] >> 4

    flags = tcph[5]
    fin = flags & 0x01
    syn = (flags & 0x02) >> 1
    rst = (flags & 0x04) >> 2
    psh = (flags & 0x08) >> 3
    ack = (flags & 0x10) >> 4
    
    print("Source Port: {}\nDestination Port: {}\nSequence Number: {}\nAcknowledgment: {}\nTCP Length: {}".format(source, dest, seqnum, acknum, tcp_len))
    print("fin: {}, syn: {}, rst: {}, psh: {}, ack: {}".format(fin, syn, rst, psh, ack))
    print("======")

def main(argv):
    try:
        cap = pcapy.open_offline(argv[1])
    except:
        print("Failed to open the specified cap file")
        
    (header, payload) = cap.next()

    while header:
        parse_payload(payload)
        (header, payload) = cap.next()


if __name__=="__main__":
    main(sys.argv)

