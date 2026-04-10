
import os
import pandas as pd
from .connection import connection


def load_data(file_path, table_name, cur):
    
    df = pd.read_csv(file_path)
    
    df.columns = [col.lower().strip() for col in df.columns]

    columns = ','.join(df.columns)
    place = ','.join(['%s'] * len(df.columns))

    query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({place}) 
    """

    rows = [tuple(row) for row in df.to_numpy()]
    
    cur.executemany(query, rows)
    


def load_tables():

    base_path = "data/"

    archivos = {
        "cat_perfil_riesgo.csv": "final.cat_perfil_riesgo",
        "catalogo_activos.csv": "final.catalogo_activos",
        "catalogo_banca.csv": "final.catalogo_banca",
        "historico_aba_macroactivos.csv": "raw.historico_macroactivos",
        "historico_aba_usd_internacional.csv": "raw.historico_internacional"
    }
    
    conn = connection()
    cur = conn.cursor()
    
    for file, table in archivos.items():
        path = os.path.join(base_path, file)

        if not os.path.exists(path):
                print(f"[AVISO] No se encontró: {path}")
                continue
        
        print(f"[INFO] Cargando {file} en {table}...")
        
        load_data(path, table, cur)
        
    conn.commit()
    
    print("[INFO] Carga de datos finalizada.")
    
    cur.close()
    conn.close()