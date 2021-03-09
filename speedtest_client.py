import socket
import sys
import time
import random
import threading
import logging
from multiprocessing import Process, Queue
import concurrent.futures
import speedtest


hostname = socket.gethostname()
ip = "3.209.93.245"
port = 8801
PPS = 1  # 400 packets per second
PACKETS_TO_SEND = 5*PPS
MAX_THREADS = 100

def test_us(i,d):
    p_rx = 0
    p_lost = 0
    p_sent = 0
    #rdata = ""
    # Create socket for server

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    #print("\n \n starting test_us() for thread ", i)
    # Let's send data through UDP protocol
    packet_counter =0
    packet_loss = 0
    while (packet_counter<PACKETS_TO_SEND) :
        packet_size = random.randint(1000,1200)
        data = "x" * packet_size
        pc = str(packet_counter) + " "
        send_data = "Data "+pc+data
        s.sendto(send_data.encode('utf-8'), (ip, port))
        #print('\n Sent : ', pc, "\n")
        packet_counter +=1

        time.sleep(1/PPS)
        #data, address = s.recvfrom(4096)
        #print("\n\n 2. Client received : ", data.decode('utf-8'), "\n\n")
    # print("\n Packets received:", p_rx, "Packets lost:", p_lost)

    send_data = "Done " + str(pc)
    s.sendto(send_data.encode('utf-8'), (ip, port))

    p_sent = packet_counter
    rdata, address = s.recvfrom(4096)
    data_list = rdata.decode().split(",")
    p_rx = data_list[0]
    p_lost = data_list[1]
    packet_loss = 1 - int(p_rx) / int(packet_counter)
    d[i] = packet_loss

    # close the socket
    s.close()


if __name__ =="__main__":
    t = dict()
    queue = Queue()
    d = dict()
    print("Test speed of Internet Connection\n")
    st = speedtest.Speedtest()
    dl = st.download()
    ul = st.upload()
    print("Download:", dl, " Upload:", ul)

    count = int(MAX_THREADS * 0)+2
    max_p_loss = 0
    while count < MAX_THREADS and max_p_loss < 0.1:
        print("\n starting ", count, " sessions\n")
        #processes = [Process(target=test_us, args=(queue,)) for _ in range(count)]

        #for p in processes:
        #    p.start()

        #for p in processes:
        #    p.join()

        #results = [queue.get() for _ in processes]
        #max_p_loss = max(results)
        #print(count, " sessions:", max_p_loss)
        #count += 1

        for i in range(count):
            t[i] = threading.Thread(target=test_us, args=(i,d,))

        for i in range(count):
            t[i].start()

        for i in range(count):
            t[i].join()

        #for i in range()
        #with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        #    t[i] = executor.submit((test_us,(i,d)))

        print(d.values())
        max_p_loss = max(d.values())
        count +=1

    print("Finished")

