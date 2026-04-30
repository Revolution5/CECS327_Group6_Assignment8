A Python installation is required to run these programs. Modern Python installations should come with the socket module, but if not, it can easily be installed using the pip packet manager. 

For example: 

```bash
pip install socket 
python -m pip install socket
```

To run the system, you will need to open two terminals in the project directory.

To run the server in one terminal, type ```python tcpserver.py```. This will start the server automatically

To run the client in another terminal, type ```python tcpclient.py```. To connect the client to the server, you must first type the server IP and port. 

For example, if you are running the server locally, enter localhost (as the IP) when prompted and 1024 (as the port) when prompted.

After the client connects to the server, you will be presented with a menu of available queries. Simply type the number of the query you would like to run. If an invalid input is typed, the client will show an error and display the menu again.

The server connects to a PostgreSQL database hosted on NeonDB that collects data from our DataNiz devices. To this end, it uses the ```psycopg2``` module to set up a connection, construct various queries, and execute those queries. 

The connections and queries required for a given request are determined at runtime. Each of us has a database that includes shared data, and unique data which exists before the date we started sharing our data.

Query completeness is determined by the share date. If the query requires data that exists before the share date, the server separately queries both of our databases and combines the results to get the complete dataset.

The server uses device data and metadata created by DataNiz to construct an internal representation of metadata. Then, it can determine the correct devices and sensors for any given query.