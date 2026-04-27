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
                sensor_type = sensor['customAttributes']['name']
                if "amm" in sensor_type.lower(): sensor_type = "AMM"
                elif "mm" in sensor_type.lower(): sensor_type = "MM"
                elif "wac" in sensor_type.lower(): sensor_type = "WAC"
                else: continue
                sensor_units = sensor['customAttributes']['unit']
            
                metadata_nick[asset_uid][sensor_type] = (sensor_uid, sensor_units)

    
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
                sensor_type = sensor['customAttributes']['name']
                if "moisture" in sensor_type.lower(): sensor_type = "MM"
                elif "ammeter" in sensor_type.lower(): sensor_type = "AMM"
                elif "consumption" in sensor_type.lower(): sensor_type = "WAC"
                else: continue
                sensor_units = sensor['customAttributes']['unit']

                metadata_damon[asset_uid][sensor_type] = (sensor_uid, sensor_units)
    
    return metadata_nick, metadata_damon

metadata_nick, metadata_damon = load_metadata()
first_fridge = metadata_nick["fridges"][0]
print(metadata_nick[first_fridge])

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
            WHEN payload::jsonb ->> 'parent_asset_uid' = {nicksf1} THEN 'NICK-SF1'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {nicksf2} THEN 'NICK-SF2'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {damonsf1} THEN 'DAMON-SF1'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {damonsf2} THEN 'DAMON-SF2'
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
        'SD-WAC' AS dishwasher,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        (payload ->> 'SD-WAC')::numeric AS value
    FROM {coll}
) AS t
WHERE value IS NOT NULL
GROUP BY dishwasher
ORDER BY dishwasher;"""

    MOST_ELECTRICITY_CONSUMPTION = \
""""""

#--------------------------------------------------------------


valid_queries = {
    "get_avg_moisture": QueryEnum.AVG_MOISTURE.value,
    "get_avg_water_consumption": QueryEnum.AVG_WATER_CONSUMPTION.value
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
            response = str(cursor.fetchall())
            return response
        
    elif request == "get_avg_water_consumption":
        pass

    else:
        pass

    return ""