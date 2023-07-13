import psycopg2
import os
import json
from datetime import datetime, timezone
import uuid
                    
#Get the environment variables:
username = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "changethis")
postgres_server = os.getenv("POSTGRES_SERVER", "localhost")
postgres_db = os.getenv("POSTGRES_DB", "coproduction")

def migrateDataClaims(connection=None):

    total_inserted_rows = 0


    #Establish the first time connection if dont exist
    if not connection:
        connection = psycopg2.connect(user=username,
                                    password=password,
                                    host=postgres_server,
                                    port="5432",
                                    database=postgres_db)

    cursor = connection.cursor()

    #Fix coproduction tree references:

    #Obtain all parents nodes with multiple dependants (inconsistences)

    query_coproductionprocessnotification = "SELECT id,coproductionprocess_id, asset_id, user_id, parameters, created_at FROM coproductionprocessnotification WHERE claim_type='development';" 
    
    # Execute the query
    cursor.execute(query_coproductionprocessnotification)

    # Fetch all rows
    rows = cursor.fetchall()

    # Print the number of rows
    numeroRows = len(rows)
    print(f'Number of rows: {numeroRows}')

    # Iterate over rows
    for row in rows:
        id,coproductionprocess_id, asset_id, user_id, parameters, created_at = row
       
        parameters_dict = json.loads(parameters)
    
        assetId = parameters_dict.get('assetId')
        commentTitle = parameters_dict.get('commentTitle')
        commentDescription = parameters_dict.get('commentDescription')
        treeitem_id = parameters_dict.get('treeitem_id')
        
        print(f'coproductionprocess_id: {coproductionprocess_id}, asset_id: {asset_id}, user_id: {user_id}, assetId: {assetId}, task_id: {treeitem_id}, created_at {created_at}, commentTitle: {commentTitle}')

        #Insert the new claim
        query_insert_claim = """
            INSERT INTO claim (id, user_id, asset_id, task_id, coproductionprocess_id, title, description, state, claim_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
            ON CONFLICT (id) DO NOTHING RETURNING id;
        """
        values = (id,user_id, asset_id, treeitem_id, coproductionprocess_id, commentTitle, commentDescription, False, 'development')
        cursor.execute(query_insert_claim, values)
        
        result = cursor.fetchone()
        
        if result is not None:
            claim_id = result[0]
            connection.commit()  # Commit the transaction

            #Update the created_at field
            query_update_claim = "UPDATE claim SET created_at = %s WHERE id = %s;"
            values = (created_at, claim_id)
            cursor.execute(query_update_claim, values)

            connection.commit()  # Commit the transaction

            total_inserted_rows += 1

            print(f'claim_id: {claim_id} created_at: {created_at}')

        else:
            print(f'A row with id {id} already exists.')
    
    print(f'Total inserted rows: {total_inserted_rows}')

        

       

migrateDataClaims()    