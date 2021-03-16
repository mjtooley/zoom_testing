import socket
import time
import json
import threading
import sys
from queue import Queue
import struct

MAX_PACKET_LOSS = .15

def max_packet_loss(pl_dict):
    max_p_loss = 0
    for key in pl_dict:
        if pl_dict[key]['packet_loss'] > max_p_loss:
            max_p_loss = pl_dict[key]['packet_loss']
    return max_p_loss

#assume a socket disconnect (data returned is empty string) means  all data was #done being sent.
def recv_basic(the_socket):
    total_data=[]
    while True:
        data = the_socket.recv(8192)
        if not data: break
        total_data.append(data)
    return ''.join(total_data)

def recv_timeout(the_socket, timeout=2):
    # make socket non blocking
    the_socket.setblocking(0)

    # total data partwise in an array
    total_data = [];
    data = '';

    # beginning time
    begin = time.time()
    while 1:
        # if you got some data, then break after timeout
        if total_data and time.time() - begin > timeout:
            break

        # if you got no data at all, wait a little longer, twice the timeout
        elif time.time() - begin > timeout * 2:
            break

        # recv something
        try:
            data = the_socket.recv(8192)
            if data:
                total_data.append(data)
                # change the beginning time for measurement
                begin = time.time()
            else:
                # sleep for sometime to indicate a gap
                time.sleep(0.1)
        except:
            pass

    # join all parts to make final string
    return ''.join(total_data)

End='\n'
def recv_end(the_socket):
    total_data=[];data=''
    while True:
            data=the_socket.recv(8192)
            data = data.decode('utf-8')
            if End in data:
                total_data.append(data[:data.find(End)])
                break
            total_data.append(data)
            if len(total_data)>1:
                #check if end_of_data was split
                last_pair=total_data[-2]+total_data[-1]
                if End in last_pair:
                    total_data[-2]=last_pair[:last_pair.find(End)]
                    total_data.pop()
                    break
    return ''.join(total_data)

def recv_size(the_socket):
    #data length is packed into 4 bytes
    total_len=0;total_data=[];size=sys.maxint
    size_data=sock_data='';recv_size=8192
    while total_len<size:
        sock_data=the_socket.recv(recv_size)
        if not total_data:
            if len(sock_data)>4:
                size_data+=sock_data
                size=struct.unpack('>i', size_data[:4])[0]
                recv_size=size
                if recv_size>524288:recv_size=524288
                total_data.append(size_data[4:])
            else:
                size_data+=sock_data
        else:
            total_data.append(sock_data)
        total_len=sum([len(i) for i in total_data ])
    return ''.join(total_data)

def control_listener(d):
    server_address = ('', 8802)
    print("Listening of port:", server_address)
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        connection, client_address = sock.accept()

        try:
            # Receive the data in small chunks and retransmit it
            while max_packet_loss(d)< MAX_PACKET_LOSS:
                # Wait for a request for data
                msg = recv_end(connection)
                if msg == 'Get stats':
                    # Send the stats
                    try:
                        data = json.dumps(d)
                    except Exception as e:
                        print(e)
                    header_str = str(len(data)) + '\n'
                    connection.send(bytes(header_str,encoding='utf-8'))
                    connection.sendall(bytes(data,encoding='utf-8'))
                if msg == "Done":
                    d.clear()
                    connection.close()
                    break

        except Exception as e:
            print(e)
            print("Resetting the stats")
            d.clear()  # Clear the dictionary

        finally:
            # Clean up the connection
            connection.close()

def data_listener(pl_dict):
    hostname = socket.gethostname()
    # ip = socket.gethostbyname(hostname)
    ip = ''
    port = 8801
    s= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (ip,port)
    s.bind(server_address)

    last_counter = dict()
    packet_count = dict()
    packets_missed = dict()

    print("### Server is listening for ", server_address)
    while True:
        data, address = s.recvfrom(4096)
        recv_ip = address[0]
        port = address[1]
        data_list = data.decode().split(" ")
        test = data_list[0]
        if test == 'Data':
            counter = int(data_list[1])
            if port not in last_counter:
                last_counter[port] = counter
                packet_count[port] = 1
                packets_missed[port] = 0
            elif counter == last_counter[port]+1:
                packet_count[port] += 1
                last_counter[port] = counter
            else:
                packets_missed[port] += counter - last_counter[port]
                last_counter[port] = counter

        pl_dict[port] = {
            'packet_count': packet_count[port],
            'packets_missed': packets_missed[port],
            'recv_ip': recv_ip,
            'recv_port': port,
            'packet_loss': (packets_missed[port] / packet_count[port]),
            'last_counter': last_counter[port]
        }

def main(argv):
    pdict = {}
    #pdict[0] = {
    #    'packet_count': 0,
    #    'packets_missed': 0,
    #    'recv_ip': 0,
    #    'recv_port': 0,
    #    'packet_loss': 0
    #}
    #control_listener(pl_dict=pdict)
    t = threading.Thread(target=control_listener, args=(pdict,))
    t.start()

    data_listener(pdict)

    t.join()

if __name__ == "__main__":
    main(sys.argv[1:])
