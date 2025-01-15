import socket
import threading

# Define the IP and port where the server will listen for incoming connections
IP = '0.0.0.0'  # '0.0.0.0' allows the server to accept connections from any network interface
PORT = 9998     # Port number to listen on

def main():
    # Create a socket object using IPv4 addressing and TCP protocol
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to the specified IP and port
    server.bind((IP, PORT))
    
    # Start listening for incoming connections, with a backlog of 5 connections
    server.listen(5)
    print(f'[*] Listening on {IP}:{PORT}')

    while True:
        # Accept a new client connection
        client, address = server.accept()
        print(f'[+] Accepted connection from {address[0]}:{address[1]}')

        # Create a new thread to handle the client connection
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

def handle_client(client_socket):
    # Use a context manager to ensure the client socket is properly closed
    with client_socket as sock:
        # Receive data from the client (up to 1024 bytes)
        request = sock.recv(1024)
        print(f'[*] Received: {request.decode("utf-8")}')

        # Send a response back to the client
        sock.send(b'ACK')

if __name__ == '__main__':
    # Entry point of the script
    main()