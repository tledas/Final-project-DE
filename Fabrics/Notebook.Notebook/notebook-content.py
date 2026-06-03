# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.12"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "dba5cd7e-a9c2-4a49-84d6-97d63db82beb",
# META       "default_lakehouse_name": "Bronze",
# META       "default_lakehouse_workspace_id": "74ae7af4-8788-4bea-b8c4-b8377fd376c7",
# META       "known_lakehouses": [
# META         {
# META           "id": "dba5cd7e-a9c2-4a49-84d6-97d63db82beb"
# META         },
# META         {
# META           "id": "ceb40d9a-f541-4780-b16b-07e3a4e8cd76"
# META         },
# META         {
# META           "id": "f50e128a-6f83-48ff-868a-c872df8f3eb3"
# META         }
# META       ]
# META     },
# META     "warehouse": {
# META       "default_warehouse": "47691dc9-374e-4173-b61b-f2666adff661",
# META       "known_warehouses": [
# META         {
# META           "id": "47691dc9-374e-4173-b61b-f2666adff661",
# META           "type": "Lakewarehouse"
# META         },
# META         {
# META           "id": "e90fb599-998a-4504-a101-8ec1988f98f6",
# META           "type": "Lakewarehouse"
# META         },
# META         {
# META           "id": "d8b754b8-93f6-43e8-b0f8-e8543df5a913",
# META           "type": "Lakewarehouse"
# META         },
# META         {
# META           "id": "8fa5268a-7b13-8f78-4995-a07c5b01d68b",
# META           "type": "Datawarehouse"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import requests
import time
import pandas as pd

from pyspark.sql.types import *
from pyspark.sql.functions import col

BASE_URL = "https://api.openaq.org/v3"
BUCKET_URL = "https://openaq-data-archive.s3.amazonaws.com/"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "X-API-Key" 
}

NYC_BBOX = "-74.259,40.477,-73.700,40.917"

YEARS = [2023, 2024]
MONTHS = [f"{m:02d}" for m in range(1, 13)]

PARAMS = ["pm25", "no2", "o3", "co", "so2", "no", "nox", "pm10", "pm1"]


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

def get_locations_nyc():
    locations = []
    page = 1

    while True:
        r = requests.get(
            f"{BASE_URL}/locations",
            headers=HEADERS,
            params={
                "bbox": NYC_BBOX,
                "limit": 1000,
                "page": page
            },
            timeout=30
        )

        print(f"Страница {page}: статус {r.status_code}")

        data = r.json()
        results = data.get("results", [])

        if not results:
            break

        locations.extend(results)

        print(f"Получено {len(results)} локаций, всего: {len(locations)}")

        page += 1
        time.sleep(0.5)

    return locations


locations = get_locations_nyc()

