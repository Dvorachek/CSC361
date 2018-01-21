import socket
import ssl
import sys
import h2.connection
import re


_BUFF_SIZE = 10000
http_version = ''
https = ''


class smart_web_client(object):

    def __init__(self, host):
        self.host = host
        self.port = 80
        self.secure_port = 443
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.s.settimeout(10)
        self.ss.settimeout(10)
        
        self.__set_https()
        
        try:
            self.connect()
        except:
            print('http failed')
            
        try:
            self.connect_s()
        except:
            print('https failed')
        
    def connect(self):
        self.s.connect((self.host, self.port))
        
    def connect_s(self):
        self.ss.connect((self.host, self.secure_port))
        
    def disconnect(self):
        try:
            self.s.close
        except:
            print('no http connection to disconnect')
        
        try:
            self.ss.close
        except:
            print('no https connection to disconnect')

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
        
    def send_request(self):
        request = b"HEAD / HTTP/1.1\r\nHost: " + self.host + b"\r\nConnection: close\r\n\r\n"
        
        response = []
        response.append(self.send_request_http(request))

        i = response_ok(response)

        return response[i]
        
    def __set_https(self):
        self.ss = ssl.wrap_socket(self.ss, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)

def response_code(response):
    response = response.split(' ')
    return response[1]

def locate(response):
    response = response.split('\n')
    location = ''
    for line in response:
        if line[:10] == 'Location: ':
            location = line[10:]
            break
    
    return location

def redirection(location):
    global https
    location = location.strip()
    if location[:8] == 'https://':
        location = location[8:]
        https = 'yes'

    if location[:7] == 'http://':
        location = location[7:]
        https = 'no'
    
    if location[-1] == '/':
        location = location[:-1]
        
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    if https == 'yes':
        sock.connect((location, 443))
        sock = ssl.wrap_socket(sock, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
    else:
        sock.connect((location, 80))
        
    request = b"HEAD / HTTP/1.1\r\nHost: " + location + b"\r\nConnection: close\r\n\r\n"
    sock.sendall(request)
    response = sock.recv(100000)
    sock.close
    return response

def response_ok(response):
    global https
    
    if response_code(response[1]) == '200':
        https = 'yes'
        return 1
    elif response_code(response[0]) == '200':
        https = 'no'
        return 0
    elif response_code(response[1]) in '301 302':
        response.append(redirection(locate(response[1])))
        return 2
    elif response_code(response[0]) in '301 302':
        response.append(redirection(locate(response[0])))
        return 2
    elif response_code(response[1]) in '404':
        return 4
    elif response_code(response[0]) in '404':
        return 4
    elif response_code(response[1]) in '505':
        return 5
    elif response_code(response[0]) in '505':
        return 5
        
def parse_and_format(response, host):
    global http_version, https

    response = response.split('\n')

    cookies = []
    for item in response:
        if 'HTTP' in item and not http_version:
            http_version = item.split(' ')[0]
        if 'Set-Cookie:' in item:
            cookies.append(item[11:])

    print("website: {}".format(host))
    print("1. Support of HTTPS: {}".format(https))
    print("2. The newest HTTP versions that the web server supports: {}".format(http_version))
    print("3. List of Cookies:")

    for item in cookies:
        name = '-'
        key = '-'
        domain = host
        item = item.split(';')
        key = item[0].split('=')[0]
        for segment in item:
            if 'domain' in segment:
                domain = segment.split('=')[1]

        print("name: {}, key: {}, domain name: {}".format(name, key, domain))

'''
The next three functions were taken from: https://python-hyper.org/projects/h2/en/stable/negotiating-http2.html
The purpose is to determine if the server supports HTTP2
Comments have been removed to make functions smaller, but can be recovered by following the above link
'''
def establish_tcp_connection(host):
    return socket.create_connection((host, 443))

def get_http2_ssl_context():
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
    ctx.set_alpn_protocols(["h2", "http/1.1"])

    try:
        ctx.set_npn_protocols(["h2", "http/1.1"])
    except NotImplementedError:
        pass

    return ctx
    
def negotiate_tls(tcp_conn, context, host):
    global http_version
    tls_conn = context.wrap_socket(tcp_conn, server_hostname=host)

    negotiated_protocol = tls_conn.selected_alpn_protocol()
    if negotiated_protocol is None:
        negotiated_protocol = tls_conn.selected_npn_protocol()

    if negotiated_protocol != "h2":
        print("Didn't negotiate HTTP/2!")
        # raise RuntimeError("Didn't negotiate HTTP/2!")
    else:
        http_version = 'HTTP/2'

    return tls_conn

def check_http2(host):
    context = get_http2_ssl_context()
    connection = establish_tcp_connection(host)
    tls_connection = negotiate_tls(connection, context, host)


def main():
    if len(sys.argv) < 2:
        print("Invalid program usage, please specify a web server")
        exit(0)

    host = sys.argv[1]
    
    check_http2(host)
    
    client = smart_web_client(host)

    response = client.send_request()
    
    parse_and_format(response, host)

    client.disconnect()


if __name__=='__main__':
    main()
