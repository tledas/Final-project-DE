# Microsoft Fabric Data Engineering Project

End-to-end analytics project in **Microsoft Fabric** combining **NYC Yellow Taxi (2023–2024)**, **OpenAQ air quality**, **World Bank GDP**, and **ECB USD/EUR FX rates**. Built with **Bronze → Silver → Gold** medallion architecture, modeled in a **Warehouse star schema**, and visualized in a **Power BI report**.

## Architecture
Sources → Lakehouse (Bronze/Silver/Gold) → Warehouse → Semantic Model → Power BI Report

## Data Sources
- NYC TLC Yellow Taxi Trips (monthly Parquet)
- OpenAQ Air Quality (NYC stations, pollutant measurements)
- World Bank GDP (USA, yearly)
- ECB FX (USD/EUR, daily)

## What’s Built
- Lakehouse layers: Bronze ingestion, Silver cleaning, Gold modeling
- Warehouse tables: `FactTaxiDaily`, `FactAirQualityDaily`, `DimDate`, `DimZone`, `DimFX`, `DimGDP`
- Report-ready tables: GDP yearly context and FX daily conversion comparison
- Power BI report pages: Taxi, Air Quality, Taxi vs Air Quality, Economy (GDP & FX)

## Key Findings (Short)
- Taxi activity and pollution show similar time patterns, but the direct relationship is weak.
- NYC yellow taxi revenue is a very small share of annual US GDP.
- EUR results differ when using daily ECB rates vs a fixed conversion rate.

## Repository Structure
- `sql/` Warehouse SQL (aggregations, report tables, validation)
- `notebooks/bronze/` ingestion notebooks/scripts
- `notebooks/silver/` cleaning & standardization
- `notebooks/gold/` fact/dim modeling + report tables
- `visuals/` report screenshots / visuals
- `dataflow/` Dataflow Gen2 (Power Query/M) scripts or exports
- `docs/` final documentation (`.docx` / `.pdf`)

## Notes
- Raw source files are not stored in this repo.
- Do not commit API keys/secrets.
