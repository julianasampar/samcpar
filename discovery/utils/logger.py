import duckdb

def ingest_metadata(json, database, database_table):
    connection = duckdb.connect(database)
    connection.sql(f"""CREATE TABLE IF NOT EXISTS {database_table} ( 
                        interaction_log JSON,
                        inserted_at TIMESTAMP
                    );
                    """)
    connection.execute(f"""INSERT INTO {database_table} VALUES 
                        (?, CURRENT_TIMESTAMP);
                        """, 
                        [json]
                    )