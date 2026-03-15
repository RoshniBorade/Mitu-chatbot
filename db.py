import os
import pymysql
import re
import pymysql.converters
from pymysql.constants import FIELD_TYPE
from dotenv import load_dotenv

load_dotenv()

class MySQLCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor

    def _convert_query(self, query):
        # Extremely simple ? to %s converter.
        # It replaces ? with %s correctly in strings if they are not in quotes.
        # But for most simple queries, replacing ? with %s is sufficient.
        # Just replace ? with %s
        return query.replace('?', '%s')

    def execute(self, query, args=None):
        converted_query = self._convert_query(query)
        if args is not None:
            self.cursor.execute(converted_query, args)
        else:
            self.cursor.execute(converted_query)

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()
        
    @property
    def lastrowid(self):
        return self.cursor.lastrowid

class MySQLConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return MySQLCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        self.close()

def connect(database=None):
    # Connect to MySQL server without database first to ensure the db exists
    host = os.environ.get("MYSQL_HOST", "localhost")
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "")
    db_name = os.environ.get("MYSQL_DB", "mitu_chatbot_db")
    
    # Check if database exists, create if not
    temp_conn = pymysql.connect(
        host=host,
        user=user,
        password=password
    )
    with temp_conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    temp_conn.close()

    conv = pymysql.converters.conversions.copy()
    conv[FIELD_TYPE.DATETIME] = str
    conv[FIELD_TYPE.TIMESTAMP] = str
    conv[FIELD_TYPE.DATE] = str

    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.Cursor, # default returns tuple
        conv=conv
    )
    return MySQLConnectionWrapper(conn)

# Fallback for Exceptions
IntegrityError = pymysql.err.IntegrityError
