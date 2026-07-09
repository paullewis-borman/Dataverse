# Dataverse

Documents the structure of a Microsoft Dataverse entity — as a SQL Server schema, or as a CSV/Excel documentation output — and can generate a matching staging table for importing data into Dataverse.

## What it does

Dataverse doesn't expose its entity structure as a plain schema — `dataverse.py` fills that gap. It calls the Dataverse Web API to fetch metadata for a given entity (its attributes and their types), then converts that metadata into one of:

- a SQL Server `CREATE TABLE` statement (`--format sql`, default), or
- a flat, one-row-per-column documentation table as CSV or Excel (`--format csv` / `--format xlsx`), including entity/column display names, the Dataverse type, the mapped SQL type, primary key flag, and required level.

Dataverse field types (e.g. `Text`, `Currency`, `Lookup`) are mapped to SQL Server column types using `type_mapping.json`.

The main uses are:

- **Documentation** — a readable, versionable representation of an entity's structure (SQL for engineers, CSV/Excel for sharing with non-technical stakeholders), instead of digging through Dataverse's metadata API by hand.
- **Import prep** — the generated `CREATE TABLE` statement can be used as a staging table (e.g. in Azure SQL) that a pipeline such as Azure Data Factory (ADF) lands data into, before mapping and pushing it into Dataverse.

Note: this only pulls schema/metadata, not row data. It documents structure — it doesn't move data itself. Actually loading data into (or out of) Dataverse still needs separate code or a pipeline (e.g. an ADF copy activity) built against this schema.

## Files

- `dataverse.py` — fetches entity metadata and generates the SQL schema file.
- `type_mapping.json` — maps Dataverse attribute types to SQL Server column types.

## How it works

1. `fetch_dataverse_metadata(entity)` requests `{entity}/metadata` from the Dataverse API using a bearer token.
2. For `--format sql`, `generate_sql_create_statements(entity_metadata)` walks each entity's attributes, looks up the matching SQL type (falling back to `NVARCHAR(MAX)` for unmapped types), and marks primary keys.
3. For `--format csv`/`--format xlsx`, `generate_documentation_rows(entity_metadata)` flattens each entity's attributes into one row per column (entity/column logical + display name, Dataverse type, mapped SQL type, primary key flag, required level).
4. The result is written to the output file (`database_schema.sql`, `dataverse_structure.csv`, or `dataverse_structure.xlsx` by default).

## Installation

```bash
git clone https://github.com/paullewis-borman/Dataverse
cd Dataverse
pip install requests openpyxl
```

`openpyxl` is only needed for `--format xlsx`.

## Usage

Before running, edit `dataverse.py` to set the `url` and `Authorization` header in `fetch_dataverse_metadata` to your actual Dataverse API endpoint and a valid bearer token.

Then run one of:

```bash
python dataverse.py --entity your_entity_name --format sql    # database_schema.sql (default)
python dataverse.py --entity your_entity_name --format csv    # dataverse_structure.csv
python dataverse.py --entity your_entity_name --format xlsx   # dataverse_structure.xlsx
```

Use `--output <path>` to override the default output file name.

## Notes / limitations

- Credentials and the API endpoint are hardcoded placeholders — not suitable for production use as-is (no config file or env vars, no auth flow).
- Only handles a single entity per run.
- Any Dataverse attribute type not listed in `type_mapping.json` defaults to `NVARCHAR(MAX)`.
- Display names and required level assume the standard Dataverse `EntityDefinitions`/`Attributes` metadata shape (`DisplayName.UserLocalizedLabel.Label`, `RequiredLevel.Value`); if your API response differs, these fields will just fall back to blank/logical name.