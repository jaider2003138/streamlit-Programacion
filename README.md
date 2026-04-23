# Dashboard COVID Colombia

Aplicacion web desarrollada con Streamlit para extraer, limpiar, almacenar y analizar datos de COVID en Colombia usando una API publica y MongoDB Atlas.

Integra en una sola solucion:

- extraccion desde `datos.gov.co`
- limpieza y enriquecimiento del dataset
- persistencia en MongoDB Atlas
- visualizacion interactiva
- analisis descriptivo y predictivo
- despliegue con Docker y Render

## Arquitectura

El proyecto sigue una arquitectura modular por responsabilidades, con capas ligeras dentro de una aplicacion multipagina de Streamlit:

- **Presentacion**: `app.py` y `pages/`
- **Servicios de datos**: `api_service.py`, `mongo_db.py`
- **Procesamiento y preparacion**: `data_cleaning.py`, `covid_dataframe_utils.py`
- **Analitica y visualizacion**: `covid_forecasting.py`, `covid_visualization_utils.py`, `covid_dashboard_module.py`
- **Utilidades de interfaz**: `dashboard_page_utils.py`, `ui_styles.py`

## Funcionalidades principales

- Carga de datos desde la API publica de COVID Colombia
- Almacenamiento en MongoDB Atlas
- Limpieza automatizada del dataset
- Variables derivadas para analisis temporal y demografico
- Filtros interactivos por periodo, territorio, sexo, edad, estado, contagio, ubicacion y recuperacion
- Analisis de preguntas de negocio en una sola pagina
- Pronosticos de casos y mortalidad
- Exportacion de resultados filtrados
- Ejecucion local y despliegue con Docker

## Preguntas de negocio que responde

La pagina de analisis responde estas preguntas:

1. En que meses se concentro el mayor numero de casos reportados?
2. Que departamentos y ciudades concentran mas casos en el periodo filtrado?
3. Que grupos de edad tienen mayor participacion y como cambia su peso en el tiempo?
4. Existen diferencias por sexo en el total de casos y en los fallecimientos?
5. Como se relacionan el volumen de casos y la mortalidad en el tiempo?
6. Que territorios y poblaciones conviene priorizar cuando se analiza la severidad?
7. Que tan rapido se diagnostican los casos y donde hay mayor demora?
8. Como cambia el origen del contagio y la ubicacion del caso en el filtro actual?

## Estructura del proyecto

```text
streamlit-main/
├── Dockerfile
├── render.yaml
├── README.md
├── .dockerignore
├── .gitignore
├── .env
├── .streamlit/
│   └── config.toml
└── proyecto_streamlit/
    ├── .env.example
    ├── app.py
    ├── api_service.py
    ├── auto_update.py
    ├── covid_dashboard_module.py
    ├── covid_dataframe_utils.py
    ├── covid_forecasting.py
    ├── covid_visualization_utils.py
    ├── dashboard_page_utils.py
    ├── data_cleaning.py
    ├── mongo_db.py
    ├── requirements.txt
    ├── ui_styles.py
    ├── data_exports/
    ├── docs/
    │   └── limpieza_dataset_covid.md
    └── pages/
        ├── 1_Cargar_Datos.py
        ├── 2_Ver_Datos.py
        └── 3_Analisis.py
```

## Archivos clave

- `proyecto_streamlit/app.py`: portada del dashboard y contexto del proyecto
- `proyecto_streamlit/pages/1_Cargar_Datos.py`: descarga desde API y guardado en MongoDB
- `proyecto_streamlit/pages/2_Ver_Datos.py`: exploracion tabular y filtros de consulta
- `proyecto_streamlit/pages/3_Analisis.py`: analisis de negocio y visualizaciones
- `proyecto_streamlit/api_service.py`: cliente de la API publica
- `proyecto_streamlit/mongo_db.py`: conexion, lectura y escritura en MongoDB Atlas
- `proyecto_streamlit/data_cleaning.py`: limpieza, estandarizacion y variables derivadas
- `proyecto_streamlit/dashboard_page_utils.py`: utilidades compartidas de filtros y carga
- `proyecto_streamlit/covid_dashboard_module.py`: integracion de preparacion, pronostico y graficas

## Variables de entorno

Copia `proyecto_streamlit/.env.example` a `.env` en la raiz del proyecto y ajusta:

```env
MONGO_USER=tu_usuario
MONGO_PASSWORD=tu_password
MONGO_HOST=tu_host_mongodb_atlas
MONGO_DB=tu_base
API_URL=https://www.datos.gov.co/resource/gt2j-8ykr.json
COLLECTION_NAME=datos_api
```

Variables usadas por la app:

- `MONGO_USER`
- `MONGO_PASSWORD`
- `MONGO_HOST`
- `MONGO_DB`
- `API_URL`
- `COLLECTION_NAME`

Variables opcionales para automatizacion:

