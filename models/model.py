import psycopg2
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Conexión a PostgreSQL
conn = psycopg2.connect(
        host="localhost",
        database="inversiones_clientes",
        user="postgres",
        password="1234"
)
def query_to_df(sql: str) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)

# Cargar datos desde la vista
df = query_to_df("SELECT * FROM views.vw_metricas_cliente")

# Preparar datos para clustering
features = [
    "aum_total",
    "num_activos",
    "pct_mayor_posicion",
    "pct_exposicion_usd"
]

# Asegurar que los datos sean numéricos y manejar nulos
df[features] = df[features].astype(float).fillna(0)

X = StandardScaler().fit_transform(df[features])

##
resultados = []
for k in range(2, 8):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    resultados.append({
        "k": k,
        "inercia": km.inertia_,
        "silhouette": silhouette_score(X, labels)
    })

df_eval = pd.DataFrame(resultados)

#modelo
K_OPTIMO = 4  # ajusta según el output de arriba

km_final = KMeans(n_clusters=K_OPTIMO, random_state=42, n_init=10)
df["segmento"] = km_final.fit_predict(X)

## Análisis de segmentos
perfil = (
    df.groupby("segmento")[features]
    .mean()
    .round(2)
)
print("\nPerfil por segmento:")
print(perfil.to_string())

# Guardar resultados en la base de datos
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS final.cliente_segmento (
            id_sistema_cliente BIGINT PRIMARY KEY,
            segmento           INTEGER,
            aum_total          NUMERIC,
            num_activos        INTEGER,
            pct_mayor_posicion NUMERIC,
            pct_exposicion_usd NUMERIC
        )
    """)

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO final.cliente_segmento
                (id_sistema_cliente, segmento, aum_total, num_activos,
                 pct_mayor_posicion, pct_exposicion_usd)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_sistema_cliente) DO UPDATE
                SET segmento           = EXCLUDED.segmento,
                    aum_total          = EXCLUDED.aum_total,
                    num_activos        = EXCLUDED.num_activos,
                    pct_mayor_posicion = EXCLUDED.pct_mayor_posicion,
                    pct_exposicion_usd = EXCLUDED.pct_exposicion_usd
        """, (
            int(row["id_sistema_cliente"]),
            int(row["segmento"]),
            float(row["aum_total"]),
            int(row["num_activos"]),
            float(row["pct_mayor_posicion"]),
            float(row["pct_exposicion_usd"])
        ))

    conn.commit()
    print("\nSegmentos guardados en final.cliente_segmento")

conn.close()