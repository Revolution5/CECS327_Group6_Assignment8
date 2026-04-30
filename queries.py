from enum import Enum
from psycopg2 import connect, sql
from datetime import datetime, timezone, timedelta

DATABASE_URL_NICK = "postgresql://neondb_owner:npg_kbSDQ23IHNfr@ep-still-mode-amoxs3df-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
COLLECTION_NICK = "Devices_virtual"
METADATA_NICK = "Devices_metadata"

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
            return response[0]
        else:
            raise Exception("Failed timestamp evaluation.")

initial_ts_shared = initial_timestamp_shared_from_damon()

def time_since_data_shared():
    now = datetime.now(timezone.utc)
    return now - initial_ts_shared

def ts_now_str():
    return datetime.now().astimezone().strftime("%A, %B %d, %Y %I:%M:%S %p") + " PST"

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

    AVG_MOISTURE_NICK_ONLY = \
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
        END AS fridge,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        COALESCE(
            (payload ->> 'SF1-MM')::numeric,
            (payload ->> 'SF2-MM')::numeric
        ) AS value
    FROM {coll}
    WHERE payload::jsonb ->> 'parent_asset_uid' = {nicksf1}
       OR payload::jsonb ->> 'parent_asset_uid' = {nicksf2}
) AS t
WHERE value IS NOT NULL
GROUP BY fridge
ORDER BY fridge;"""

    AVG_MOISTURE_DAMON_ONLY = \
"""SELECT
    fridge,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 hour')  AS avg_last_hour,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 week')  AS avg_last_week,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 month') AS avg_last_month
