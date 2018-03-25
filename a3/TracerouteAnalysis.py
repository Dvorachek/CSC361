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
         'time_in': [],
         'RTT': [],
         'frag_count': 0,
         'off_set': 0}
    
    return d
    
def check_more_fragments(flag_offset, key):
    if flag_offset:
        re = (flag_offset & 0b1000000000000000) >> 15
        df = (flag_offset & 0b0100000000000000) >> 14
        mf = (flag_offset & 0b0010000000000000) >> 13
        frag_off = (flag_offset & 0b0001111111111111)
        
        if mf:
            data[key]['frag_count'] += 1
        elif not mf and data[key]['frag_count']:
            data[key]['offset'] = frag_off

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
    
    if protocol == 1:
        protocols.add("1: ICMP")
        
        used = iph_len + eth_len
        icmph_len = 8
        icmp_header = payload[used:used+icmph_len]
        
        icmph = unpack('!BBHHH', icmp_header)
        
        icmp_type = icmph[0]
        code = icmph[1]
        checksum = icmph[2]
        
        print(icmph)

        if icmp_type == 0:
            # windows reply from ult dest
            key = icmph[4]
                
            data[key]['time_in'].append(time)
            data[key]['router'] = str(s_addr)
            
            calc_RTT(key)
        
        elif icmp_type == 3:
            # linux reply from ult dest
            port_off = used + icmph_len + 22
            get_port = payload[port_off:port_off+2]
            port = unpack('!H', get_port)
            key = port[0]
            
            data[key]['time_in'].append(time)
            data[key]['router'] = str(s_addr)
            
            calc_RTT(key)

        elif icmp_type == 8:

            if not source_addr:
                source_addr = s_addr
                
            if not ult_dest_addr:
                ult_dest_addr = d_addr
                
            seq = icmph[4]
            if seq not in data:
                data[seq] = data_init()
            
            # check for fragments
            check_more_fragments(iph[4], seq)
            
            # add timestamps to data
            data[seq]['time_out'].append(time)
            
        elif icmp_type == 11:
            # get seq num in case of windows
            seq_off = used + icmph_len + 26
            get_seq = payload[seq_off:seq_off+2]
            seq = unpack('!H', get_seq)

            # get port in case of linux
            port_off = used + icmph_len + 22
            get_port = payload[port_off:port_off+2]
            port = unpack('!H', get_port)

            # add router to the list of intermediate destination nodes
            if s_addr not in addresses:
                addresses.append(s_addr)
                
            # get key to match ping
            if seq[0] in data:
                key = seq[0]
            elif port[0] in data:
                key = port[0]
                
           # print(key)
            data[key]['time_in'].append(time)
            data[key]['router'] = str(s_addr)
            
            calc_RTT(key)

           
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

            # init dict value
            if d_port not in data:
                data[d_port] = data_init()
                
            # check for fragments
            check_more_fragments(iph[4], d_port)
            
            # do stuff with data times
            data[d_port]['time_out'].append(time)

def make_time(time):
    return (time[0] + (float(time[1])/1000000)) * 1000

def calc_RTT(key):
    alpha = 0.25
    
    if data[key]['RTT']:
        data[key]['RTT'].append(((1-alpha)*data[id]['RTT'][-1]+(alpha*(abs(make_time(data[key]['time_in'][-1]) - make_time(data[key]['time_out'][-1]))))))
    elif data[key]['time_in'] and data[key]['time_out']:
        data[key]['RTT'].append(abs(make_time(data[key]['time_in'][-1]) - make_time(data[key]['time_out'][-1])))

def calc_STD(RTT):
    # assuming a large beta to lower the weight of the initial std value
    beta = 0.75
    
    # first RTT
    r1 = RTT[0]
    
    # init std
    STD = max(RTT) - min(RTT)
    
    for r in RTT[1:]:
        STD = (1-beta)*STD+(beta*(abs(r1-r)))
        
    return STD


def output_format():
    print("The IP address of the source node: {}".format(source_addr))
    print("The IP address of ultimate destination node: {}".format(ult_dest_addr))
    print("The IP addresses of the intermediate destination nodes:")
    for item in list(enumerate(addresses, start=1)):
        print("\tRouter {}: {}".format(item[0], item[1]))
        
    print("\nThe values in the protocol field of IP headers:")
    for item in protocols:
        print("\t{}".format(item))
    
    for key, v in data.items():
        print("\nThe number of fragments created from the original datagram is: {}".format(v['frag_count']))
        print("The offset of the last fragment is: {}\n".format(v['off_set']))
        break
    
    join_RTT = OrderedDict()
    for key, v in data.items():
        ip = v['router']
        if not ip:
            continue
        if ip not in join_RTT:
            join_RTT[ip] = v['RTT']
        else:
            join_RTT[ip].append(v['RTT'][0])
    
    RTT_form = []
    for key, v in join_RTT.items():
        s = source_addr
        d = key
        RTT = sum(v)/len(v)
        STD = calc_STD(v)
        RTT_form.append((s, d, RTT, STD))
        
    for item in RTT_form:
        s, d, RTT, STD = item
        print("The avg RTT between {} and {} is: {:.2f} ms, the s.d. is: {:.2f} ms".format(s, d, RTT, STD))
        
   # print(data)


def main(argv):
    try:
        cap = pcapy.open_offline(argv[1])
    except:
        print("Failed to open the specified cap file")
        exit(1)
        
    header, payload = cap.next()
    
    while header:
        parse_payload(header, payload)
        (header, payload) = cap.next()
        
    output_format()


if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Requires an additional argument specifying a cap file")
        exit(1)
    main(sys.argv)
