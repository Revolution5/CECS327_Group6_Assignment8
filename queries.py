# This file contains the queries that the server can execute, 
# as well as a mapping of valid query names to their corresponding query strings.

from enum import Enum

class Query(Enum):
    AVG_MOISTURE = \
"""SELECT
    fridge,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 hour')  AS avg_last_hour,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 week')  AS avg_last_week,
    AVG(value) FILTER (WHERE ts >= NOW() - INTERVAL '1 month') AS avg_last_month
FROM (
    SELECT
        CASE
            WHEN payload::jsonb ? 'SF1-MM' THEN 'SF1'
            WHEN payload::jsonb ? 'SF2-MM' THEN 'SF2'
        END AS fridge,
        to_timestamp((payload ->> 'timestamp')::bigint) AS ts,
        COALESCE(
            (payload ->> 'SF1-MM')::numeric,
            (payload ->> 'SF2-MM')::numeric
        ) AS value
    FROM {coll}
) AS t
WHERE value IS NOT NULL
GROUP BY fridge
ORDER BY fridge;"""

    AVG_WATER_CONSUMPTION = ""

#--------------------------------------------------------------

# The valid queries that the server can execute.
# This is used to validate user input (and, to prevent SQL injection).

valid_queries = {
    "get_avg_moisture": Query.AVG_MOISTURE.value,
    #"get_avg_water_consumption": Query.AVG_WATER_CONSUMPTION.value
}

def get_valid_query(request : str) -> str:
    if request not in valid_queries:
        return f"Invalid query could not be processed. Valid queries are: {', '.join(valid_queries.keys())}"
    return valid_queries[request]