FROM (
    SELECT
        CASE
            WHEN payload::jsonb ->> 'parent_asset_uid' = {damonsf1} THEN 'DAMON-SmartFridge1'
            WHEN payload::jsonb ->> 'parent_asset_uid' = {damonsf2} THEN 'DAMON-SmartFridge2'
        END AS fridge,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        COALESCE(
            (payload ->> 'Moisture Meter - Moisture Meter Fridge')::numeric,
            (payload ->> 'Moisture Meter - Moisture Meter Fridge 2')::numeric
        ) AS value
    FROM {coll}
    WHERE payload::jsonb ->> 'parent_asset_uid' = {damonsf1}
       OR payload::jsonb ->> 'parent_asset_uid' = {damonsf2}
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

    AVG_WATER_CONSUMPTION_NICK_ONLY = \
"""SELECT
    dishwasher,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 hour')  AS avg_last_hour,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 week')  AS avg_last_week,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 month') AS avg_last_month
FROM (
    SELECT
        'NICK-Dishwasher' AS dishwasher,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        (payload ->> 'SD-WAC')::numeric AS value
    FROM {coll}
    WHERE payload::jsonb ->> 'parent_asset_uid' = {nicksdishwasher}
) AS t
WHERE value IS NOT NULL
GROUP BY dishwasher
ORDER BY dishwasher;"""

    AVG_WATER_CONSUMPTION_DAMON_ONLY = \
"""SELECT
    dishwasher,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 hour')  AS avg_last_hour,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 week')  AS avg_last_week,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 month') AS avg_last_month
FROM (
    SELECT
        'DAMON-Dishwasher' AS dishwasher,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        (payload ->> 'YF-S201 - wac')::numeric AS value
    FROM {coll}
    WHERE payload::jsonb ->> 'parent_asset_uid' = {damonsdishwasher}
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

def query(request : str) -> tuple[str, str]:
    if request == "get_avg_moisture":
        elapsed = time_since_data_shared()
        need_week_union  = elapsed < timedelta(weeks=1)
        need_month_union = elapsed < timedelta(days=31)

        if need_week_union or need_month_union:
            # One or both time windows extend before initial_ts_shared, so Damon's data
            # in Nick's DB is incomplete for that window.  Query each DB separately and
            # union the result rows in Python (equivalent of a SQL UNION ALL).
            conn_nick = connect(DATABASE_URL_NICK)
            with conn_nick.cursor() as cursor:
                q = sql.SQL(QueryEnum.AVG_MOISTURE_NICK_ONLY.value) \
                    .format(nicksf1=sql.Literal(metadata_nick['fridges'][0]),
                            nicksf2=sql.Literal(metadata_nick['fridges'][1]),
                            coll=sql.Identifier(COLLECTION_NICK))
                cursor.execute(q)
                response_nick = cursor.fetchall()

            conn_damon = connect(DATABASE_URL_DAMON)
            with conn_damon.cursor() as cursor:
                q = sql.SQL(QueryEnum.AVG_MOISTURE_DAMON_ONLY.value) \
                    .format(damonsf1=sql.Literal(metadata_damon['fridges'][0]),
                            damonsf2=sql.Literal(metadata_damon['fridges'][1]),
                            coll=sql.Identifier(COLLECTION_DAMON))
                cursor.execute(q)
                time_completed = ts_now_str()
                response_damon = cursor.fetchall()

            # Union: combine both result sets
            # Union (distinct): deduplicate by device name, last writer wins.
            merged = {row[0]: row for row in response_nick + response_damon}
            response = sorted(merged.values(), key=lambda r: r[0])
        else:
            # All of Damon's data is already present in Nick's DB — single query suffices.
            conn = connect(DATABASE_URL_NICK)
            with conn.cursor() as cursor:
                q = sql.SQL(valid_queries[request]) \
                    .format(nicksf1=sql.Literal(metadata_nick['fridges'][0]),
                            nicksf2=sql.Literal(metadata_nick['fridges'][1]),
                            damonsf1=sql.Literal(metadata_damon['fridges'][0]),
                            damonsf2=sql.Literal(metadata_damon['fridges'][1]),
                            coll=sql.Identifier(COLLECTION_NICK))
                cursor.execute(q)
                time_completed = ts_now_str()
                response = cursor.fetchall()

        # Format the response
        ret = "Fridge | Hour | Week | Month"
        for i in range(len(response)):
            unit = "Relative Humidity (%)"
            device, perhour, perweek, permonth = response[i]
            perhour  = round((perhour  / 40) * 100, 2)
            perweek  = round((perweek  / 40) * 100, 2)
            permonth = round((permonth / 40) * 100, 2)
            ret += f"\n{device}"
            ret += f"\t{perhour} {unit}"
            ret += f"\t{perweek} {unit}"
            ret += f"\t{permonth} {unit}"
        return time_completed, ret
        
    elif request == "get_avg_water_consumption":
        elapsed = time_since_data_shared()
        need_week_union  = elapsed < timedelta(weeks=1)
        need_month_union = elapsed < timedelta(days=31)

        if need_week_union or need_month_union:
            conn_nick = connect(DATABASE_URL_NICK)
            with conn_nick.cursor() as cursor:
                q = sql.SQL(QueryEnum.AVG_WATER_CONSUMPTION_NICK_ONLY.value) \
                    .format(nicksdishwasher=sql.Literal(metadata_nick['dishwasher']),
                            coll=sql.Identifier(COLLECTION_NICK))
                cursor.execute(q)
                response_nick = cursor.fetchall()

            conn_damon = connect(DATABASE_URL_DAMON)
            with conn_damon.cursor() as cursor:
                q = sql.SQL(QueryEnum.AVG_WATER_CONSUMPTION_DAMON_ONLY.value) \
                    .format(damonsdishwasher=sql.Literal(metadata_damon['dishwasher']),
                            coll=sql.Identifier(COLLECTION_DAMON))
                cursor.execute(q)
                time_completed = ts_now_str()
                response_damon = cursor.fetchall()

            # Union
            merged = {row[0]: row for row in response_nick + response_damon}
            response = sorted(merged.values(), key=lambda r: r[0])
        else:
            # All of Damon's data is already in Nick's DB — single query suffices.
            conn = connect(DATABASE_URL_NICK)
            with conn.cursor() as cursor:
                q = sql.SQL(valid_queries[request]) \
                    .format(nicksdishwasher=sql.Literal(metadata_nick['dishwasher']),
                            damonsdishwasher=sql.Literal(metadata_damon['dishwasher']),
                            coll=sql.Identifier(COLLECTION_NICK))
                cursor.execute(q)
                time_completed = ts_now_str()
                response = cursor.fetchall()

        ret = "Dishwasher | Hour | Week | Month"
        for i in range(len(response)):
            unit = "Liters Per Minute"
            device, perhour, perweek, permonth = response[i]
            ret += f"\n{device}"
            ret += f"\t{round(perhour, 2)} {unit}"
            ret += f"\t{round(perweek, 2)} {unit}"
            ret += f"\t{round(permonth, 2)} {unit}"
        return time_completed, ret
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
                return "", "Error: Query failed with Nick's house"
              
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
            time_completed = ts_now_str()
            damon_result = cursor.fetchone()

            if damon_result is None:
                return "", "Error: Query failed with Damon's house"
        
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
        ret += " in the past day"
        return time_completed, ret
    else:
        raise Exception("Invalid query passed to query(request) in queries.py.")