- `AUTO_UPDATE_FULL_DATA=true`
- `AUTO_UPDATE_LIMIT=5000`
- `AUTO_UPDATE_BATCH_SIZE=5000`

## Requisitos

- Python 3.11 o compatible
- MongoDB Atlas accesible desde tu red o desde Render
- Docker Desktop si vas a usar contenedores

## Ejecucion local sin Docker

Instala dependencias:

```bash
pip install -r proyecto_streamlit/requirements.txt
```

Ejecuta la app:

```bash
streamlit run proyecto_streamlit/app.py
```

La aplicacion quedara disponible en:

```text
http://localhost:8501
```

## Ejecucion con Docker

Construir la imagen:

```bash
docker build --no-cache -t streamlit-covid-dashboard .
```

Ejecutar el contenedor:

```bash
docker run --env-file .env -p 8501:8501 streamlit-covid-dashboard
```

La aplicacion quedara disponible en:

```text
http://localhost:8501
```

Si quieres construirla compatible con despliegue en Render:

```bash
docker build --platform linux/amd64 --no-cache -t streamlit-covid-dashboard .
```

## Publicacion en Docker Hub

Ejemplo de flujo para publicar la imagen:

```bash
docker build --platform linux/amd64 --no-cache -t streamlit-covid-dashboard .
docker tag streamlit-covid-dashboard TU_USUARIO/streamlit-covid-dashboard:latest
docker push TU_USUARIO/streamlit-covid-dashboard:latest
```

## Despliegue en Render

Este proyecto puede desplegarse de dos formas:

- desde `Dockerfile`
- desde una imagen ya publicada en Docker Hub

### Opcion 1: Dockerfile en Render

Render detecta el `Dockerfile` y usa el comando definido en la imagen.

### Opcion 2: Existing Image en Render

Si subiste la imagen a Docker Hub, en Render puedes usar:

```text
docker.io/TU_USUARIO/streamlit-covid-dashboard:latest
```

Variables de entorno que debes configurar en Render:

- `MONGO_USER`
- `MONGO_PASSWORD`
- `MONGO_HOST`
- `MONGO_DB`
- `API_URL`
- `COLLECTION_NAME`

No necesitas crear manualmente `PORT`; Render lo inyecta automaticamente y el `Dockerfile` ya lo soporta.

## Flujo de uso recomendado

1. Configura el archivo `.env`
2. Inicia la app
3. Ve a `Cargar Datos`
4. Descarga una muestra o realiza una carga completa
5. Revisa el contenido en `Ver Datos`
6. Explora los hallazgos en `Analisis`

## Notas operativas importantes

- La carga manual desde la interfaz esta limitada a `60000` registros para evitar problemas de rendimiento y estabilidad.
- La opcion `Usar el 100% de los datos del endpoint` sigue disponible, pero puede tardar varios minutos y consumir mas memoria.
- La escritura en MongoDB ahora se realiza por lotes para soportar mejor cargas medianas y grandes.
- La limpieza del dataset se ejecuta una sola vez por flujo de carga, evitando trabajo duplicado.
- La conexion a MongoDB reutiliza el cliente para reducir errores intermitentes de DNS en Atlas.

## Limpieza y transformacion de datos

El proceso de limpieza:

- normaliza nombres de columnas
- elimina columnas no utiles
- estandariza sexo, estado, contagio, ubicacion, departamento y ciudad
- convierte fechas relevantes
- calcula grupos de edad
- construye variables temporales como `anio_reporte` y `mes_reporte`
- calcula diferencias de dias entre sintomas, diagnostico, recuperacion y muerte

Documentacion complementaria:

- `proyecto_streamlit/docs/limpieza_dataset_covid.md`

## Automatizacion sin interfaz

Puedes actualizar la coleccion sin abrir Streamlit:

Carga completa:

```bash
python proyecto_streamlit/auto_update.py --full
```

Carga limitada:

```bash
python proyecto_streamlit/auto_update.py --limit 5000
```

Esto permite programar actualizaciones con Task Scheduler en Windows o `cron` en Linux.

## Archivos auxiliares

- `proyecto_streamlit/data_exports/`: ejemplos y artefactos locales de apoyo; no son necesarios para la ejecucion normal de la app
- `render.yaml`: alternativa de despliegue sin imagen Docker prepublicada
- `.dockerignore`: excluye archivos innecesarios del build, incluyendo `data_exports`

## Consideraciones de seguridad

- No publiques credenciales reales en el repositorio
- Si una contraseña fue expuesta, rotala en MongoDB Atlas
- Mantén `.env` fuera de control de versiones

## Estado actual del proyecto

El proyecto se encuentra operativo para:

- carga de datos desde API
- persistencia en MongoDB Atlas
- exploracion y filtrado
- analisis descriptivo
- pronostico basico
- despliegue con Docker y Render

## Autor

Proyecto academico/practico de visualizacion y analisis de datos con Streamlit, MongoDB Atlas, Docker y Render.
