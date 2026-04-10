-- Active: 1775777294201@@127.0.0.1@5432@inversiones_clientes
-- Database
--CREATE DATABASE inversiones_clientes

-- Creación de esquemas para organizar el pipeline de datos: 
-- raw (datos crudos), clean (datos depurados) y final (datos listos para análisis)
CREATE SCHEMA raw;
CREATE SCHEMA clean;
CREATE SCHEMA final;
--- Tablas para los datos de perfil de riesgo, activos y banca, que no requieren procesamiento adicional, se almacenarán directamente en el esquema clean.
CREATE TABLE final.cat_perfil_riesgo (
    cod_perfil_riesgo TEXT PRIMARY KEY,
    perfil_riesgo TEXT NOT NULL
);

CREATE TABLE final.catalogo_activos (
    activo TEXT NOT NULL,
    cod_activo TEXT PRIMARY KEY
);

CREATE TABLE final.catalogo_banca (
    banca TEXT NOT NULL,
    cod_banca TEXT PRIMARY KEY
);

-- Tablas para almacenar los datos sin procesar de historico macroactivos e historico internacional (raw) 
CREATE TABLE raw.historico_macroactivos (
    ingestion_year TEXT,
    ingestion_month TEXT,
    ingestion_day TEXT,
    id_sistema_cliente TEXT,
    macroactivo TEXT,
    cod_activo TEXT,
    aba TEXT,
    cod_perfil_riesgo TEXT,
    cod_banca TEXT,
    year TEXT,
    month TEXT
);

CREATE TABLE raw.historico_internacional (
    ingestion_year TEXT,
    ingestion_month TEXT,
    ingestion_day TEXT,
    id_sistema_cliente TEXT,
    simbol TEXT,
    cusip TEXT,
    isin TEXT,
    nombre_activo TEXT,
    cantidad TEXT,
    valor_mercado TEXT,
    fecha_vencimiento TEXT,
    tasa_cupon TEXT
);