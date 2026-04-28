from enum import Enum
from psycopg2 import connect, sql
from datetime import datetime, timezone, timedelta

DATABASE_URL_NICK = "postgresql://neondb_owner:npg_Tow98ynjARdP@ep-sparkling-glade-anutd48q-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
COLLECTION_NICK = "Table2_virtual"
METADATA_NICK = "Table2_metadata"

DATABASE_URL_DAMON = "postgresql://neondb_owner:npg_0kIR3uXfEhoj@ep-orange-cloud-a4p72xmt.us-east-1.aws.neon.tech/neondb?sslmode=require"
COLLECTION_DAMON = "table_virtual"
METADATA_DAMON = "table_metadata"

def load_metadata():
    conn = connect(DATABASE_URL_NICK)
    query = sql.SQL("SELECT {uid}, {type}, {cattr} FROM {coll}") \
        .format(uid= sql.Identifier("assetUid"), 
                type= sql.Identifier("assetType"),
                cattr = sql.Identifier("customAttributes"),
                coll=sql.Identifier(METADATA_NICK))
    
    metadata_nick = {"fridges": [], "dishwasher": ""}
    with conn.cursor() as cursor:
        cursor.execute(query)
        all_metadata = cursor.fetchall()
        for x in all_metadata:
            asset_uid = x[0]
            asset_type = x[1]
            print(asset_type)
            if asset_type == "Fridge": 
                metadata_nick['fridges'].append(asset_uid)
            elif asset_type == "Dishwasher": 
                metadata_nick['dishwasher'] = asset_uid

            custom_attr = x[2]
            sensors = custom_attr['children'][0]['customAttributes']['children']
            metadata_nick[asset_uid] = {}
            for sensor in sensors:
                sensor_uid = sensor['assetUid']
                sensor_name = sensor['customAttributes']['name']
                if "amm" in sensor_name.lower(): sensor_type = "AMM"
                elif "mm" in sensor_name.lower(): sensor_type = "MM"
                elif "wac" in sensor_name.lower(): sensor_type = "WAC"
                else: continue
                sensor_units = sensor['customAttributes']['unit']
            
                metadata_nick[asset_uid][sensor_type] = (sensor_uid, sensor_units, sensor_name)

    
    conn = connect(DATABASE_URL_DAMON)
    query = sql.SQL("SELECT {uid}, {type}, {cattr} FROM {coll}") \
        .format(uid= sql.Identifier("assetUid"), 
                type= sql.Identifier("assetType"),
                cattr = sql.Identifier("customAttributes"),
                coll=sql.Identifier(METADATA_DAMON))
    
    metadata_damon = {"fridges": [], "dishwasher": ""}
    with conn.cursor() as cursor:
        cursor.execute(query)
        all_metadata = cursor.fetchall()
        for x in all_metadata:
            asset_uid = x[0]
            asset_type = x[1]
            print(asset_type)
            if asset_type == "Fridge": 
                metadata_damon['fridges'].append(asset_uid)
            elif asset_type == "Dishwasher": 
                metadata_damon['dishwasher'] = asset_uid

            custom_attr = x[2]
            sensors = custom_attr['children'][0]['customAttributes']['children']
            metadata_damon[asset_uid] = {}
            for sensor in sensors:
                sensor_uid = sensor['assetUid']
                sensor_name = sensor['customAttributes']['name']
                if "moisture" in sensor_name.lower(): sensor_type = "MM"
                elif "ammeter" in sensor_name.lower(): sensor_type = "AMM"
                elif "wac" in sensor_name.lower(): sensor_type = "WAC"
                else: continue
                sensor_units = sensor['customAttributes']['unit']

                metadata_damon[asset_uid][sensor_type] = (sensor_uid, sensor_units, sensor_name)
    
    return metadata_nick, metadata_damon

metadata_nick, metadata_damon = load_metadata()
print(metadata_damon)
dishwasher=metadata_damon["dishwasher"]
print(metadata_damon[dishwasher])

def initial_timestamp_shared_from_damon():
    conn = connect(DATABASE_URL_NICK)
    with conn.cursor() as cursor:
        query = sql.SQL("SELECT to_timestamp((payload ->> 'timestamp')::bigint) AS ts FROM {coll} " \
        "WHERE topic = 'damonboone99@gmail.com/home'" \
        "ORDER BY ts " \
        "LIMIT 1") \
            .format(coll=sql.Identifier(COLLECTION_NICK))
        cursor.execute(query)
        response = cursor.fetchone()
        if response is not None:
            print(response)
            return response[0]
        else:
            raise Exception("Failed timestamp evaluation.")

