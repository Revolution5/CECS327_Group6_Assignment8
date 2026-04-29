import socket
from queries import query

MAX_BYTES_TO_RECEIVE = 1000
PORT = 1024

myTCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
myTCPSocket.bind(("0.0.0.0", PORT))
myTCPSocket.listen(5)
incomingSocket, incomingAddress = myTCPSocket.accept()

try:
    while True:
        request = incomingSocket.recv(MAX_BYTES_TO_RECEIVE).decode()
        print(f"Received query request.")

        time_completed, query_result = query(request)
        response = f"Query completed at: {time_completed}.\n{query_result}"

        print(f"Sending query result: {response}")
        response_text = str(response)
        incomingSocket.send(response_text.encode('utf-8'))
except Exception as e:
    print(f"Error with receiving/transmission of message.\n{e}")
except KeyboardInterrupt as k:
    print(f"Receiving and transmission of data interrupted by keyboard input.")
finally:
    myTCPSocket.close()