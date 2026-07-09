import argparse
import csv
import json

import requests

# Load the type mappings from the JSON file
with open('type_mapping.json', 'r') as file:
    type_mapping = json.load(file)


# Define the function to fetch metadata from Dataverse
def fetch_dataverse_metadata(entity):
    url = f"https://your-dataverse-api-endpoint/entities/{entity}/metadata"
    headers = {
        'Authorization': 'Bearer your_access_token',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    return response.json()


# --- Helpers for reading optional/nested metadata fields safely ---

def get_display_name(item):
    """Return an item's display label, falling back to its logical name."""
    label = (item.get('DisplayName') or {}).get('UserLocalizedLabel') or {}
    return label.get('Label') or item.get('LogicalName', '')


def get_required_level(attribute):
    """Return the RequiredLevel value (e.g. ApplicationRequired, None, Recommended)."""
    return (attribute.get('RequiredLevel') or {}).get('Value', '')


# Function to generate SQL CREATE TABLE statements
def generate_sql_create_statements(entity_metadata):
    sql_commands = []
    for entity in entity_metadata:
        table_name = entity['LogicalName']
        sql = f"CREATE TABLE {table_name} (\n"
        columns = []
        for attribute in entity['Attributes']:
            dataverse_type = attribute['AttributeType']
            sql_type = type_mapping.get(dataverse_type, 'NVARCHAR(MAX)')
            column_name = attribute['LogicalName']
            column_definition = f"    {column_name} {sql_type}"
            if attribute.get('IsPrimaryKey', False):
                column_definition += " PRIMARY KEY"
            columns.append(column_definition)
        sql += ",\n".join(columns)
        sql += "\n);"
        sql_commands.append(sql)
    return sql_commands


# Function to flatten entity metadata into documentation rows
# (one row per column), used by the CSV/Excel documentation output.
def generate_documentation_rows(entity_metadata):
    rows = []
    for entity in entity_metadata:
        entity_logical_name = entity['LogicalName']
        entity_display_name = get_display_name(entity)
        for attribute in entity['Attributes']:
            dataverse_type = attribute['AttributeType']
            sql_type = type_mapping.get(dataverse_type, 'NVARCHAR(MAX)')
            rows.append({
                'Entity (Logical Name)': entity_logical_name,
                'Entity (Display Name)': entity_display_name,
                'Column (Logical Name)': attribute['LogicalName'],
                'Column (Display Name)': get_display_name(attribute),
                'Dataverse Type': dataverse_type,
                'SQL Server Type': sql_type,
                'Primary Key': attribute.get('IsPrimaryKey', False),
                'Required Level': get_required_level(attribute),
            })
    return rows


def write_sql_file(sql_statements, output_path):
    with open(output_path, 'w') as sql_file:
        for statement in sql_statements:
            sql_file.write(statement + "\n\n")


def write_csv_file(rows, output_path):
    fieldnames = [
        'Entity (Logical Name)', 'Entity (Display Name)',
        'Column (Logical Name)', 'Column (Display Name)',
        'Dataverse Type', 'SQL Server Type', 'Primary Key', 'Required Level',
    ]
    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx_file(rows, output_path):
    # Imported lazily so csv/sql output doesn't require openpyxl to be installed.
    from openpyxl import Workbook
    from openpyxl.styles import Font

    fieldnames = [
        'Entity (Logical Name)', 'Entity (Display Name)',
        'Column (Logical Name)', 'Column (Display Name)',
        'Dataverse Type', 'SQL Server Type', 'Primary Key', 'Required Level',
    ]

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Dataverse Structure'

    sheet.append(fieldnames)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        sheet.append([row[field] for field in fieldnames])

    # Auto-size columns roughly based on content length.
    for column_cells in sheet.columns:
        length = max(len(str(cell.value)) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 60)

    sheet.freeze_panes = 'A2'
    workbook.save(output_path)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Fetch Dataverse entity metadata and generate either a SQL Server '
                    'schema or a documentation output (CSV/Excel) of the structure.'
    )
    parser.add_argument(
        '--entity', default='your_entity_name',
        help='Logical name of the Dataverse entity to fetch metadata for.'
    )
    parser.add_argument(
        '--format', choices=['sql', 'csv', 'xlsx'], default='sql',
        help='Output format: sql (CREATE TABLE statements, default), '
             'csv or xlsx (tabular documentation of the structure).'
    )
    parser.add_argument(
        '--output',
        help='Output file path. Defaults to database_schema.sql, '
             'dataverse_structure.csv, or dataverse_structure.xlsx depending on --format.'
    )
    return parser.parse_args()


# Main script execution
if __name__ == "__main__":
    args = parse_args()
    metadata = fetch_dataverse_metadata(args.entity)

    default_output = {
        'sql': 'database_schema.sql',
        'csv': 'dataverse_structure.csv',
        'xlsx': 'dataverse_structure.xlsx',
    }[args.format]
    output_path = args.output or default_output

    if args.format == 'sql':
        sql_statements = generate_sql_create_statements(metadata)
        write_sql_file(sql_statements, output_path)
    else:
        doc_rows = generate_documentation_rows(metadata)
        if args.format == 'csv':
            write_csv_file(doc_rows, output_path)
        else:
            write_xlsx_file(doc_rows, output_path)

    print(f"Wrote {args.format} output to {output_path}")
