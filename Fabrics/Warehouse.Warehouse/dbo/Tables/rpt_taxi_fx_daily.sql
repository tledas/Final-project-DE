CREATE TABLE [dbo].[rpt_taxi_fx_daily] (

	[date] date NULL, 
	[year] int NULL, 
	[month] int NULL, 
	[total_trips] bigint NULL, 
	[total_fare_usd] float NULL, 
	[fixed_fare_eur] float NULL, 
	[theoretical_fare_eur] float NULL, 
	[eur_difference] float NULL, 
	[usd_eur_rate] float NULL
);