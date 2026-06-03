# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.12"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************


# CELL ********************

%pip install azure-kusto-data great_expectations pandas requests

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

CLUSTER = "https://trd-hfb2q528r4e8qyku5p.z7.kusto.fabric.microsoft.com"
DATABASE = "Eventhouse"

kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(CLUSTER)
client = KustoClient(kcsb)

query = """
weather_hourly_enriched
| take 10
"""

response = client.execute(DATABASE, query)

rows = [row.to_dict() for row in response.primary_results[0]]
rows

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import pandas as pd

query = """
weather_hourly_enriched
| where ts > ago(7d)
| project
    ts,
    location_key,
    location_name,
    latitude,
    longitude,
    temperature_c,
    relative_humidity_pct,
    dew_point_c,
    apparent_temperature_c,
    precipitation_mm,
    rain_mm,
    snowfall_cm,
    weather_code,
    weather_condition,
    cloud_cover_pct,
    surface_pressure_hpa,
    wind_speed_ms,
    wind_gusts_ms,
    heat_index_c,
    wind_chill_c,
    comfort_index,
    is_raining,
    is_snowing,
    source,
    fetched_at
"""

response = client.execute(DATABASE, query)
df = pd.DataFrame([row.to_dict() for row in response.primary_results[0]])

print(df.head())
print(df.shape)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import great_expectations as gx
from datetime import datetime

context = gx.get_context(mode="ephemeral")

source = context.data_sources.add_pandas(name="fabric_eventhouse")
asset = source.add_dataframe_asset(name="weather_hourly_enriched")
batch_def = asset.add_batch_definition_whole_dataframe("batch")
batch = batch_def.get_batch(batch_parameters={"dataframe": df})

suite = context.suites.add(gx.ExpectationSuite(name="weather_quality_suite"))
validator = context.get_validator(batch=batch, expectation_suite=suite)

validator.expect_table_row_count_to_be_between(min_value=1)

validator.expect_column_values_to_not_be_null("ts")
validator.expect_column_values_to_not_be_null("location_name")
validator.expect_column_values_to_not_be_null("temperature_c", mostly=0.95)

validator.expect_column_values_to_be_between("temperature_c", min_value=-50, max_value=60)
validator.expect_column_values_to_be_between("relative_humidity_pct", min_value=0, max_value=100)
validator.expect_column_values_to_be_between("precipitation_mm", min_value=0)
validator.expect_column_values_to_be_between("rain_mm", min_value=0)
validator.expect_column_values_to_be_between("snowfall_cm", min_value=0)
validator.expect_column_values_to_be_between("cloud_cover_pct", min_value=0, max_value=100)
validator.expect_column_values_to_be_between("wind_speed_ms", min_value=0)
validator.expect_column_values_to_be_between("wind_gusts_ms", min_value=0)

validator.expect_column_distinct_values_to_be_in_set("is_raining", value_set=[True, False])
validator.expect_column_distinct_values_to_be_in_set("is_snowing", value_set=[True, False])

result = validator.validate()
stats = result["statistics"]

summary = f"""
Weather Data Quality Report
Source: Fabric Eventhouse / weather_hourly_enriched
Generated: {datetime.utcnow().isoformat()} UTC
Rows checked: {len(df)}

Success: {result["success"]}
Evaluated expectations: {stats["evaluated_expectations"]}
Successful: {stats["successful_expectations"]}
Failed: {stats["unsuccessful_expectations"]}
"""

print(summary)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

failures = []

for item in result["results"]:
    if not item["success"]:
        expectation_type = item["expectation_config"]["type"]
        kwargs = item["expectation_config"]["kwargs"]
        column = kwargs.get("column", "table")
        unexpected_count = item["result"].get("unexpected_count", "n/a")
        unexpected_percent = item["result"].get("unexpected_percent", "n/a")

        failures.append({
            "expectation": expectation_type,
            "column": column,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
        })

failures_df = pd.DataFrame(failures)

print(failures_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

null_summary = df.isna().sum().sort_values(ascending=False).reset_index()
null_summary.columns = ["column", "null_count"]
null_summary["null_percent"] = (null_summary["null_count"] / len(df) * 100).round(2)

numeric_summary = df.select_dtypes(include="number").describe().T.reset_index()
numeric_summary = numeric_summary.rename(columns={"index": "column"})

print("NO FAILURES FOUND")
print()
print("NULL SUMMARY")
print(null_summary.head(20))
print()
print("NUMERIC SUMMARY")
print(numeric_summary)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import json
from datetime import datetime

report = {
    "report_name": "Weather Data Quality Report",
    "source": "Fabric Eventhouse / weather_hourly_enriched",
    "generated_at_utc": datetime.utcnow().isoformat(),
    "rows_checked": int(len(df)),
    "success": bool(result["success"]),
    "statistics": {
        "evaluated_expectations": int(stats["evaluated_expectations"]),
        "successful_expectations": int(stats["successful_expectations"]),
        "unsuccessful_expectations": int(stats["unsuccessful_expectations"]),
    },
    "failures": failures,
    "null_summary": null_summary.head(20).to_dict(orient="records"),
    "numeric_summary": numeric_summary.to_dict(orient="records"),
    "first_rows": df.head(5).astype(str).to_dict(orient="records"),
}

report_json = json.dumps(report, indent=2, ensure_ascii=False)

print(report_json[:4000])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

from pathlib import Path

timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

report_dir = Path("/lakehouse/default/Files/quality_reports")
report_dir.mkdir(parents=True, exist_ok=True)

report_path = report_dir / f"weather_quality_report_{timestamp}.json"

report_path.write_text(report_json, encoding="utf-8")

print(f"Report saved: {report_path}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

TELEGRAM_BOT_TOKEN = str(globals().get("telegram_bot_token", "")).strip()
TELEGRAM_CHAT_ID = str(globals().get("telegram_chat_id", "")).strip()

print("telegram_bot_token in globals:", "telegram_bot_token" in globals())
print("telegram_chat_id in globals:", "telegram_chat_id" in globals())
print("token exists:", bool(TELEGRAM_BOT_TOKEN))
print("token length:", len(TELEGRAM_BOT_TOKEN))
print("chat id:", TELEGRAM_CHAT_ID)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

TELEGRAM_BOT_TOKEN = 

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
