import socket
import time
import random
import threading
#import speedtest as st
import numpy as np
import sys, getopt
import json

hostname = socket.gethostname()
#ip = "3.209.93.245"
ip = '10.0.0.181'
port = 8801
HD_PPS = 400  # 400 packets per second
SD_PPS = 100
PACKETS_TO_SEND = 10*HD_PPS
MAX_THREADS = 100

def test_us(pps,psize, state):
    # Create socket for server
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.settimeout(5) # set udp socket read timeout
    # Let's send data through UDP protocol
    packet_counter =0
    packet_loss = 0
    while (True) :
        if state['state'] == 'run':
            #packet_size = random.randint(1000,1200)
            packet_size = np.random.normal(size=1, loc=psize, scale=100)
            data = "x" * int(packet_size[0])
            pc = str(packet_counter) + " "
            send_data = "Data "+pc+data
            s.sendto(send_data.encode('utf-8'), (ip, port))
            packet_counter +=1
            sleep_time = (1/pps)+random.randint(0,1)/1000 # randomize the backoff
            time.sleep(sleep_time)
        if state['state'] == 'pause':
            pass
        if state['state'] == 'end':
            break

    # close the socket
    s.close()

def msg_len(s):
    length = ''
    d = s.recv(1)
    char = d.decode('utf-8')
    while char != '\n':
        length += char
        d = s.recv(1)
        char = d.decode('utf-8')
    total = int(length)
    return total

def get_stats(s):
    msg = "Get stats\n"
    s.send(bytes(msg,encoding='utf-8'))


    total = msg_len(s)
    view = memoryview(bytearray(total))
    next_offset = 0
    while total - next_offset >0:
        recv_size = s.recv_into(view[next_offset:], total - next_offset)
        next_offset += recv_size
    try:
        deserialized = json.loads(view.tobytes())
    except (TypeError, ValueError):
        raise Exception('Data received was not in JSON Format')
    return deserialized

def send_done(s):
    msg = "Done\n"
    s.send(bytes(msg, encoding='utf-8'))

def get_max_loss(d):
    max_loss = 0
    for key in d:
        if d[key]['packet_loss'] > max_loss:
            max_loss = d[key]['packet_loss']
    return max_loss

def zoom_test(pps, p_size):
    max_p_loss = 0
    t = dict()
    d = dict()
    testing = dict()
    testing['state'] = 'run'

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    server_address = (ip, 8802)
    sock.connect(server_address)

    for i in range(10):
        t[i] = threading.Thread(target=test_us, args=(pps,p_size, testing))
        t[i].start()
    i = 10
    while max_p_loss < .10:
        t[i] = threading.Thread(target=test_us, args=(pps,p_size, testing))
        t[i].start()
        # Let the test run for a few seconds
        time.sleep(3)

        testing['state'] = 'pause' # pause the testing

        # Now read the test statistics
        stats = get_stats(sock)
        max_p_loss = get_max_loss(stats)
        print("Threads {}  Loss {}".format(i,max_p_loss))
        i += 1
        testing['state'] = 'run' # start the packets again

    testing['state'] = 'end'

    for j in range(len(t)):
        t[j].join()

    send_done(sock)
    print("Closing TCP socket")
    sock.close()
    return i, max_p_loss

def main(argv):
    server = ip
    test_time = 10
    try:
        opts, args = getopt.getopt(argv, "h:st", ["server=", "time="])
    except getopt.GetoptError:
        print
        'speedtest_client.py -s <server> -t <time of each session>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print
            'speedtest_client.py -s <server> -t <time of each session>'
            sys.exit()
        elif opt in ("-s", "--server"):
            server = arg
        elif opt in ("-t", "--time"):
            test_time = arg

    #print("Testing speed of your Internet Connection\n")
    #speed_test = st.Speedtest()
    #try:
    #    dl = speed_test.download()
    #    ul = speed_test.upload()
    #except:
    #    print("Speedtest.net is busy")
    #    dl =0.0
    #    ul = 0.0
    ul = 0.0
    dl = 0.0
    #print("Download: {0:4.0f} Mbps  Upload: {1:4.0f} Mbps".format(dl/1000000,ul/1000000))

    ZOOM_UL = 2000000
    if ul >0 :
        count = int(ul / ZOOM_UL )
    else:
        count = int(MAX_THREADS * 0)+2

    print("Starting HD testing\n")
    hd_count, hd_loss = zoom_test(HD_PPS, 1000)
    print("Starting SD testing\n")
    sd_count, sd_loss = zoom_test( SD_PPS, 900)

    print("Finished testing\n")
    print("Looks like you have {0:4.0f} Mbps of Upload speed \n".format(ul/1000000))
    print("And with it you can do {0:3d} Zoom HD concurrent sessions".format(hd_count))
    print("Max packet loss with {0:3d} HD sesssions was {1:3.2f}%".format(hd_count, hd_loss))
    print("And with it you can do {0:3d} Zoom SD concurrent sessions".format(sd_count))
    print("Max packet loss with {0:3d} SD sesssions was {1:3.2f}%".format(sd_count, hd_loss))
    print("Finished")

if __name__ == "__main__":
    main(sys.argv[1:])
