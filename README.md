# 📊 Herramienta Analítica de Portafolios de Inversión

Este proyecto desarrolla una solución analítica para visualizar, analizar y generar insights sobre portafolios de clientes, integrando múltiples fuentes de datos mediante PostgreSQL, SQL y Python.

La herramienta permite a equipos comerciales y estructuradores entender mejor el comportamiento de sus clientes y tomar decisiones basadas en datos.

## 🎯 Objetivo

Construir una herramienta que permita:

- Integrar información de clientes desde múltiples fuentes
- Limpiar y transformar datos usando SQL
- Visualizar portafolios locales (COP) e internacionales (USD)
- Generar conocimiento mediante modelos analíticos


## 🏗️ Arquitectura del Pipeline

El flujo del proyecto es el siguiente:

1. Ingesta de datos:
   Los archivos CSV son cargados automáticamente a PostgreSQL mediante scripts en Python.

2. Almacenamiento:
    Los datos se almacenan en tablas crudas (data raw).

3. Procesamiento:
    Se realiza limpieza y transformación de datos utilizando SQL (data clean).

4. Consolidación:
   Se construyen vistas que integran y agregan la información (data final).

5. Modelado:
   Se aplican modelos de clustering para segmentar clientes y generar recomendaciones.

6. Visualización:
   Se desarrolla un dashboard interactivo para explorar los portafolios.


## 🗂️ Estructura del proyecto

portafolio-analitico/
│ 
├── docs/                  
├── etl/                   
├── models/                   
├── notebooks/             
├── src/                  
├── video/                 
├── README.md 


## ⚙️ Tecnologías

- Python
- PostgreSQL
- SQL
- Pandas
- SQLAlchemy
- Dash / Plotly
- Scikit-learn (modelo analítico)

## 🧱 Base de Datos

Se creó una base de datos en PostgreSQL con una tabla por cada archivo CSV:

- cat_perfil_riesgo
- catalogo_activos
- catalogo_banca
- historico_aba_macroactivos
- historico_aba_usd_internacional

## 🧹 Procesamiento de datos

La transformación se realizó principalmente en SQL mediante:

- Se identificó que habia filas con datos corridos o en celdas que no correspondian, se identificaron esos patrones y se modificó columna por columna para organizar los datos.
- Se limpió los valores nulos 
- Se Normalizaron los de datos
- Se hizo integración de tablas mediante JOINs
- Se crearon vistas analíticas


## 📊 Vistas principales

- vw_portafolio_base → integración de datos
- vw_portafolio_actual → última fecha disponible
- vw_portafolio_cliente → valor total por cliente
- vw_composicion_activos → distribución por activo


## 📈 Visualización

Se desarrolló un dashboard interactivo con Dash que permite:

- Seleccionar clientes
- Visualizar portafolios en COP y USD
- Analizar la composición por activos

## 🚀 Ejecución

1. Clonar repositorio:
```bash
git clone https://github.com/tu_usuario/portafolio-analitico.git
```
2. Instalar dependencias:
```bash
pip install -r requirements.txt
```
3. Configurar conexión a PostgreSQL

4. Ejecutar carga de datos:
```bash
python src/main.py
```
5. Ejecutar dashboard:
```bash
python src/dashboard/app.py
```