initial_ts_shared = initial_timestamp_shared_from_damon()        

def time_since_data_shared():
    now = datetime.now(timezone.utc)
    return now - initial_ts_shared

class QueryEnum(Enum):
    AVG_MOISTURE = \
"""SELECT
    fridge,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 hour')  AS avg_last_hour,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 week')  AS avg_last_week,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 month') AS avg_last_month
FROM (
    SELECT
        CASE
            WHEN payload::jsonb ->> 'parent_asset_uid' = {nicksf1} THEN 'NICK-SmartFridge1'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {nicksf2} THEN 'NICK-SmartFridge2'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {damonsf1} THEN 'DAMON-SmartFridge1'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {damonsf2} THEN 'DAMON-SmartFridge2'
        END AS fridge,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        COALESCE(
            (payload ->> 'SF1-MM')::numeric,
            (payload ->> 'SF2-MM')::numeric,
            (payload ->> 'Moisture Meter - Moisture Meter Fridge')::numeric,
            (payload ->> 'Moisture Meter - Moisture Meter Fridge 2')::numeric
            
        ) AS value
    FROM {coll}
) AS t
WHERE value IS NOT NULL
GROUP BY fridge
ORDER BY fridge;"""

    AVG_WATER_CONSUMPTION = \
"""SELECT
    dishwasher,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 hour')  AS avg_last_hour,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 week')  AS avg_last_week,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 month') AS avg_last_month
FROM (
    SELECT
        CASE
            WHEN payload::jsonb ->> 'parent_asset_uid' = {nicksdishwasher} THEN 'NICK-Dishwasher'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {damonsdishwasher} THEN 'DAMON-Dishwasher'
        END AS dishwasher,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        COALESCE(
            (payload ->> 'SD-WAC')::numeric,
            (payload ->> 'YF-S201 - wac')::numeric
        ) AS value
    FROM {coll}
) AS t
WHERE value IS NOT NULL
GROUP BY dishwasher
ORDER BY dishwasher;"""

    MOST_ELECTRICITY_CONSUMPTION = \
""""""
    
    ELECTRICITY_CONSUMPTION_HOUSE = \
"""SELECT
    house,
    SUM(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 day') AS energy_consumption
FROM (
    SELECT
        {house} AS house,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        COALESCE(
            (payload ->> {amm1})::numeric,
            (payload ->> {amm2})::numeric,
            (payload ->> {amm3})::numeric
        ) AS value
    FROM {coll}
    WHERE payload::jsonb ->> 'parent_asset_uid' IN ({device1}, {device2}, {device3})
) AS t
WHERE value IS NOT NULL
GROUP BY house
"""

#--------------------------------------------------------------


valid_queries = {
    "get_avg_moisture": QueryEnum.AVG_MOISTURE.value,
    "get_avg_water_consumption": QueryEnum.AVG_WATER_CONSUMPTION.value,
    "get_most_electricity_consumption": QueryEnum.MOST_ELECTRICITY_CONSUMPTION.value,
    "get_house_electricity_consumption": QueryEnum.ELECTRICITY_CONSUMPTION_HOUSE.value
}

# The valid queries that the server can execute.
# This is used to validate user input (and, to prevent SQL injection).

def is_valid_query(query_str : str) -> bool:
    return query_str in valid_queries

