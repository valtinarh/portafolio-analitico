-- Active: 1775777294201@@127.0.0.1@5432@inversiones_clientes

-- Limpieza de datos: Copia de tablas desde raw a clean
CREATE TABLE clean.copia_internacional (
    LIKE raw.historico_internacional INCLUDING ALL);
INSERT INTO clean.copia_internacional
SELECT *
FROM raw.historico_internacional;

CREATE TABLE clean.copia_macroactivos (
    LIKE raw.historico_macroactivos INCLUDING ALL);
INSERT INTO clean.copia_macroactivos
SELECT *
FROM raw.historico_macroactivos;

-- Verificación de datos: Conteo de registros en tablas limpias
SELECT 'copia_internacional' AS tabla, COUNT(*) AS total_registros
FROM clean.copia_internacional;

SELECT 'copia_macroactivos' AS tabla, COUNT(*) AS total_registros
FROM clean.copia_macroactivos;

-- Limpieza tabla de macroactivos:
-- 0. Agregar nuevas columnas para almacenar los datos limpios
ALTER TABLE clean.copia_macroactivos 
    ADD COLUMN new_ingestion_day TEXT,
    ADD COLUMN new_macroactivo TEXT,
    ADD COLUMN new_cod_activo TEXT,
    ADD COLUMN new_aba TEXT,
    ADD COLUMN new_cod_perfil TEXT,
    ADD COLUMN new_cod_banca TEXT,
    ADD COLUMN new_year TEXT,
    ADD COLUMN new_month TEXT,
    ADD COLUMN new_id_sistema TEXT;

-- 1. Limpiar la columna ingestion_day: Si la longitud es mayor a 2, asignar '0', de lo contrario mantener el valor original

UPDATE clean.copia_macroactivos
SET new_ingestion_day = 
CASE 
    WHEN LENGTH(ingestion_day) > 2 THEN '1'
    ELSE ingestion_day
END
WHERE ingestion_day IS NOT NULL;


-- 2. Limpiar la columna id_sistema_cliente:
DELETE FROM clean.copia_macroactivos
WHERE id_sistema_cliente = 'NaN';

UPDATE clean.copia_macroactivos
SET new_id_sistema = 
CASE 
    WHEN id_sistema_cliente ~ '^[0-9]+' 
        AND id_sistema_cliente ~ '[A-Za-z]' 
        AND id_sistema_cliente NOT ILIKE '%E+%' 
    THEN substring(id_sistema_cliente FROM '^[0-9]+')
    ELSE id_sistema_cliente
END;

UPDATE clean.copia_macroactivos
SET new_id_sistema = 
CASE 
    WHEN length(ingestion_day::text) > 2
    THEN new_id_sistema || ingestion_day::text
    ELSE new_id_sistema
END;

UPDATE clean.copia_macroactivos
SET new_id_sistema = 
CASE 
	WHEN macroactivo::text ~ '^[0-9]+$' 
        AND length(macroactivo::text) > 5
    THEN new_id_sistema || macroactivo::text
	ELSE new_id_sistema
END;

-- 3. Limpiar la columna macroactivo: 
UPDATE clean.copia_macroactivos
SET new_macroactivo = 
CASE 
    WHEN cod_activo IN ('FICs', 'Renta Variable') 
    THEN cod_activo
    ELSE macroactivo
END;

UPDATE clean.copia_macroactivos
SET new_macroactivo = 
CASE 
    WHEN id_sistema_cliente ~ '^[0-9]+(FICs|Renta Variable)$' 
    THEN regexp_replace(id_sistema_cliente, '^[0-9]+', '')
    ELSE new_macroactivo
END;

-- 4. Limpiar la columna cod_activo:
UPDATE clean.copia_macroactivos
SET new_cod_activo = 
CASE 
    WHEN cod_activo = '10007' OR aba = '10007.0'
    THEN '1007'
    ELSE cod_activo
END;

UPDATE clean.copia_macroactivos
SET new_cod_activo = 
CASE
	WHEN LENGTH(aba) <= 6 AND aba LIKE '10%'
	THEN aba
    ELSE new_cod_activo
END;

UPDATE clean.copia_macroactivos
SET new_cod_activo = 
CASE
	WHEN LENGTH(macroactivo) <= 6 AND macroactivo LIKE '10%'
	THEN macroactivo
    ELSE new_cod_activo
END;

-- 5. Limpiar la columna aba:
UPDATE clean.copia_macroactivos
SET new_aba = 
CASE
	WHEN LENGTH(cod_perfil_riesgo) > 6 
	THEN cod_perfil_riesgo
    ELSE aba
END;

UPDATE clean.copia_macroactivos
SET new_aba = 
CASE
	WHEN LENGTH(cod_activo) > 6 
	AND cod_activo ~ '^[0-9.]+$'
	THEN cod_activo
    ELSE new_aba
END;

-- 6. Limpiar la columna cod_perfil_riesgo:
UPDATE clean.copia_macroactivos
SET new_cod_perfil = 
CASE
	WHEN LENGTH(aba) < 7 AND aba LIKE '14%'
	THEN aba
    ELSE cod_perfil_riesgo