print(f"\nВсего локаций NYC bbox: {len(locations)}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

available_locations = []

for loc in locations:
    location_id = loc["id"]
    location_name = loc.get("name", "")

    years_found = []

    for year in YEARS:
        found_year = False

        for month in MONTHS:
            prefix = f"records/csv.gz/locationid={location_id}/year={year}/month={month}/"

            r = requests.get(
                BUCKET_URL,
                params={
                    "list-type": "2",
                    "prefix": prefix,
                    "max-keys": 1
                },
                timeout=30
            )

            if "<Key>" in r.text:
                found_year = True
                break

            time.sleep(0.03)

        if found_year:
            years_found.append(year)

    if years_found:
        available_locations.append({
            "location_id": location_id,
            "location_name": location_name,
            "years": years_found
        })

        print(location_id, location_name, years_found)

print("Locations available:", len(available_locations))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

NYC_LOCATION_IDS = [
    384,      # CCNY
    625,      # Manhattan/IS143
    626,      # Bronx - IS52
    628,      # Maspeth
    631,      # Queens
    648,      # Bklyn - PS 314
    664,      # Bklyn - PS274
    665,      # Bronx - IS74
    666,      # Pfizer Lab
    292229,   # Morrisania
    1824516,  # Bayside, NY
    2616564,  # 7th Ave and W 16th St
    2903996,  # Win Son
    3041962,  # Near Bay 50 St
    3181018,  # Hillcrest, NY
    4727343,  # E Houston St between Clinton St & Attorney St
    4811604,  # Caton Ave and Ocean Pkwy, Brooklyn
    6091551,  # Brooklyn
    6166696   # Downtown Manhattan FiDi/Seaport
]

available_locations = [
    item for item in available_locations
    if item["location_id"] in NYC_LOCATION_IDS
]

print("NYC-only locations:", len(available_locations))

for item in available_locations:
    print(item["location_id"], item["location_name"], item["years"])


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

file_urls = []

for item in available_locations:
    location_id = item["location_id"]

    for year in YEARS:
        for month in MONTHS:
            prefix = f"records/csv.gz/locationid={location_id}/year={year}/month={month}/"

            r = requests.get(
                BUCKET_URL,
                params={
                    "list-type": "2",
                    "prefix": prefix,
                    "max-keys": 1000
                },
                timeout=30
            )

            if "<Key>" not in r.text:
                continue

            keys = r.text.split("<Key>")[1:]

            for k in keys:
                key = k.split("</Key>")[0]
                file_urls.append(BUCKET_URL + key)

print("CSV files:", len(file_urls))
print(file_urls[:3])


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

all_pdfs = []

for i, file_url in enumerate(file_urls):
    try:
        pdf = pd.read_csv(file_url, compression="gzip")
        pdf = pdf[pdf["parameter"].isin(PARAMS)]
        pdf["source_file"] = file_url.replace(BUCKET_URL, "")
        all_pdfs.append(pdf)
    except Exception as e:
        print("Ошибка чтения:", file_url, e)

    if (i + 1) % 500 == 0:
        print(f"Прочитано файлов: {i + 1}/{len(file_urls)}")

print("Pandas chunks:", len(all_pdfs))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

from pyspark.sql.types import *
from pyspark.sql.functions import col

schema = StructType([
    StructField("location_id", IntegerType(), True),
    StructField("sensors_id", IntegerType(), True),
    StructField("location", StringType(), True),
    StructField("datetime", StringType(), True),
    StructField("lat", DoubleType(), True),
    StructField("lon", DoubleType(), True),
    StructField("parameter", StringType(), True),
    StructField("units", StringType(), True),
    StructField("value", DoubleType(), True),
    StructField("source_file", StringType(), True),
])

pdf_all = pd.concat(all_pdfs, ignore_index=True)

df = spark.createDataFrame(pdf_all, schema=schema) \
    .withColumnRenamed("sensors_id", "sensor_id") \
    .withColumnRenamed("location", "location_name") \
    .withColumn("measured_at", col("datetime").cast("timestamp")) \
    .drop("datetime")

df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .partitionBy("parameter") \
    .saveAsTable("Bronze.dbo.openaq_measurements")

print(f"Bronze OpenAQ записано: {df.count()} строк")
display(df.limit(10))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import pyspark.sql.functions as F

df_air_bronze = spark.read.table("Bronze.dbo.openaq_measurements")

df_air_bronze.agg(
    F.min("measured_at").alias("min_measured_at"),
    F.max("measured_at").alias("max_measured_at"),
    F.count("*").alias("rows")
).show(truncate=False)

df_air_bronze.groupBy("parameter") \
    .count() \
    .orderBy("parameter") \
    .show(truncate=False)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import pandas as pd
import pyspark.sql.functions as F

pandas_rows = sum(len(pdf) for pdf in all_pdfs)

df_air_bronze = spark.read.table("Bronze.dbo.openaq_measurements")
bronze_rows = df_air_bronze.count()

print("Rows in all_pdfs:", pandas_rows)
print("Rows in Bronze:", bronze_rows)
print("Difference:", pandas_rows - bronze_rows)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import pyspark.sql.functions as F

df_air_bronze = spark.read.table("Bronze.dbo.openaq_measurements")

df_air_bronze.groupBy("parameter") \
    .count() \
    .orderBy("parameter") \
    .show(truncate=False)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

from pyspark.sql.functions import col, lit
from pyspark.sql.types import LongType
import pyspark.sql.functions as F

spark.conf.set("spark.sql.parquet.enableVectorizedReader", "false")

def read_and_fix(path):
    df = spark.read.parquet(path)
    for field in df.schema.fields:
        if str(field.dataType) == "IntegerType":
            df = df.withColumn(field.name, col(field.name).cast(LongType()))
    if "Airport_fee" in df.columns:
        df = df.withColumnRenamed("Airport_fee", "airport_fee")
            


    return df



files_yellow = [f"Files/Bronze/Taxi/Yellow/{y}/yellow_tripdata_{y}-{str(m).zfill(2)}.parquet" 
                for y in [2023, 2024] for m in range(1, 13)]



df_all = None
for f in files_yellow:
    try:
        df_temp = read_and_fix(f)
        df_all = df_temp if df_all is None else df_all.unionByName(df_temp, allowMissingColumns=True)
        print(f"Yes {f.split('/')[-1]}")
    except Exception as e:
        print(f"No {f.split('/')[-1]}: {e}")


df_all.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Bronze.dbo.nyc_taxi_trips")

print(f"\nЗаписано строк: {df_all.count()}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# Finished to work with the Bronze lakehouse, staring with Silver

# MARKDOWN ********************

# Taxi rec. from bronze to silver

# CELL ********************

import pyspark.sql.functions as F

df_taxi = spark.read.table("Bronze.dbo.nyc_taxi_trips")

df_taxi = df_taxi.withColumn(
    "pickup_datetime",
    F.col("tpep_pickup_datetime")
)

df_taxi_silver = df_taxi \
    .dropDuplicates() \
    .filter(
        (F.col("trip_distance") > 0) &
        (F.col("fare_amount") > 0) &
        (F.col("passenger_count") > 0) &
        F.col("pickup_datetime").isNotNull()
    ) \
    .withColumn("year", F.year(F.col("pickup_datetime"))) \
    .withColumn("month", F.month(F.col("pickup_datetime"))) \
    .withColumn("day_of_week", F.dayofweek(F.col("pickup_datetime"))) \
    .withColumn("hour", F.hour(F.col("pickup_datetime"))) \
    .withColumn("fare_eur", F.round(F.col("fare_amount") / 1.08, 2))

df_taxi_silver.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Silver.dbo.nyc_taxi_silver")

print(f"Silver такси записано: {df_taxi_silver.count()}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# OpenAQ from bronze to silver

# CELL ********************

import pyspark.sql.functions as F

df_air = spark.read.table("Bronze.dbo.openaq_measurements")

df_air_silver = df_air \
    .dropDuplicates() \
    .filter(
        (F.col("value") > 0) &
        (F.col("measured_at").isNotNull())
    ) \
    .withColumn("date", F.to_date(F.col("measured_at"))) \
    .withColumn("year", F.year(F.col("measured_at"))) \
    .withColumn("month", F.month(F.col("measured_at"))) \
    .withColumn("day_of_week", F.dayofweek(F.col("measured_at")))

df_air_silver.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Silver.dbo.openaq_silver")

print(f"Silver OpenAQ: {df_air_silver.count()} строк")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# Banks from bronze to silver

# CELL ********************

import pyspark.sql.functions as F

# ECB FX Silver
df_ecb = spark.read.table("Bronze.dbo.ecb_data")

df_ecb_silver = df_ecb \
    .dropDuplicates() \
    .filter(F.col("OBS_VALUE").isNotNull()) \
    .withColumnRenamed("TIME_PERIOD", "date") \
    .withColumnRenamed("OBS_VALUE", "usd_eur_rate") \
    .withColumn("date", F.to_date(F.col("date"))) \
    .filter(
        (F.col("date") >= F.lit("2023-01-01").cast("date")) &
        (F.col("date") <= F.lit("2024-12-31").cast("date"))
    ) \
    .withColumn("year", F.year(F.col("date"))) \
    .withColumn("month", F.month(F.col("date")))

df_ecb_silver.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Silver.dbo.ecb_fx_silver")

print(f"Silver ECB: {df_ecb_silver.count()} строк")

# World Bank GDP Silver
df_gdp = spark.read.table("Bronze.dbo.world_bank_data")

df_gdp_silver = df_gdp \
    .dropDuplicates() \
    .filter(
        F.col("gdp_usd").isNotNull() &
        F.col("year").isin(2023, 2024)
    )
df_gdp_silver.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Silver.dbo.worldbank_gdp_silver")

print(f"Silver GDP: {df_gdp_silver.count()} строк")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# Tables to gold lakehouse

# CELL ********************

import pandas as pd
import pyspark.sql.functions as F

dates = pd.date_range("2023-01-01", "2024-12-31", freq="D")
df_dates = spark.createDataFrame([(str(d.date()),) for d in dates], ["date"])

df_dim_date = df_dates \
    .withColumn("date", F.to_date(F.col("date"))) \
    .withColumn("date_key", F.regexp_replace(F.col("date").cast("string"), "-", "").cast("int")) \
    .withColumn("year", F.year("date")) \
    .withColumn("month", F.month("date")) \
    .withColumn("day", F.dayofmonth("date")) \
    .withColumn("day_of_week", F.dayofweek("date")) \
    .withColumn("quarter", F.quarter("date")) \
    .withColumn("is_weekend", F.dayofweek("date").isin([1, 7]))

df_dim_date.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Gold.dbo.DimDate")

print(f"DimDate записано: {df_dim_date.count()} дней")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# taxi daily

# CELL ********************

import pyspark.sql.functions as F

df_taxi = spark.read.table("Silver.dbo.nyc_taxi_silver")

df_taxi_for_fact = df_taxi.select(
    F.to_date(F.col("pickup_datetime").cast("timestamp")).alias("date"),
    F.col("PULocationID").cast("long").alias("zone_id"),
    F.col("fare_amount").cast("double").alias("fare_amount"),
    F.col("fare_eur").cast("double").alias("fare_eur"),
    F.col("trip_distance").cast("double").alias("trip_distance"),
    F.col("passenger_count").cast("double").alias("passenger_count")
)

df_fact_taxi = df_taxi_for_fact \
    .filter(
        (F.col("date") >= F.lit("2023-01-01").cast("date")) &
        (F.col("date") <= F.lit("2024-12-31").cast("date")) &
        F.col("zone_id").isNotNull() 
    ) \
    .groupBy(
        F.col("date"),
        F.col("zone_id")
    ) \
    .agg(
        F.count("*").alias("trip_count"),
        F.round(F.avg("fare_amount"), 2).alias("avg_fare_usd"),
        F.round(F.sum("fare_amount"), 2).alias("total_fare_usd"),
        F.round(F.avg("fare_eur"), 2).alias("avg_fare_eur"),
        F.round(F.avg("trip_distance"), 2).alias("avg_distance"),
        F.round(F.avg("passenger_count"), 2).alias("avg_passengers")
    ) \
    .withColumn("date_key", F.date_format(F.col("date"), "yyyyMMdd").cast("int"))

spark.sql("DROP TABLE IF EXISTS Gold.dbo.FactTaxiDaily")

df_fact_taxi.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Gold.dbo.FactTaxiDaily")

print(f"FactTaxiDaily записано: {df_fact_taxi.count()} строк")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# FactAirQualityDaily

# CELL ********************

import pyspark.sql.functions as F

df_air_silver = spark.read.table("Silver.dbo.openaq_silver")

df_fact_air = df_air_silver \
    .filter(
        (F.col("date") >= F.lit("2023-01-01").cast("date")) &
        (F.col("date") <= F.lit("2024-12-31").cast("date")) &
        F.col("parameter").isNotNull() &
        F.col("location_name").isNotNull()
    ) \
    .groupBy("date", "parameter", "location_id", "location_name") \
    .agg(
        F.count("*").alias("measurement_count"),
        F.round(F.avg("value"), 2).alias("avg_value"),
        F.round(F.min("value"), 2).alias("min_value"),
        F.round(F.max("value"), 2).alias("max_value"),
        F.round(F.avg("lat"), 6).alias("lat"),
        F.round(F.avg("lon"), 6).alias("lon")
    ) \
    .withColumn("date_key", F.date_format(F.col("date"), "yyyyMMdd").cast("int"))

spark.sql("DROP TABLE IF EXISTS Gold.dbo.FactAirQualityDaily")

df_fact_air.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Gold.dbo.FactAirQualityDaily")

print(f"Gold FactAirQualityDaily: {df_fact_air.count()} строк")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# DimFX и DimGDP


# CELL ********************

import pyspark.sql.functions as F

# DimFXDaily
df_ecb = spark.read.table("Silver.dbo.ecb_fx_silver")

df_ecb.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Gold.dbo.DimFX")

print(f"DimFX записано: {df_ecb.count()} строк")

# DimGDPYearly
df_gdp = spark.read.table("Silver.dbo.worldbank_gdp_silver")

df_gdp.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Gold.dbo.DimGDP")

print(f"DimGDP записано: {df_gdp.count()} строк")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# Visualization

# CELL ********************

import pyspark.sql.functions as F
import pandas as pd
import matplotlib.pyplot as plt

df_taxi = spark.read.table("Gold.dbo.FactTaxiDaily")
df_air = spark.read.table("Gold.dbo.FactAirQualityDaily")

# Фильтр только 2023-2024
df_taxi_day = df_taxi \
    .filter((F.col("date") >= "2023-01-01") & (F.col("date") <= "2024-12-31")) \
    .groupBy("date").agg(
        F.sum("trip_count").alias("total_trips"),
        F.round(F.avg("avg_fare_usd"), 2).alias("avg_fare")
    )

df_air_filtered = df_air \
    .filter((F.col("date") >= "2023-01-01") & (F.col("date") <= "2024-12-31"))

df_air_pivot = df_air_filtered.groupBy("date").pivot("parameter",
    ["pm25", "no2", "o3", "co"]).agg(F.avg("avg_value"))

df_joined = df_taxi_day.join(df_air_pivot, on="date", how="inner")
pdf = df_joined.toPandas().sort_values("date")

print(f"Строк после JOIN: {len(pdf)}")
print("\nМатрица корреляций:")
print(pdf[["total_trips", "pm25", "no2", "o3", "co"]].corr())

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
params = ["pm25", "no2", "o3", "co"]

for ax, param in zip(axes.flatten(), params):
    data = pdf[["total_trips", param]].dropna()
    ax.scatter(data["total_trips"], data[param], alpha=0.4, color="steelblue")
    ax.set_xlabel("Поездки такси в день")
    ax.set_ylabel(param.upper())
    ax.set_title(f"Такси vs {param.upper()}")
    r = data["total_trips"].corr(data[param])
    ax.annotate(f"r = {r:.3f}", xy=(0.05, 0.9), xycoords="axes fraction", fontsize=12)

plt.tight_layout()
plt.show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import requests

BASE_URL = "https://api.openaq.org/v3"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "X-API-Key": "4ba172a012af7a04c271fca0f6807767323206b74c708461394961a153b185ec"
}

from collections import defaultdict

param_dates = defaultdict(list)

for loc in locations:
    date_last = loc.get('datetimeLast', {})
    if date_last:
        last = date_last.get('utc', '')
        for s in loc.get("sensors", []):
            param = s['parameter']['name']
            param_dates[param].append(last)

for param, dates in sorted(param_dates.items()):
    active_2023 = [d for d in dates if d >= '2023-01-01']
    print(f"{param}: всего сенсоров={len(dates)}, активных в 2023+={len(active_2023)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import pyspark.sql.functions as F

spark.read.table("Bronze.dbo.openaq_measurements") \
    .filter((F.col("measured_at") >= "2023-01-01")) \
    .groupBy("parameter").count().orderBy("count", ascending=False).show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import time

for param_name in ["co", "o3"]:
    print(f"\n=== {param_name.upper()} сенсоры ===")
    sensors_param = []
    for loc in locations:
        for sensor in loc.get("sensors", []):
            if sensor.get("parameter", {}).get("name") == param_name:
                sensors_param.append({
                    "sensor_id": sensor["id"],
                    "location": loc["name"]
                })
    
    for s in sensors_param:
        r2 = requests.get(
            f"{BASE_URL}/sensors/{s['sensor_id']}/days",
            headers=HEADERS,
            params={
                "datetime_from": "2022-01-01T00:00:00Z",
                "datetime_to": "2024-12-31T00:00:00Z",
                "limit": 1
            }
        )
        results = r2.json().get("results", [])
        if results:
            last = results[0]["period"]["datetimeFrom"]["utc"]
            print(f"Сенсор {s['sensor_id']} ({s['location']}): {last}")
        else:
            print(f"Сенсор {s['sensor_id']} ({s['location']}): нет данных за 2022-2024")
        time.sleep(0.3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import time

for param_name in ["co", "o3"]:
    print(f"\n=== {param_name.upper()} — последние доступные данные ===")
    for loc in locations:
        for sensor in loc.get("sensors", []):
            if sensor.get("parameter", {}).get("name") == param_name:
                r2 = requests.get(
                    f"{BASE_URL}/sensors/{sensor['id']}/days",
                    headers=HEADERS,
                    params={"limit": 1}
                )
                results = r2.json().get("results", [])
                if results:
                    last = results[0]["period"]["datetimeFrom"]["utc"]
                    print(f"Сенсор {sensor['id']} ({loc['name']}): {last}")
                time.sleep(0.3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
