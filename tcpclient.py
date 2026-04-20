import socket
import queries

MAX_BYTES_TO_RECEIVE = 1000

serverip = input("Input the server IP address: ")
serverport = int(input("Input the server port: "))
print()

myTCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    myTCPSocket.connect((serverip, serverport))
except Exception as e:
    print(f"Error with socket connection.\n{e}")
    
    myTCPSocket.close()
    exit()

print("Socket connection was successful.\n")

try:
    while True:
        query = input("Input the query you wish to send: ")
        query_str = queries.get_valid_query(query)
        if query_str.find("Invalid query") == 0:
            print(query_str)
            continue

        myTCPSocket.send(bytearray(query_str, encoding='utf-8'))
        serverresponse = myTCPSocket.recv(MAX_BYTES_TO_RECEIVE).decode()
        print(f"Server response: {serverresponse}")
except Exception as e:
    print(f"Error with transmission/receiving of message.\n{e}")
except KeyboardInterrupt as k:
    print(f"Transmission and receiving of data interrupted by keyboard input.")
finally:
    myTCPSocket.close()