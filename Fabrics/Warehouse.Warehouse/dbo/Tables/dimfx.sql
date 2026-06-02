CREATE TABLE [dbo].[dimfx] (

	[CURRENCY] varchar(8000) NULL, 
	[CURRENCY_DENOM] varchar(8000) NULL, 
	[date] date NULL, 
	[usd_eur_rate] float NULL, 
	[year] int NULL, 
	[month] int NULL
);