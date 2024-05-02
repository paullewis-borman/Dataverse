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

# Main script execution
if __name__ == "__main__":
    entity = 'your_entity_name'  # Replace with the actual entity name
    metadata = fetch_dataverse_metadata(entity)
    sql_statements = generate_sql_create_statements(metadata)
    # Write SQL statements to a .sql file
    with open('database_schema.sql', 'w') as sql_file:
        for statement in sql_statements:
            sql_file.write(statement + "\n\n")