END;

UPDATE clean.copia_macroactivos
SET new_cod_perfil = 
CASE
	WHEN cod_banca LIKE '14%'
	THEN cod_banca
    ELSE new_cod_perfil
END;

UPDATE clean.copia_macroactivos
SET new_cod_perfil = 
CASE
	WHEN cod_perfil_riesgo = 'PN'
	THEN ''
    ELSE new_cod_perfil
END;

-- 7. Limpiar la columna cod_banca:
UPDATE clean.copia_macroactivos
SET new_cod_banca = 
CASE
	WHEN LENGTH(cod_perfil_riesgo) = 2
	THEN cod_perfil_riesgo
    ELSE cod_banca
END;

UPDATE clean.copia_macroactivos
SET new_cod_banca = 
CASE
	WHEN LENGTH(year) = 2 
	THEN year
    ELSE new_cod_banca
END;

-- 8. Limpiar la columna year:
UPDATE clean.copia_macroactivos
SET new_year = ingestion_year;

-- 9. Limpiar la columna month:
UPDATE clean.copia_macroactivos
SET ingestion_month = 
CASE
	WHEN ingestion_month = 'NaN' 
	THEN month
    ELSE ingestion_month 
END;

UPDATE clean.copia_macroactivos
SET new_month = ingestion_month;


-- 10. Duplicados
CREATE TABLE clean.nueva_tabla AS
SELECT DISTINCT *
FROM clean.copia_macroactivos;

DROP TABLE clean.copia_macroactivos;
ALTER TABLE clean.nueva_tabla RENAME TO hist_macroactivos;

-- 11. Celdas vacías en macroactivo: 
UPDATE clean.hist_macroactivos a
SET new_macroactivo = b.new_macroactivo
FROM clean.hist_macroactivos b
WHERE a.new_id_sistema = b.new_id_sistema
  AND a.new_cod_activo = b.new_cod_activo
  AND a.ctid <> b.ctid;

-- 12. Celdas vacías en cod_perfil_riesgo:
UPDATE clean.hist_macroactivos a
SET new_cod_perfil = b.new_cod_perfil
FROM clean.hist_macroactivos b
WHERE a.new_id_sistema = b.new_id_sistema
  AND a.ctid <> b.ctid;


UPDATE clean.hist_macroactivos
SET new_cod_perfil = 
CASE
    WHEN new_cod_perfil = 'NaN'
    THEN '1466'
    ELSE new_cod_perfil
END;

--13. Celdas vacías en cod_banca:
UPDATE clean.hist_macroactivos a
SET new_cod_banca = b.new_cod_banca
FROM clean.hist_macroactivos b
WHERE a.new_id_sistema = b.new_id_sistema
  AND a.ctid <> b.ctid;

-- 14. Celdas vacías en cod_activo:

UPDATE clean.hist_macroactivos m
SET new_cod_activo = sub.moda
FROM (
    SELECT new_id_sistema,
           MODE() WITHIN GROUP (ORDER BY new_cod_activo) AS moda
    FROM clean.hist_macroactivos
    WHERE new_cod_activo IS NOT NULL
    GROUP BY new_id_sistema
) sub
WHERE m.new_id_sistema = sub.new_id_sistema
  AND m.new_cod_activo = 'NaN';
------------------------------------
-- Limpieza tabla de internacional:
DELETE FROM clean.copia_internacional
WHERE tasa_cupon = 'NaN' OR tasa_cupon ~ '[0-9]{1}/[0-9]{2}/[0-9]{4}';

-- Duplicados
CREATE TABLE clean.nueva_tabla AS
SELECT DISTINCT *
FROM clean.copia_internacional;

DROP TABLE clean.copia_internacional;
ALTER TABLE clean.nueva_tabla RENAME TO hist_internacional;

UPDATE clean.hist_internacional
SET simbol = 
CASE
    WHEN simbol = 'NaN' THEN 'Desconocido'
    ELSE simbol
END;
-- Pasar datos limpios a la tabla final
CREATE TABLE final.histo_macroactivos AS
SELECT
	ingestion_year,
	ingestion_month,
	new_ingestion_day AS ingestion_day,
	new_id_sistema::NUMERIC AS id_sistema_cliente,
	new_macroactivo AS macroactivo,
	new_cod_activo AS cod_activo,
	new_aba::NUMERIC AS aba,
	new_cod_perfil AS cod_perfil,
	new_cod_banca AS cod_banca,
	new_year AS year,
	new_month AS month
FROM clean.hist_macroactivos;

CREATE TABLE final.histo_internacional AS
SELECT
	ingestion_year,
	ingestion_month,
	ingestion_day,
	id_sistema_cliente::NUMERIC,
    simbol,
	cusip,
	isin,
	nombre_activo,
	cantidad::NUMERIC,
	valor_mercado::NUMERIC,
	TO_DATE(fecha_vencimiento, 'MM/DD/YYYY'),
	tasa_cupon::NUMERIC
FROM clean.hist_internacional;
