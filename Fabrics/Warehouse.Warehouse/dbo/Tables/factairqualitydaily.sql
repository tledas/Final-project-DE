CREATE TABLE [dbo].[factairqualitydaily] (

	[date] date NULL, 
	[parameter] varchar(8000) NULL, 
	[location_id] int NULL, 
	[location_name] varchar(8000) NULL, 
	[measurement_count] bigint NULL, 
	[avg_value] float NULL, 
	[min_value] float NULL, 
	[max_value] float NULL, 
	[lat] float NULL, 
	[lon] float NULL, 
	[date_key] int NULL
);