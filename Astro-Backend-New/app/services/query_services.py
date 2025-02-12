import pymysql as psql  # type: ignore
from dotenv import load_dotenv

import os
import logging
from typing import Optional, List, Dict, Any

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to connect to the database
def connect_to_db() -> Optional[psql.connections.Connection]:
    """
    Establishes a connection to the database using credentials from environment variables.

    Returns:
        psql.connections.Connection: The database connection object.
        None: If the connection fails.
    """
    try:
        # Fetch environment variables
        host = os.getenv("DB_HOST")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")
        
        # Check for missing environment variables
        if not all([host, user, password, database]):
            logging.error("Missing one or more required database environment variables (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).")
            return None

        # Establish the database connection
        conn = psql.connect(
            host=host,
            user=user,
            passwd=password,
            database=database,
            connect_timeout=10  # Optional: Specify a timeout for connection attempts
        )
        logging.info("Database connection established successfully.")
        return conn
    except psql.MySQLError as e:
        logging.exception("Failed to connect to the database.")
        return None

# Function to execute a query and fetch data
def get_query_data(query: str) -> Optional[List[Dict[str, Any]]]:
    """
    Executes a SQL query and returns the results as a list of dictionaries.

    Args:
        query (str): The SQL query to execute.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries where each dictionary represents a row.
        None: If no results are found or an error occurs.
    """
    try:
        # Connect to the database
        conn = connect_to_db()
        if not conn:
            logging.error("Database connection is unavailable. Cannot execute the query.")
            return None

        # Use 'with' to ensure proper resource cleanup
        with conn.cursor() as cur:
            # Execute the query
            cur.execute(query)

            # Fetch all rows
            query_results = cur.fetchall()

            if query_results:
                # Extract column names from cursor description
                columns = [col[0] for col in cur.description]

                # Convert rows into a list of dictionaries
                result_dict = [dict(zip(columns, row)) for row in query_results]

                logging.info(f"Query executed successfully. Retrieved {len(result_dict)} rows.")
                return result_dict
            else:
                logging.info("Query executed successfully but returned no results.")
                return None
    except psql.MySQLError as e:
        logging.exception("An error occurred while executing the query.")
        return None
    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()
            logging.info("Database connection closed.")
