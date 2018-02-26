import pcapy
import sys
import socket
from struct import *
import datetime


data = {'total': {}}
l = []

def data_init(s_addr, d_addr, s_port, d_port):
    d = {'s_addr': s_addr,
         'd_addr': d_addr,
         's_port': s_port,
         'd_port': d_port,
         'fin': 0,
         'syn': 0,
         'rst': 0,
         'ack': 0,
         'packet_out': 0,
         'packet_in': 0,
         'data_out': 0,
         'data_in': 0,
         'time': [],
         'complete': False
        }
    return d

def parse_payload(header, payload, i):
    time = header.getts()
    data_sent = header.getlen()

    # ethernet header = 14, ip header = 20
    
    iph = unpack('!BBHHHBBH4s4s', payload[14:34])
   # print(iph)
    
    s_addr = socket.inet_ntoa(iph[8])
    d_addr = socket.inet_ntoa(iph[9])
    
   # print("s:{} d:{}".format(s_addr, d_addr))
    
    tcphead = payload[34:54]
    tcph = unpack('!HHLLBBHHH', tcphead)
    s_port = tcph[0]
    d_port = tcph[1]
  #  seqnum = tcph[2]
  #  acknum = tcph[3]
    tcp_len = tcph[4] >> 4

    flags = tcph[5]
    fin = flags & 0x01
    syn = (flags & 0x02) >> 1
    rst = (flags & 0x04) >> 2
    psh = (flags & 0x08) >> 3
    ack = (flags & 0x10) >> 4
    
    id = s_port + d_port - 80
    
    # create data structure entry
    try:
        data[id]
    except:
        data[id] = data_init(s_addr, d_addr, s_port, d_port)
    
    # update data structure
    data[id]['fin'] += fin
    data[id]['syn'] += syn
    data[id]['rst'] += rst
    data[id]['ack'] += ack
    if data[id]['fin'] and data[id]['syn']:
        data[id]['complete'] = True  # probably can move to a later portion
    if s_port == 80:
        data[id]['packet_out'] += 1
        data[id]['data_out'] += data_sent
    else:
        data[id]['packet_in'] += 1
        data[id]['data_in'] += data_sent
    data[id]['time'].append(time)
    
    print("Connection {}:".format(i))
    print("Source Address: {}".format(s_addr))
    print("Destination Address: {}".format(d_addr))
    print("Source Port: {}".format(s_port))
    print("Destination Port: {}".format(d_port))
    print("Status: S{}F{}  R{}".format(data[id]['syn'], data[id]['fin'], data[id]['rst']))
    
    if data[id]['complete']:
        time = data[id]['time']
        start_time = time[0][0] + (float(time[0][1])/1000000)
        end_time = time[-1][0] + (float(time[-1][1])/1000000)
        duration = end_time - start_time
        print("Start Time: {}".format(datetime.datetime.fromtimestamp(start_time)))
        print("End Time: {}".format(datetime.datetime.fromtimestamp(end_time)))
        print("Duration: {}".format(duration))
        print(
        
   # l.append(source + dest - 80)
   # print(tcphead)
   # print(tcph)
   # print("Source Port: {}\nDestination Port: {}\nSequence Number: {}\nAcknowledgment: {}\nTCP Length: {}".format(source, dest, seqnum, acknum, tcp_len))
   # print("fin: {}, syn: {}, rst: {}, psh: {}, ack: {}".format(fin, syn, rst, psh, ack))
    print("======")

def main(argv):
    try:
        cap = pcapy.open_offline(argv[1])
    except:
        print("Failed to open the specified cap file")
        
    (header, payload) = cap.next()

    i = 1
    while header:
       # print(header.getlen())
        parse_payload(header, payload, i)
        (header, payload) = cap.next()
        i += 1
        
   # print(data)


if __name__=="__main__":
    print(len(sys.argv))
    main(sys.argv)

