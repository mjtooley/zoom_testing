import socket
import time
import json
import threading
import sys
from queue import Queue

MAX_PACKET_LOSS = .15

def max_packet_loss(pl_dict):
    max_p_loss = 0
    for key in pl_dict:
        if pl_dict[key]['packet_loss'] > max_p_loss:
            max_p_loss = pl_dict[key]['packet_loss']
    return max_p_loss


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
                try:
                    data = json.dumps(d)
                except Exception as e:
                    print(e)
                header_str = str(len(data)) + '\n'
                connection.send(bytes(header_str,encoding='utf-8'))
                connection.sendall(bytes(data,encoding='utf-8'))
                time.sleep(5)
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
