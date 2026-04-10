CREATE SCHEMA views;

-- 1. PORTAFOLIO LOCAL (COP)
CREATE OR REPLACE VIEW views.vw_portafolio_local AS
SELECT
    h.id_sistema_cliente,
    h.cod_activo,
    a.activo  AS nombre_activo,
    h.macroactivo,
    h.aba  AS valor,
    'COP' AS moneda,
    h.cod_perfil,
    p.perfil_riesgo,
    h.cod_banca,
    b.banca,
    h.ingestion_year,
    h.ingestion_month,
    h.ingestion_day
FROM final.histo_macroactivos h
INNER JOIN final.catalogo_activos   a ON h.cod_activo  = a.cod_activo
LEFT  JOIN final.cat_perfil_riesgo  p ON h.cod_perfil  = p.cod_perfil_riesgo
LEFT  JOIN final.catalogo_banca     b ON h.cod_banca   = b.cod_banca;

-- 2. PORTAFOLIO INTERNACIONAL (USD)
CREATE OR REPLACE VIEW views.vw_portafolio_internacional AS
SELECT
    id_sistema_cliente,
    simbol AS cod_activo,
    nombre_activo,
    NULL AS macroactivo,
    valor_mercado AS valor,
    'USD'  AS moneda,
    NULL AS perfil_riesgo,
    NULL AS banca,
    ingestion_year,
    ingestion_month,
    ingestion_day
FROM final.histo_internacional;

-- 3. PORTAFOLIO TOTAL (COP + USD)
CREATE OR REPLACE VIEW views.vw_portafolio_total AS
SELECT
    id_sistema_cliente,
    cod_activo,
    nombre_activo,
    macroactivo,
    valor,
    moneda,
    perfil_riesgo,
    banca,
    ingestion_year,
    ingestion_month,
    ingestion_day
FROM views.vw_portafolio_local
UNION ALL
SELECT
    id_sistema_cliente,
    cod_activo,
    nombre_activo,
    macroactivo,
    valor,
    moneda,
    perfil_riesgo,
    banca,
    ingestion_year,
    ingestion_month,
    ingestion_day
FROM views.vw_portafolio_internacional;

-- 4. PORTAFOLIO ACTUAL (última fecha disponible)
CREATE OR REPLACE VIEW views.vw_portafolio_actual AS
SELECT *
FROM views.vw_portafolio_total
WHERE TO_DATE(
    ingestion_year || '-' ||
    LPAD(SPLIT_PART(ingestion_month::text, '.', 1), 2, '0') || '-' ||
    LPAD(SPLIT_PART(ingestion_day::text,   '.', 1), 2, '0'),
    'YYYY-MM-DD'
) = (
    SELECT MAX(
        TO_DATE(
            ingestion_year || '-' ||
            LPAD(SPLIT_PART(ingestion_month::text, '.', 1), 2, '0') || '-' ||
            LPAD(SPLIT_PART(ingestion_day::text,   '.', 1), 2, '0'),
            'YYYY-MM-DD'
        )
    )
    FROM views.vw_portafolio_total
);
 
-- 5. RESUMEN POR CLIENTE
CREATE OR REPLACE VIEW views.vw_resumen_cliente AS
SELECT
    id_sistema_cliente,
    moneda,
    COUNT(DISTINCT nombre_activo)   AS num_activos,
    SUM(valor) AS total_portafolio
FROM views.vw_portafolio_actual
GROUP BY id_sistema_cliente, moneda;

-- 6. COMPOSICIÓN POR ACTIVO

CREATE OR REPLACE VIEW views.vw_composicion_activos AS
SELECT
    id_sistema_cliente,
    moneda,
    macroactivo,
    nombre_activo,
    SUM(valor) AS valor
FROM views.vw_portafolio_actual
GROUP BY id_sistema_cliente, moneda, macroactivo, nombre_activo;
 

-- 7. COMPOSICIÓN CON PESO PORCENTUAL (nuevo)

CREATE OR REPLACE VIEW views.vw_composicion_pct AS
SELECT
    id_sistema_cliente,
    moneda,
    macroactivo,
    nombre_activo,
    valor,
    ROUND(
        valor / NULLIF(
            SUM(valor) OVER (PARTITION BY id_sistema_cliente, moneda),0
            ) * 100,
    2)                              AS pct_portafolio
FROM views.vw_composicion_activos;

-- 8. MÉTRICAS POR CLIENTE
CREATE OR REPLACE VIEW views.vw_metricas_cliente AS
SELECT
    id_sistema_cliente,
    SUM(CASE WHEN moneda = 'COP' THEN valor ELSE 0 END) AS aum_cop,
    SUM(CASE WHEN moneda = 'USD' THEN valor ELSE 0 END) AS aum_usd,
    SUM(valor) AS aum_total,
    COUNT(DISTINCT nombre_activo) AS num_activos,
    COUNT(DISTINCT macroactivo)  AS num_macroactivos,
    COUNT(DISTINCT moneda) AS num_monedas,    
    MAX(valor) / NULLIF(SUM(valor), 0) * 100 AS pct_mayor_posicion,
    SUM(CASE WHEN moneda = 'USD' THEN valor ELSE 0 END)
    / NULLIF(SUM(valor), 0) * 100  AS pct_exposicion_usd,
    MODE() WITHIN GROUP (ORDER BY perfil_riesgo)  AS perfil_riesgo,
    MODE() WITHIN GROUP (ORDER BY banca) AS banca
FROM views.vw_portafolio_actual
GROUP BY id_sistema_cliente;
 