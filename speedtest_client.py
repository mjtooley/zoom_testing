import socket
import time
import random
import threading
#import speedtest as st
import numpy as np
import sys, getopt

hostname = socket.gethostname()
ip = "3.209.93.245"
port = 8801
HD_PPS = 300  # 400 packets per second
SD_PPS = 100
PACKETS_TO_SEND = 10*HD_PPS
MAX_THREADS = 100

def test_us(i,d, pps,p_max, psize):
    # Create socket for server
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.settimeout(5) # set udp socket read timeout
    # Let's send data through UDP protocol
    packet_counter =0
    packet_loss = 0
    while (packet_counter<p_max) :
        #packet_size = random.randint(1000,1200)
        packet_size = np.random.normal(size=1, loc=psize, scale=100)
        data = "x" * int(packet_size[0])
        pc = str(packet_counter) + " "
        send_data = "Data "+pc+data
        s.sendto(send_data.encode('utf-8'), (ip, port))
        packet_counter +=1
        sleep_time = (1/pps)+random.randint(0,1)/1000 # randomize the backoff
        time.sleep(sleep_time)

    send_data = "Done " + str(pc)
    s.sendto(send_data.encode('utf-8'), (ip, port))
    
    try:
        p_sent = packet_counter
        rdata, address = s.recvfrom(4096)
        data_list = rdata.decode().split(",")
        p_rx = data_list[0]
        p_lost = data_list[1]
        packet_loss = 1 - int(p_rx) / int(packet_counter)
        if packet_loss < 0:
            d[i] = 0
        else:
            d[i] = packet_loss
    except:
        print("Socket Timeout for thread:", i)
        d[i] = 0 # set the packet loss to zero to use the highest calculate

    # close the socket
    s.close()

def zoom_test(start,pps, p_size, p_count):
    count = start
    max_p_loss = 0
    t = dict()
    d = dict()
    while count < MAX_THREADS and max_p_loss < 10:
        print("\n Starting ", count, " sessions\n")
        for i in range(count):
            t[i] = threading.Thread(target=test_us, args=(i, d, pps, p_count, p_size))

        for i in range(count):
            t[i].start()

        for i in range(count):
            t[i].join()
        max_p_loss = max(d.values()) * 100  # convert to %
        print("Zoom testing at {0:3d} PPS: Max packet loss with {1:2d} sessions was {2:3.2f}%".format(pps,count, max_p_loss))
        count += 1
    return count, max_p_loss

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

    #p_count = test_time*PPS
    hd_count, hd_loss = zoom_test(count,HD_PPS, 1000, test_time*HD_PPS)
    #pps = int(PPS/4)
    #p_count = test_time * pps
    sd_count, sd_loss = zoom_test(count*4, SD_PPS, 900, test_time*SD_PPS)

    print("Finished testing\n")
    print("Looks like you have {0:4.0f} Mbps of Upload speed \n".format(ul/1000000))
    print("And with it you can do {0:3d} Zoom HD concurrent sessions".format(hd_count))
    print("Max packet loss with {0:3d} HD sesssions was {1:3.2f}%".format(hd_count, hd_loss))
    print("And with it you can do {0:3d} Zoom SD concurrent sessions".format(sd_count))
    print("Max packet loss with {0:3d} SD sesssions was {1:3.2f}%".format(sd_count, hd_loss))
    print("Finished")

if __name__ == "__main__":
    main(sys.argv[1:])