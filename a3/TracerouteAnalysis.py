# Dylan Dvorachek
# V00863468
# CSC361 A3

import pcapy
import sys
import socket
from struct import *
from collections import OrderedDict

# Holds parsed information
data = OrderedDict()
identification = OrderedDict()
protocols = set()
source_addr = False
ult_dest_addr = False


# Function which is used to initalize the values for
# individual keys in 'data'
def data_init():
    d = {'router': '',
         'time_out': [],
         'time_in': [],
         'RTT': [],
         'frag_count': 0,
         'off_set': 0}
    
    return d
    
# helper fuction which checks the more fragment flag
# and the final offset
def check_more_fragments(flag_offset, key):
    if flag_offset:
        re = (flag_offset & 0x8000) >> 15
        df = (flag_offset & 0x4000) >> 14
        mf = (flag_offset & 0x2000) >> 13
        frag_off = flag_offset

        if mf:
            data[key]['frag_count'] += 1
        elif not mf and data[key]['frag_count'] > 0:
            data[key]['frag_count'] += 1
            data[key]['off_set'] = frag_off

# Reads in packet header/payload and parses information into the
# ordered dictionary 'data' depending on the protocol type.
def parse_payload(header, payload):
    global source_addr, ult_dest_addr
    
    time = header.getts()

    eth_len = 14
    iph = unpack('!BBHHHBBH4s4s', payload[eth_len:eth_len+20])
    
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

        if icmp_type == 0:
            # windows reply from ult dest
            key = icmph[4]
                
            data[key]['time_in'].append(time)
            data[key]['router'] = str(s_addr)
            
            calc_RTT(key)
            
            source_addr = d_addr
            ult_dest_addr = s_addr
        
        elif icmp_type == 3:
            # linux reply from ult dest
            port_off = used + icmph_len + 22
            get_port = payload[port_off:port_off+2]
            port = unpack('!H', get_port)
            key = port[0]
            
            data[key]['time_in'].append(time)
            data[key]['router'] = str(s_addr)
            
            calc_RTT(key)
            
            source_addr = d_addr
            ult_dest_addr = s_addr

        elif icmp_type == 8:
                
            seq = icmph[4]
            if seq not in data:
                data[seq] = data_init()
            
            # Used if the data is fragmented
            if iph[3] in identification:
                seq = identification[iph[3]]
            
            identification[iph[3]] = seq
            
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
        used = iph_len + eth_len
        udph_len = 8
        udp_header = payload[used:used+udph_len]

        udph = unpack('!HHHH', udp_header)

        s_port = udph[0]
        d_port = udph[1]
        
        # used if the message is fragmented
        if iph[3] in identification:
            d_port = identification[iph[3]]
            
        # filter unwanted UDP
        if (d_port>=33434) and (d_port<=33529):
            protocols.add('17: UDP')
            identification[iph[3]] = d_port
            
            # init dict value
            if d_port not in data:
                data[d_port] = data_init()
                
            # check for fragments
            check_more_fragments(iph[4], d_port)
            
            # do stuff with data times
            data[d_port]['time_out'].append(time)

# Helper function for converting (second, millisecond) tuple into seconds.
def make_time(time):
    return (time[0] + (float(time[1])/1000000)) * 1000

# Appends a new RTT value from the latest response.
def calc_RTT(key):
    alpha = 0.25
    
    if data[key]['RTT']:
        data[key]['RTT'].append(((1-alpha)*data[id]['RTT'][-1]+(alpha*(abs(make_time(data[key]['time_in'][-1]) - make_time(data[key]['time_out'][-1]))))))
    elif data[key]['time_in'] and data[key]['time_out']:
        data[key]['RTT'].append(abs(make_time(data[key]['time_in'][-1]) - make_time(data[key]['time_out'][-1])))

# Returns the STD from a list of RTTs
def calc_STD(RTT):
    beta = 0.5
    
    # first RTT
    r1 = RTT[0]
    
    # init std
    STD = max(RTT) - min(RTT)
    
    for r in RTT[1:]:
        STD = (1-beta)*STD+(beta*(abs(r1-r)))
        r1 = r
        
    return STD

# Helper function for 'output_format'
# Formats RTT values from the 'data' dict.
def format_RTT():
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
        
    return RTT_form
    
# Formats and prints output from OrderedDict 'data'.
def output_format():
    print("The IP address of the source node: {}".format(source_addr))
    print("The IP address of ultimate destination node: {}".format(ult_dest_addr))
    
    addrs = []
    [addrs.append(v['router']) for key, v in data.items() if v['router'] not in addrs and v['router'] != ult_dest_addr and v['router']]
    print("The IP addresses of the intermediate destination nodes:")
    for item in list(enumerate(addrs, start=1)):
        print("\tRouter {}: {}".format(item[0], item[1]))
        
    print("\nThe values in the protocol field of IP headers:")
    for item in protocols:
        print("\t{}".format(item))
    
    s = set()
    count = 1
    for key, v in data.items():
        item = (v['frag_count'], v['off_set'])
        if item[0] or item[1]:
            print("\nThe number of fragments created from the original datagram D{} is: {}".format(count, v['frag_count']))
            print("The offset of the last fragment is: {}\n".format(v['off_set']))
            s.add(item)
            count += 1
    if not s:
        print("\nThe number of fragments created from the original datagram is: 0")
        print("The offset of the last fragment is: 0\n")
        
    for item in format_RTT():
        s, d, RTT, STD = item
        print("The avg RTT between {} and {} is: {:.2f} ms, the s.d. is: {:.2f} ms".format(s, d, RTT, STD))


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

