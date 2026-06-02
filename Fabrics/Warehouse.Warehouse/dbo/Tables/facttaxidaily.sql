CREATE TABLE [dbo].[facttaxidaily] (

	[date] date NULL, 
	[zone_id] bigint NULL, 
	[trip_count] bigint NULL, 
	[avg_fare_usd] float NULL, 
	[total_fare_usd] float NULL, 
	[avg_fare_eur] float NULL, 
	[avg_distance] float NULL, 
	[avg_passengers] float NULL, 
	[date_key] int NULL
);