def query(request : str) -> str:
    if request == "get_avg_moisture":
        conn = connect(DATABASE_URL_NICK)
        with conn.cursor() as cursor:
            if time_since_data_shared() < timedelta(days=31):
                # TODO: modify query to bring in data from other collection
                pass
            
            query = sql.SQL(valid_queries[request]) \
                .format(nicksf1=sql.Literal(metadata_nick['fridges'][0]), 
                        nicksf2=sql.Literal(metadata_nick['fridges'][1]),
                        damonsf1=sql.Literal(metadata_damon['fridges'][0]),
                        damonsf2=sql.Literal(metadata_damon['fridges'][1]),
                        coll=sql.Identifier(COLLECTION_NICK))
            cursor.execute(query)
            response = cursor.fetchall()

            # Format the response
            ret = "Fridge | Hour | Week | Month"
            assets = [metadata_nick['fridges'][0], metadata_nick['fridges'][1],
                     metadata_damon['fridges'][0], metadata_damon['fridges'][1]]
            units = [metadata_nick[assets[0]]["MM"][1], metadata_nick[assets[1]]["MM"][1],
                     metadata_damon[assets[2]]["MM"][1], metadata_damon[assets[3]]["MM"][1]]
            for i in range(len(response)):
                unit = "Volts" #units[i]
                result = response[i]
                ret += f"\n{result[0]}"
                ret += f"\t{round(result[1], 2)} {unit}"
                ret += f"\t{round(result[2], 2)} {unit}"
                ret += f"\t{round(result[3], 2)} {unit}"
                # "\t{round(result[1], 2)}\t{round(result[2], 2)}\t{round(result[3], 2)}\n"
            return ret
        
    elif request == "get_avg_water_consumption":
        conn = connect(DATABASE_URL_NICK)
        with conn.cursor() as cursor:
            if time_since_data_shared() < timedelta(days=31):
                # TODO: modify query to bring in data from other collection
                pass
            
            query = sql.SQL(valid_queries[request]) \
                .format(nicksdishwasher=sql.Literal(metadata_nick['dishwasher']), 
                        damonsdishwasher=sql.Literal(metadata_damon['dishwasher']),
                        coll=sql.Identifier(COLLECTION_NICK))
            cursor.execute(query)
            response = cursor.fetchall()

            # Keep a string return type so socket encoding is consistent.
            ret = "Dishwasher | Hour | Week | Month"
            assets = [metadata_nick['dishwasher'], metadata_damon['dishwasher']]
            units = [metadata_nick[assets[0]]["WAC"][1], metadata_damon[assets[1]]["WAC"][1]]
            for i in range(len(response)):
                unit = units[i]
                result = response[i]
                ret += f"\n{result[0]}"
                ret += f"\t{round(result[1], 2)} {unit}"
                ret += f"\t{round(result[2], 2)} {unit}"
                ret += f"\t{round(result[3], 2)} {unit}"
            return ret
    elif request == "get_most_electricity_consumption":
        if time_since_data_shared() >= timedelta(days=1): # All the data is in one database
            # TODO: modify query to only pull from one database
            pass

        conn = connect(DATABASE_URL_NICK)
        with conn.cursor() as cursor:
            devices = [metadata_nick["fridges"][0], metadata_nick["fridges"][1], metadata_nick["dishwasher"]]
            names = [metadata_nick[devices[i]]["AMM"][2] for i in (0, 1, 2)]
            query = sql.SQL(valid_queries["get_house_electricity_consumption"]) \
                .format(house=sql.Literal('NICK-House'),
                        amm1=sql.Literal(names[0]),
                        amm2=sql.Literal(names[1]),
                        amm3=sql.Literal(names[2]),
                        device1=sql.Literal(devices[0]),
                        device2=sql.Literal(devices[1]),
                        device3=sql.Literal(devices[2]),
                        coll=sql.Identifier(COLLECTION_NICK))
            cursor.execute(query)
            nick_result = cursor.fetchone()
            
            if nick_result is None:
                return "Error: Query failed with Nick's house"
              
            nick_house, nick_consumption = nick_result[0], round(nick_result[1], 2)
        
        conn = connect(DATABASE_URL_DAMON)
        with conn.cursor() as cursor:
            devices = [metadata_damon["fridges"][0], metadata_damon["fridges"][1], metadata_damon["dishwasher"]]
            names = [metadata_damon[devices[i]]["AMM"][2] for i in (0, 1, 2)]
            query = sql.SQL(valid_queries["get_house_electricity_consumption"]) \
                .format(house=sql.Literal('DAMON-House'),
                        amm1=sql.Literal(names[0]),
                        amm2=sql.Literal(names[1]),
                        amm3=sql.Literal(names[2]),
                        device1=sql.Literal(devices[0]),
                        device2=sql.Literal(devices[1]),
                        device3=sql.Literal(devices[2]),
                        coll=sql.Identifier(COLLECTION_DAMON))
            cursor.execute(query)
            damon_result = cursor.fetchone()

            if damon_result is None:
                return "Error: Query failed with Damon's house"
        
            damon_house, damon_consumption = damon_result[0], round(damon_result[1], 2)

        ret = "House | Consumption"
        ret += f"\n{nick_house}\t{nick_consumption} Amperes"
        ret += f"\n{damon_house}\t{damon_consumption} Amperes"
        ret += "\n\n"

        difference = nick_consumption - damon_consumption
        if difference > 0:
            ret += f"{nick_house} consumed {difference} Amperes more than {damon_house}"
        elif difference < 0:
            ret += f"{damon_house} consumed {-difference} Amperes more than {nick_house}"
        else:
            ret += f"Both houses consumed the same amount of electricity"

        return ret
    else:
        raise Exception("Invalid query passed to query(request) in queries.py.")