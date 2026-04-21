import socket
from psycopg2 import connect, sql
import queries

MAX_BYTES_TO_RECEIVE = 1000
PORT = 1024
DATABASE_URL_NICK = "postgresql://neondb_owner:npg_Tow98ynjARdP@ep-sparkling-glade-anutd48q-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
COLLECTION_NICK = "Table2_virtual"

myTCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
myTCPSocket.bind(("0.0.0.0", PORT))
myTCPSocket.listen(5)
incomingSocket, incomingAddress = myTCPSocket.accept()
conn = connect(DATABASE_URL_NICK)

try:
    while True:
        request = incomingSocket.recv(MAX_BYTES_TO_RECEIVE).decode()
        print(f"Received query request.")

        with conn.cursor() as cursor:
            query = sql.SQL(queries.valid_queries[request]) \
                .format(coll=sql.Identifier(COLLECTION_NICK))
            cursor.execute(query)
            response = str(cursor.fetchall())

        print(f"Sending query result: {response}")
        incomingSocket.send(bytearray(response, encoding='utf-8'))
except Exception as e:
    print(f"Error with receiving/transmission of message.\n{e}")
except KeyboardInterrupt as k:
    print(f"Receiving and transmission of data interrupted by keyboard input.")
finally:
    myTCPSocket.close()