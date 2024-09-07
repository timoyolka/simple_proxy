import socket
import threading

HOST = "0.0.0.0"
HOST_PORT = 8080
MAX_QUEUE = 5
BUFF_SIZE = 8192

def extract_host_port(request):
    parts = request.split()
    
    if len(parts) < 2:
        return None, None
    
    host_port = parts[1]
    
    if ':' in host_port:
        host, port = host_port.split(':')
        return host, int(port)
    else:
        return host_port, 443

def handle_client(client_socket, client_addr):
    try:
        #client - me
        request = client_socket.recv(BUFF_SIZE).decode()
        if not request:
            return

        remote_host, remote_port = extract_host_port(request)
        
        if not remote_host:
            print(f"Invalid remote host or port for client {client_addr}")
            return

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((remote_host, remote_port))
        
        if request.startswith("CONNECT"):
            client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            print(f"Established tunnel for client {client_addr} to {remote_host}:{remote_port}")
        else:
            print(f"Received HTTP request from client {client_addr} for {remote_host}:{remote_port}")
            remote_socket.sendall(request.encode())
           
        def forward(source, destination):
            """Forward data from source to destination."""
            while True:
                data = source.recv(BUFF_SIZE)
                if not data:
                    break
                destination.sendall(data)

        #exchange between me and remote host
        client_to_remote = threading.Thread(target=forward, args=(client_socket, remote_socket))
        remote_to_client = threading.Thread(target=forward, args=(remote_socket, client_socket))

        client_to_remote.start()
        remote_to_client.start()

        client_to_remote.join()
        remote_to_client.join()

    except Exception as e:
        print(f"Error with client {client_addr}: {e}")
    finally:
        client_socket.close()
        if 'remote_socket' in locals():
            remote_socket.close()
        print(f"Closed connection with client {client_addr}")

def start_proxy(host, port, max_queue):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(max_queue)
    print(f"Proxy server listening on {host}:{port}")

    while True:
        client_socket, client_addr = server_socket.accept()
        print(f"Accepted connection from {client_addr}")
        threading.Thread(target=handle_client, args=(client_socket, client_addr)).start()

def main():
    start_proxy(HOST, HOST_PORT, MAX_QUEUE)

if __name__ == "__main__":
    main()
