[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "ECB data_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "CURRENCY", DestinationColumnName = "CURRENCY"], [SourceColumnName = "CURRENCY_DENOM", DestinationColumnName = "CURRENCY_DENOM"], [SourceColumnName = "TIME_PERIOD", DestinationColumnName = "TIME_PERIOD"], [SourceColumnName = "OBS_VALUE", DestinationColumnName = "OBS_VALUE"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared #"ECB data" = let
    Source = Csv.Document(Web.Contents("https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata"), [Delimiter = ",", Columns = 32, QuoteStyle = QuoteStyle.None]),
    #"Promoted headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {{"KEY", type text}, {"FREQ", type text}, {"CURRENCY", type text}, {"CURRENCY_DENOM", type text}, {"EXR_TYPE", type text}, {"EXR_SUFFIX", type text}, {"TIME_PERIOD", type date}, {"OBS_VALUE", type number}, {"OBS_STATUS", type text}, {"OBS_CONF", type text}, {"OBS_PRE_BREAK", type text}, {"OBS_COM", type text}, {"TIME_FORMAT", type duration}, {"BREAKS", type text}, {"COLLECTION", type text}, {"COMPILING_ORG", type text}, {"DISS_ORG", type text}, {"DOM_SER_IDS", type text}, {"PUBL_ECB", type text}, {"PUBL_MU", type text}, {"PUBL_PUBLIC", type text}, {"UNIT_INDEX_BASE", type text}, {"COMPILATION", type text}, {"COVERAGE", type text}, {"DECIMALS", Int64.Type}, {"NAT_TITLE", type text}, {"SOURCE_AGENCY", type text}, {"SOURCE_PUB", type text}, {"TITLE", type text}, {"TITLE_COMPL", type text}, {"UNIT", type text}, {"UNIT_MULT", Int64.Type}}),
    #"Removed columns" = Table.RemoveColumns(#"Changed column type", {"KEY", "FREQ", "EXR_TYPE", "EXR_SUFFIX", "OBS_STATUS", "OBS_CONF", "OBS_PRE_BREAK", "OBS_COM", "TIME_FORMAT", "BREAKS", "COLLECTION", "COMPILING_ORG", "DISS_ORG", "DOM_SER_IDS", "PUBL_ECB", "PUBL_MU", "PUBL_PUBLIC", "UNIT_INDEX_BASE", "COMPILATION", "COVERAGE", "DECIMALS", "NAT_TITLE", "SOURCE_AGENCY", "SOURCE_PUB", "TITLE", "TITLE_COMPL", "UNIT", "UNIT_MULT"}),
    #"Filtered rows" = Table.SelectRows(#"Removed columns", each 
        [TIME_PERIOD] >= #date(2023, 1, 1) and 
        [TIME_PERIOD] <= #date(2024, 12, 31))
in
    #"Filtered rows";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "World bank data_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "year", DestinationColumnName = "year"], [SourceColumnName = "gdp_usd", DestinationColumnName = "gdp_usd"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared #"World bank data" = let
    Source = Json.Document(Web.Contents("https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&per_page=100")),
    Data = Source{1},
    ToTable = Table.FromList(Data, Splitter.SplitByNothing(), {"Column1"}),
    Expanded = Table.ExpandRecordColumn(ToTable, "Column1", {"date", "value"}, {"year", "gdp_usd"}),
    FilteredRows = Table.SelectRows(Expanded, each [year] = "2023" or [year] = "2024"),
    ChangedType = Table.TransformColumnTypes(FilteredRows, {{"year", Int64.Type}, {"gdp_usd", type number}})
in
    ChangedType;
shared #"World bank data_DataDestination" = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "74ae7af4-8788-4bea-b8c4-b8377fd376c7"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "dba5cd7e-a9c2-4a49-84d6-97d63db82beb"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "world_bank_data", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared #"ECB data_DataDestination" = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "74ae7af4-8788-4bea-b8c4-b8377fd376c7"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "dba5cd7e-a9c2-4a49-84d6-97d63db82beb"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "ecb_data", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
