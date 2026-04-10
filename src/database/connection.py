import psycopg2

#database connection parameters
DB_HOST = 'localhost'
DB_NAME = 'inversiones_clientes'
DB_USER = 'postgres'
DB_PASSWORD = '1234'
DB_PORT = '5432'

#connect to the database
def connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    return conn

