To run the system, you will need to open two terminals in the project directory.

To run the server in one terminal, type "python tcpserver.py"
This will start the server automatically

To run the client in another terminal, type "python tcpclient.py"
To connect the client to the server, you must first type the server IP and port. 

If you are running the server locally, type "localhost" as the IP and "1024" as the port.

After the client connects to the server, you will be presented with a menu of available queries. Simply type the number of the query you would like to run. If an invalid input is typed, the client will show an error and display the menu again.

The system connects to a database hosted on NeonDB to collect data. It uses device data and metadata hosted on DataNiz to determine the correct device and sensor for the given query.