from database.connection import connection
from database.load_data import load_tables

def run_sql_query(path):
    conn = connection()
    cur = conn.cursor()
    
    with open(path, 'r', encoding='utf-8') as f:
        query = f.read()

    queries = query.split(';')
    for query in queries:
        query = query.strip()
        
        if not query: 
            continue
        
        cur.execute(query)
    
        if cur.description is not None:
            resultados = cur.fetchall()

            for fila in resultados[:5]:
                print(fila)
        
    conn.commit()
    
    cur.close()
    conn.close()


def run_querys():
    print("Creando tablas en la base de datos...")
    run_sql_query("etl/create_tables.sql")
    print("Tablas creadas correctamente.")
    print("Cargando tablas en la base de datos...")
    load_tables()
    print("Tablas cargadas correctamente.")
    print("Ejecutando consultas SQL...")
    run_sql_query("etl\clean_data.sql")
    print("Consultas ejecutadas correctamente.")
    run_sql_query("etl\\views.sql")
    print("Vistas creadas correctamente.")
    print("Proceso de ejecución de consultas SQL finalizado.")

   
   