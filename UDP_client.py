import socket
target_host = "127.0.0.1"
target_port = 80
# Create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Send some data
client.sendto(b"This is test data", (target_host, target_port))
# Recieve some data
data,addr = client.recvfrom(4096)
print(data)