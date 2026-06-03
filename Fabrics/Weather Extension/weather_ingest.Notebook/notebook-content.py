# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.12"
# META   },
# META   "dependencies": {
# META     "environment": {}
# META   }
# META }

# CELL ********************

import requests
from datetime import datetime, timezone

lat = 40.7128
lon = -74.0060
tz = "America/New_York"

params = {
    "latitude": lat,
    "longitude": lon,
    "timezone": tz,
    "past_days": 7,
    "forecast_days": 2,
    "hourly": ",".join([
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "snowfall",
        "weather_code",
        "cloud_cover",
        "surface_pressure",
        "wind_speed_10m",
        "wind_gusts_10m",
    ]),
}

data = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import math
import pandas as pd
from zoneinfo import ZoneInfo

def get_value(values, i):
    return values[i] if values and i < len(values) else None

def to_float(value):
    return None if value is None else float(value)

def to_int(value):
    return None if value is None else int(value)

def kmh_to_ms(value):
    return None if value is None else float(value) / 3.6

def weather_code_label(code):
    labels = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
    }
    return labels.get(code, f"Unknown ({code})") if code is not None else None

def local_time_to_utc(ts_str, tz_name):
    local_tz = ZoneInfo(tz_name)
    local_dt = datetime.fromisoformat(ts_str).replace(tzinfo=local_tz)
    return local_dt.astimezone(timezone.utc)

def heat_index_c(temperature_c, humidity_pct):
    if temperature_c is None or humidity_pct is None or temperature_c < 27:
        return None

    temp_f = temperature_c * 9 / 5 + 32
    rh = humidity_pct

    heat_index_f = (
        -42.379
        + 2.04901523 * temp_f
        + 10.14333127 * rh
        - 0.22475541 * temp_f * rh
        - 0.00683783 * temp_f * temp_f
        - 0.05481717 * rh * rh
        + 0.00122874 * temp_f * temp_f * rh
        + 0.00085282 * temp_f * rh * rh
        - 0.00000199 * temp_f * temp_f * rh * rh
    )

    return (heat_index_f - 32) * 5 / 9

def wind_chill_c(temperature_c, wind_speed_ms):
    if temperature_c is None or wind_speed_ms is None or temperature_c > 10 or wind_speed_ms <= 1.34:
        return None

    wind_kmh = wind_speed_ms * 3.6

    return (
        13.12
        + 0.6215 * temperature_c
        - 11.37 * math.pow(wind_kmh, 0.16)
        + 0.3965 * temperature_c * math.pow(wind_kmh, 0.16)
    )

def comfort_index(temperature_c, humidity_pct, wind_speed_ms):
    if temperature_c is None or humidity_pct is None or wind_speed_ms is None:
        return None

    temperature_penalty = abs(temperature_c - 21.0) * 2.0
    humidity_penalty = abs(humidity_pct - 50.0) * 0.35
    wind_penalty = max(wind_speed_ms - 4.0, 0.0) * 2.5

    return max(0.0, min(100.0, 100.0 - temperature_penalty - humidity_penalty - wind_penalty))


hourly = data["hourly"]
times = hourly["time"]
fetched_at = datetime.now(timezone.utc)

rows = []

for i, ts_str in enumerate(times):
    temperature = to_float(get_value(hourly.get("temperature_2m"), i))
    humidity = to_float(get_value(hourly.get("relative_humidity_2m"), i))
    wind_speed = kmh_to_ms(get_value(hourly.get("wind_speed_10m"), i))
    wind_gusts = kmh_to_ms(get_value(hourly.get("wind_gusts_10m"), i))
    rain = to_float(get_value(hourly.get("rain"), i))
    snowfall = to_float(get_value(hourly.get("snowfall"), i))
    weather_code = to_int(get_value(hourly.get("weather_code"), i))

    rows.append({
        "ts": local_time_to_utc(ts_str, tz),
        "location_key": "nyc",
        "location_name": "NYC",
        "latitude": lat,
        "longitude": lon,
        "temperature_c": temperature,
        "relative_humidity_pct": humidity,
        "dew_point_c": to_float(get_value(hourly.get("dew_point_2m"), i)),
        "apparent_temperature_c": to_float(get_value(hourly.get("apparent_temperature"), i)),
        "precipitation_mm": to_float(get_value(hourly.get("precipitation"), i)),
        "rain_mm": rain,
        "snowfall_cm": snowfall,
        "weather_code": weather_code,
        "weather_condition": weather_code_label(weather_code),
        "cloud_cover_pct": to_float(get_value(hourly.get("cloud_cover"), i)),
        "surface_pressure_hpa": to_float(get_value(hourly.get("surface_pressure"), i)),
        "wind_speed_ms": wind_speed,
        "wind_gusts_ms": wind_gusts,
        "heat_index_c": heat_index_c(temperature, humidity),
        "wind_chill_c": wind_chill_c(temperature, wind_speed),
        "comfort_index": comfort_index(temperature, humidity, wind_speed),
        "is_raining": bool((rain or 0) > 0),
        "is_snowing": bool((snowfall or 0) > 0),
        "source": "open-meteo",
        "fetched_at": fetched_at,
    })

df = pd.DataFrame(rows)

df.head()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

len(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

%pip install azure-kusto-data azure-kusto-ingest pandas requests

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

CLUSTER_URI = "https://trd-hfb2q528r4e8qyku5p.z7.kusto.fabric.microsoft.com"
DATABASE_NAME = "Eventhouse"
TABLE_NAME = "weather_hourly_enriched"

token = notebookutils.credentials.getToken("kusto")

kcsb = KustoConnectionStringBuilder.with_aad_user_token_authentication(
    CLUSTER_URI,
    token
)

client = KustoClient(kcsb)

print("Connected to KQL with Fabric notebook token")
print(kcsb,client,token)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

result = client.execute(DATABASE_NAME, f"{TABLE_NAME} | count")

for row in result.primary_results[0]:
    print(row)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

min_ts = df["ts"].min().strftime("%Y-%m-%dT%H:%M:%SZ")
max_ts = df["ts"].max().strftime("%Y-%m-%dT%H:%M:%SZ")

delete_command = f"""
.delete table {TABLE_NAME} records <|
{TABLE_NAME}
| where location_key == "nyc"
| where ts between (datetime({min_ts}) .. datetime({max_ts}))
"""

client.execute_mgmt(DATABASE_NAME, delete_command)

print(f"Deleted existing rows from {min_ts} to {max_ts}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import json

records = df.copy()

for col in ["ts", "fetched_at"]:
    records[col] = records[col].astype(str)

json_lines = "\n".join(
    json.dumps(row, default=str)
    for row in records.to_dict(orient="records")
)

ingest_command = f"""
.ingest inline into table {TABLE_NAME} with (format="multijson")
<|
{json_lines}
"""

client.execute_mgmt(DATABASE_NAME, ingest_command)

print(f"Inserted {len(df)} rows into {TABLE_NAME}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

result = client.execute(DATABASE_NAME, f"{TABLE_NAME} | count")

for row in result.primary_results[0]:
    print(row)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

.add database <DATABASE_NAME> viewers ('aaduser=<user@domain.com>')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
