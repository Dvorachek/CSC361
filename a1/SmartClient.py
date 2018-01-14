import socket
import ssl
import sys
import re


_BUFF_SIZE = 10000
# output = {'https': '',
          # 'http': '',
          # 'cookies': []}


class smart_web_client(object):

    def __init__(self, host, port, secure_port):
        self.host = host
        self.port = port
        self.secure_port = secure_port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(10)
        self.ss.settimeout(10)
        self.__set_https()
        
        try:
            self.connect()
        except:
            print 'http failed'
            
        try:
            self.connect_s()
        except:
            print 'https failed'
        
    def connect(self):
        self.s.connect((self.host, self.port))
        
    def connect_s(self):
        self.ss.connect((self.host, self.secure_port))
        
    def disconnect(self):
        try:
            self.s.close
        except:
            print 'no http connection to disconnect'
        
        try:
            self.ss.close
        except:
            print 'no https connection to disconnect'

    def send_request_http(self, request):
        self.s.sendall(request)
        response = self.s.recv(_BUFF_SIZE)
        r = response

        while response:
            response = self.s.recv(_BUFF_SIZE)
            r += response
            
        return r
            
    def send_request_https(self, request):
        self.ss.sendall(request)
        response = self.ss.recv(_BUFF_SIZE)
        r = response

        while response:
            response = self.ss.recv(_BUFF_SIZE)
            r += response
            
        return r
        
    def __set_https(self):
        self.ss = ssl.wrap_socket(self.ss, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)

def response_code(response):
    response = response.split(' ')
    return response[1]

def location(response):
    response = response.split('\n')
    response = response[1].split(' ')[1]
    return response

def response_ok(response):
    if response_code(response[1]) == '200':
        return 1
    elif response_code(response[0]) == '200':
        return 0
    elif response_code(response[0]) in '300 301 302' or response_code(response[1]) in '300 301 302':
        return 2
    else:
        return -1
        
def parse_and_format(response, host, https):
    output = {'https': '',
              'http': '',
              'cookies': []}
              
    print "website: {}".format(host)
    print "1. Support of HTTPS: {}".format(https)
    
    print response
    
    response = response.split('\n')

    for item in response:
        if 'HTTP' in item:
            output['http'] = item.split(' ')[0]
        if 'Set-Cookie:' in item:
            if 'deleted' in item:
                continue
            output['cookies'].append(item[11:])
            
    print "2. The newest HTTP versions that the web server supports: {}".format(output['http'])
    print "3. List of Cookies:"

    cookies = []
    for item in output['cookies']:
        name = '-'
        key = '-'
        domain = host
        item = item.split(';')
        key = item[0].split('=')[0]
        for segment in item:
            if '=' not in segment:
                name = segment
            if 'domain' in segment:
                domain = segment.split('=')[1]

        print "name: {}, key: {}, domain name: {}".format(name, key, domain)


def main():
    if len(sys.argv) < 2:
        print "Invalid program usage, please specify a web server"
        exit(0)

    host = sys.argv[1]
    
    #TESTS
    host1 = 'github.com'
    host2 = 'www.uvic.ca'
    request1 = "HEAD / HTTP/1.0\r\nHost: github.com\r\nConnection: close\r\n\r\n"
    request2 = "HEAD / HTTP/1.0\r\nHost: www.uvic.ca\r\nConnection: close\r\n\r\n"

    port = 80
    secure_port = 443

    request = "HEAD / HTTP/1.0\r\nHost: {}\r\nConnection: close\r\n\r\n".format(host)

    client = smart_web_client(host, port, secure_port)

    response = []
    response.append(client.send_request_http(request))
    response.append(client.send_request_https(request))

    i = response_ok(response)
    
    if i == 2:
        print 'add redirection here'
        # 
        https = 'some sort of test here'
    
    if i == 1:
        https = 'yes'
    if i == 0:
        https = 'no'

    parse_and_format(response[i], host, https)

    client.disconnect()


if __name__=='__main__':
    main()
