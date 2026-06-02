CREATE TABLE [dbo].[dimdate] (

	[date] date NULL, 
	[date_key] int NULL, 
	[year] int NULL, 
	[month] int NULL, 
	[day] int NULL, 
	[day_of_week] int NULL, 
	[quarter] int NULL, 
	[is_weekend] bit NULL
);