import socket
hostname = socket.gethostname()
ip = '10.0.0.82'
port = 8801

s= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (ip,port)
s.bind(server_address)

last_counter = dict()
packet_count = dict()
packets_missed = dict()
print("### Server is listenting ###")
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
    if test == "Done":
        send_data = str(packet_count[port])+','+str(packets_missed[port])
        s.sendto(send_data.encode('utf-8'), (recv_ip, port))
