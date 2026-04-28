import socket
from queries import is_valid_query, valid_queries

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
        print("Available queries:") 
        print("1. What is the average moisture inside our kitchen fridges in the past hours, week and month?")
        print("2. What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?")
        print("3. Which house consumed more electricity in the past 24 hours, and by how much?\n")
        query_input = input("Input the number of the query you wish to send: ")
        if query_input == "1":
            query_str = "get_avg_moisture"
        elif query_input == "2":
            query_str = "get_avg_water_consumption"
        elif query_input == "3":
            query_str = "get_most_electricity_consumption"
        else:
            print(f"Invalid query. Valid options are: {', '.join(valid_queries.keys())}\n")
            continue

        myTCPSocket.send(bytearray(query_str, encoding='utf-8'))
        serverresponse = myTCPSocket.recv(MAX_BYTES_TO_RECEIVE).decode()
        print(f"Server response:\n{serverresponse}\n")
except Exception as e:
    print(f"Error with transmission/receiving of message.\n{e}")
except KeyboardInterrupt as k:
    print(f"Transmission and receiving of data interrupted by keyboard input.")
finally:
    myTCPSocket.close()