# Dataverse

Documents the structure of a Microsoft Dataverse entity as a SQL Server schema, and generates a matching staging table for importing data into Dataverse.

## What it does

Dataverse doesn't expose its entity structure as a plain schema — `dataverse.py` fills that gap. It calls the Dataverse Web API to fetch metadata for a given entity (its attributes and their types), then converts that metadata into a SQL Server `CREATE TABLE` statement, writing it to `database_schema.sql`. Dataverse field types (e.g. `Text`, `Currency`, `Lookup`) are mapped to SQL Server column types using `type_mapping.json`.

The main uses are:

- **Documentation** — a readable, versionable SQL representation of an entity's structure, instead of digging through Dataverse's metadata API by hand.
- **Import prep** — the generated `CREATE TABLE` statement can be used as a staging table (e.g. in Azure SQL) that a pipeline such as Azure Data Factory (ADF) lands data into, before mapping and pushing it into Dataverse.

Note: this only pulls schema/metadata, not row data. It documents structure — it doesn't move data itself. Actually loading data into (or out of) Dataverse still needs separate code or a pipeline (e.g. an ADF copy activity) built against this schema.

## Files

- `dataverse.py` — fetches entity metadata and generates the SQL schema file.
- `type_mapping.json` — maps Dataverse attribute types to SQL Server column types.

## How it works

1. `fetch_dataverse_metadata(entity)` requests `{entity}/metadata` from the Dataverse API using a bearer token.
2. `generate_sql_create_statements(entity_metadata)` walks each entity's attributes, looks up the matching SQL type (falling back to `NVARCHAR(MAX)` for unmapped types), and marks primary keys.
3. The resulting `CREATE TABLE` statements are written to `database_schema.sql`.

## Installation

```bash
git clone https://github.com/paullewis-borman/Dataverse
cd Dataverse
pip install requests
```

## Usage

Before running, edit `dataverse.py` to set:

- `url` — your actual Dataverse API endpoint (currently a placeholder).
- `Authorization` header — a valid bearer token for your Dataverse environment.
- `entity` — the logical name of the entity you want a schema for.

Then run:

```bash
python dataverse.py
```

This creates (or overwrites) `database_schema.sql` in the project directory.

## Notes / limitations

- Credentials and the API endpoint are hardcoded placeholders — not suitable for production use as-is (no config file or env vars, no auth flow).
- Only handles a single entity per run.
- Any Dataverse attribute type not listed in `type_mapping.json` defaults to `NVARCHAR(MAX)`.
