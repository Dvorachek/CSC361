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
addresses = []
protocols = set()
source_addr = False
ult_dest_addr = False


def data_init():
    d = {'router': '',
         'time_out': [],
         'time_in': []}
    
    return d

def parse_payload(header, payload):
    global source_addr, ult_dest_addr
    time = header.getts()

    eth_len = 14
    
    iph = unpack('!BBHHHBBH4s4s', payload[14:34])
    
    iph_len = (iph[0] & 0xF) * 4
    
    ttl = iph[5]
    protocol = iph[6]
    
    s_addr = socket.inet_ntoa(iph[8])
    d_addr = socket.inet_ntoa(iph[9])
 #   print("ttl:{} protocol:{} s_addr:{} d_addr:{}".format(ttl, protocol, s_addr, d_addr))
   # print(iph)
   
    flag_offset = iph[4]
    if flag_offset:
        re = (flag_offset & 0b1000000000000000) >> 15
        df = (flag_offset & 0b0100000000000000) >> 14
        mf = (flag_offset & 0b0010000000000000) >> 13
        
        if mf:
            print('FUCK YEAH')
     #   print(df)
    
    if protocol == 1:
   #     print("ICMP")

        

        protocols.add("1: ICMP")
        used = iph_len + eth_len
        icmph_len = 8
        icmp_header = payload[used:used+icmph_len]
        
        icmph = unpack('!BBHHH', icmp_header)
        
        icmp_type = icmph[0]
        code = icmph[1]
        checksum = icmph[2]
       # print(icmph)
       # print("ttl:{} protocol:{} s_addr:{} d_addr:{}".format(ttl, protocol, s_addr, d_addr))

        if icmp_type == 8:

            if not source_addr:
                source_addr = s_addr
                
            if not ult_dest_addr:
                ult_dest_addr = d_addr
                
            seq = icmph[4]
            if seq not in data:
                data[seq] = data_init()
            
            # add timestamps to data
            
        elif icmp_type == 11:
            seq_off = used + icmph_len + 26
            get_seq = payload[seq_off:seq_off+2]

            seq = unpack('!H', get_seq)
     #       print("seq {}".format(seq[0]))
            
            port_off = used + icmph_len + 22
            get_port = payload[port_off:port_off+2]
            
            port = unpack('!H', get_port)
      #      print("port {}".format(port[0]))
            
            if s_addr not in addresses:
                addresses.append(s_addr)
                
            if seq[0] in data:
                key = seq[0]
            elif port[0] in data:
                key = port[0]
                
            print(key)
                
           # print("ttl:{} protocol:{} s_addr:{} d_addr:{}".format(ttl, protocol, s_addr, d_addr))
           # print(icmph)
           
    elif protocol == 17:
    
        protocols.add("17: UDP")
        used = iph_len + eth_len
        udph_len = 8
        udp_header = payload[used:used+udph_len]
        
        udph = unpack('!HHHH', udp_header)
        
        s_port = udph[0]
        d_port = udph[1]
        
        # filter unwanted UDP
        if (d_port>=33434) and (d_port<=33529):
            
        
            if not source_addr:
                source_addr = s_addr
            if not ult_dest_addr:
                ult_dest_addr = d_addr
   #         print("UDP")
            
            if d_port not in data:
                data[d_port] = data_init()
                
            # do stuff with data times
        
    
 #   elif protocol == 0:
 #       print("prot = 0")
 #       print("ttl:{} protocol:{} s_addr:{} d_addr:{}".format(ttl, protocol, s_addr, d_addr))
    
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
    
def output_format():
    print("The IP address of the source node: {}".format(source_addr))
    print("The IP address of ultimate destination node: {}".format(ult_dest_addr))
    print("The IP addresses of the intermediate destination nodes:")
    for item in list(enumerate(addresses, start=1)):
        print("\tRouter {}: {}".format(item[0], item[1]))
    print("The values in the protocol field of IP headers:")
    for item in protocols:
        print("\t{}".format(item))

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
        
    output_format()


if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Requires an additional argument specifying a cap file")
        exit(1)
    main(sys.argv)
