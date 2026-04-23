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

## Informe general de análisis de casos
Comparación entre panorama general y filtro territorial Antioquia – Medellín y Bello
1. Objetivo del análisis

El objetivo de este análisis es identificar los principales patrones de comportamiento de los casos reportados, evaluando su evolución en el tiempo, su distribución territorial y demográfica, su relación con la mortalidad, la oportunidad diagnóstica y las características del contagio. Para ello, se comparan dos niveles de lectura:

Panorama general sin filtro, para entender el comportamiento agregado.
Filtro territorial específico en Antioquia, Medellín y Bello, para profundizar en un caso puntual y contrastarlo con la dinámica global.

Este enfoque permite pasar de una lectura descriptiva a una interpretación de negocio, que es justamente lo que exige una visualización útil: responder preguntas reales y producir hallazgos accionables.

2. Hallazgos ejecutivos principales

En términos generales, el fenómeno presenta una alta concentración temporal en el segundo semestre de 2020, una distribución geográfica desigual, una mayor participación de adultos entre 30 y 44 años en el volumen de casos, y una mayor severidad en la población de 60 años o más. Además, se observa que la transmisión fue principalmente comunitaria, que la mayoría de los casos se ubicó en casa, y que el diagnóstico ocurrió en promedio alrededor de 10 días después del inicio de síntomas.

Al comparar con el filtro de Antioquia, Medellín y Bello, se mantiene la mayor parte de la estructura general: la concentración temporal sigue ocurriendo en 2020, Medellín domina claramente frente a Bello, los grupos de 30-44 y 18-29 años siguen concentrando el mayor número de casos, y el grupo de 60+ continúa siendo el de mayor severidad. Sin embargo, en este filtro las brechas por sexo son más moderadas y varias comparaciones territoriales pierden fuerza porque solo queda un departamento.

3. Análisis temporal de los casos
3.1 Panorama general sin filtro

En el análisis general, la mayor concentración de casos se presentó entre julio y diciembre de 2020. El pico más alto ocurrió en agosto de 2020 con 3473 casos, seguido por noviembre (2983), julio (2940) y diciembre (2904). En conjunto, esto muestra que el fenómeno no estuvo distribuido uniformemente en el tiempo, sino que se concentró en una fase crítica muy marcada durante el segundo semestre de 2020.

La variación mes a mes muestra un crecimiento fuerte entre mitad de año y finales de 2020, seguido de una caída brusca a partir de 2021. Esto sugiere una etapa de rápida expansión y luego una fase de reducción sostenida.

3.2 Filtro Antioquia – Medellín y Bello

En el filtro específico, la historia temporal se conserva, aunque a menor escala. La mayor concentración se presentó entre julio y noviembre de 2020, con pico en agosto de 2020 (414 casos), seguido por noviembre (385) y julio (355). A partir de 2021 también se observa una caída sostenida hasta niveles mínimos.

3.3 Lectura comparativa

El filtro territorial reproduce el patrón global: la fase crítica sigue estando en el segundo semestre de 2020. La diferencia es que, en el nivel local, el volumen es menor y el período de mayor presión se ve más acotado. Esto sugiere que Antioquia, y particularmente Medellín y Bello, siguieron la lógica general del fenómeno, sin comportarse como una excepción temporal.

4. Concentración territorial de los casos
4.1 Panorama general sin filtro

A nivel agregado, la concentración territorial es fuerte. Los mayores volúmenes se observaron en:

Bogotá: 5323 casos
Antioquia: 3279
Valle: 1725
Cundinamarca: 972
Santander: 744

En participación relativa, Bogotá concentró 38.7%, Antioquia 23.8% y Valle 12.5%. Entre los tres reunieron la mayor parte del volumen total.

A nivel de ciudades, los mayores registros correspondieron a:

Bogotá: 5323
Medellín: 1810
Cali: 1321
Barranquilla: 620
Cartagena: 522

Esto confirma que la carga del fenómeno estuvo localizada en pocos territorios y ciudades principales.

4.2 Filtro Antioquia – Medellín y Bello

Dentro del filtro, la comparación territorial útil ya no es entre departamentos, porque solo queda Antioquia. La comparación relevante pasa a ser entre ciudades:

Medellín: 1810 casos
Bello: 363 casos

Medellín concentra aproximadamente 83.3% de los casos del filtro, mientras Bello aporta 16.7%.

4.3 Lectura comparativa

En el panorama general, Antioquia aparece como uno de los territorios más relevantes del país. Dentro de Antioquia, esa concentración se traslada casi por completo a Medellín. En otras palabras, Medellín no solo pesa mucho dentro del filtro local, sino que también es una de las ciudades más importantes en el análisis agregado.

5. Participación por grupo de edad
5.1 Panorama general sin filtro

Los grupos con mayor participación fueron:

30-44 años: 6743 casos (33.7%)
18-29 años: 4657 (23.3%)
45-59 años: 4229 (21.1%)
60+: 3108 (15.5%)
0-17: 1263 (6.31%)

Esto muestra que la mayor carga de casos se concentró en adultos jóvenes y de mediana edad, especialmente en la población económicamente activa.

5.2 Filtro Antioquia – Medellín y Bello

En el filtro específico se repite la misma estructura:

30-44 años: 789 casos (36.3%)
18-29 años: 637 (29.3%)
45-59 años: 395 (18.2%)
60+: 208 (9.57%)
0-17: 144 (6.63%)
5.3 Cambio del peso en el tiempo

En ambos niveles de análisis, los grupos 30-44 y 18-29 dominan durante los meses de mayor incidencia. Hay variaciones mensuales, pero la jerarquía general se mantiene: lideran los adultos jóvenes y de mediana edad, mientras 0-17 conserva el menor peso relativo.

5.4 Lectura comparativa

La estructura etaria del filtro local es muy consistente con la del panorama general. La diferencia más visible es que en Antioquia, Medellín y Bello, el peso de 30-44 y 18-29 es incluso más fuerte proporcionalmente, mientras el grupo de 60+ participa menos en volumen, aunque no en severidad.

6. Diferencias por sexo
6.1 Panorama general sin filtro

En el total de casos, la diferencia entre sexos fue pequeña:

Masculino: 10.113
Femenino: 9.887

En fallecimientos sí apareció una diferencia más marcada:

Masculino: 62.4%
Femenino: 37.6%

Esto indica que la distribución de casos era casi paritaria, pero la participación masculina dentro de los fallecimientos era claramente mayor.

6.2 Filtro Antioquia – Medellín y Bello

En el filtro específico:

Masculino: 1159 casos
Femenino: 1014 casos

En fallecimientos:

Masculino: 55%
Femenino: 45%
6.3 Lectura comparativa

En ambos niveles hay una ligera mayor participación masculina en casos y fallecimientos, pero la brecha es más fuerte en el panorama general que en el filtro local. En Antioquia, Medellín y Bello, la diferencia por sexo existe, pero es más moderada.

7. Relación entre volumen de casos y mortalidad
7.1 Panorama general sin filtro

Los meses con mayor volumen de casos también concentraron mayores fallecimientos. La relación entre ambas variables fue claramente positiva: cuando aumentaron los casos, también aumentó la mortalidad en términos absolutos, especialmente en el segundo semestre de 2020.

La dispersión confirmó esta asociación ascendente, aunque no perfectamente lineal.

7.2 Filtro Antioquia – Medellín y Bello

En el filtro específico se observa el mismo patrón general: los meses de mayor incidencia coinciden con los mayores niveles de mortalidad. Sin embargo, el pico de fallecimientos no coincide exactamente con el mes de máximo volumen de casos, lo que indica que la relación es positiva pero no mecánica.

7.3 Lectura comparativa

Tanto a nivel general como local, la mortalidad acompaña la fase crítica del fenómeno. La diferencia es que, en el análisis local, esta asociación se ve más irregular y con menor volumen absoluto. En ambos casos, lo correcto es hablar de relación positiva general, no de una proporcionalidad exacta.

8. Severidad y priorización
8.1 Panorama general sin filtro

Cuando se analiza severidad, los territorios con mayor tasa de mortalidad relativa fueron:

Magdalena: 12.82%
Guainía: 8.44%
Santa Marta D.E.: 5.85%
Atlántico: 5.78%
Chocó: 5.56%

Por grupos de edad, la diferencia fue contundente:

60+: 14.22%
45-59: 1.75%
30-44: 0.44%
18-29: 0.24%
0-17: 0.08%

La principal prioridad poblacional fue claramente el grupo de 60 años o más.

8.2 Filtro Antioquia – Medellín y Bello

En el filtro local, la comparación territorial ya no es útil porque solo queda Antioquia:

Antioquia: 0.92%

Pero por grupo de edad se mantiene el hallazgo clave:

60+: 8.65%
45-59: 0.25%
30-44: 0.13%
0-17: 0%
18-29: 0%
8.3 Lectura comparativa

La conclusión central no cambia: el grupo de 60+ es la población de mayor severidad tanto en el panorama general como en el filtro local. Lo que sí cambia es la utilidad del análisis territorial: en el agregado permite comparar regiones; en el filtro local, la prioridad debe definirse más por población que por territorio.

9. Oportunidad diagnóstica
9.1 Panorama general sin filtro

El tiempo entre inicio de síntomas y diagnóstico se ubicó alrededor de 10 días. Por grupo de edad:

45-59: 10.29 días
30-44: 9.99
60+: 9.88
18-29: 9.87
0-17: 9.84

Los territorios con mayores demoras promedio fueron:

Guainía: 16.33 días
Putumayo: 14.61
Vichada: 14.00
Meta: 13.94
Amazonas: 13.78
9.2 Filtro Antioquia – Medellín y Bello

En el filtro local, el promedio fue también cercano a 10 días:

45-59: 10.21
60+: 9.89
30-44: 9.83
18-29: 9.63
0-17: 8.96

A nivel territorial solo quedó:

Antioquia: 9.79 días
9.3 Lectura comparativa

El tiempo diagnóstico del filtro local es consistente con el promedio general y no parece especialmente crítico frente al agregado. La diferencia importante es que el análisis general sí permite detectar territorios con demoras mucho más altas, mientras que en el filtro local no hay posibilidad de comparación.

10. Origen del contagio y ubicación del caso
10.1 Panorama general sin filtro

En el análisis agregado, la fuente de contagio fue principalmente:

Comunitaria: 78%
Relacionado: 22%
Importado: 0.025%

La ubicación del caso fue:

Casa: 96.6%
Fallecido: 2.79%
Sin dato: 0.61%
10.2 Filtro Antioquia – Medellín y Bello

En el filtro local:

Comunitaria: 72.8%
Relacionado: 27.1%
Importado: 0.046%

Ubicación del caso:

Casa: 98.7%
Fallecido: 0.92%
Sin dato: 0.414%
10.3 Lectura comparativa

En ambos niveles, la estructura es esencialmente la misma:

el contagio es principalmente comunitario,
los casos importados son marginales,
y la categoría dominante de ubicación es casa.

La diferencia es que en el filtro local la proporción de casos en casa es aún mayor, y la participación de fallecido es menor.

11. Conclusiones generales

El análisis integrado permite concluir que el fenómeno presentó una fase crítica bien definida en el segundo semestre de 2020, con una fuerte concentración temporal tanto en el panorama general como en el filtro de Antioquia, Medellín y Bello.

A nivel territorial, el análisis global muestra que la carga de casos se concentró en pocos territorios, liderados por Bogotá, Antioquia y Valle. Dentro de Antioquia, la mayor parte de los casos del filtro se concentra de forma marcada en Medellín.

Desde el punto de vista demográfico, el mayor volumen de casos se concentra en los grupos de 30-44 y 18-29 años, pero la mayor severidad recae con claridad sobre la población de 60 años o más. Esta es probablemente la conclusión más importante del informe: quien más casos concentra no es quien enfrenta mayor riesgo de muerte.

En cuanto al sexo, las diferencias existen, pero son más leves en el volumen total que en los fallecimientos. La participación masculina es ligeramente superior en ambos casos, aunque la brecha es más fuerte en el análisis general que en el filtro local.

La relación entre volumen de casos y mortalidad es positiva en ambos niveles de análisis, pero no perfectamente lineal. La mortalidad acompaña los períodos de mayor incidencia, aunque no siempre replica exactamente el mismo patrón mensual.

Finalmente, el tiempo a diagnóstico se ubica cerca de los 10 días tanto en el agregado como en el filtro local, con mayores diferencias territoriales en el panorama general que en el análisis específico de Antioquia.

12. Recomendaciones

Primero, conviene focalizar las estrategias de prevención y seguimiento intensivo en la población de 60 años o más, ya que es el grupo de mayor severidad tanto en el agregado como en el análisis territorial.

Segundo, las acciones de gestión territorial deberían diferenciar entre priorización por volumen y priorización por severidad. Si el objetivo es contener cantidad de casos, los focos son territorios y ciudades de alto volumen. Si el objetivo es reducir fallecimientos, la atención debe desplazarse a territorios con mayor mortalidad relativa y a poblaciones más vulnerables.

Tercero, Medellín debe entenderse como el principal foco dentro del filtro de Antioquia, por lo que cualquier estrategia local orientada a impacto debe considerar su peso dominante frente a Bello.

Cuarto, aunque el tiempo promedio a diagnóstico no muestra brechas graves en Antioquia, el panorama general sí evidencia territorios con demoras importantes. Eso sugiere que el sistema requiere estrategias diferenciadas según condiciones territoriales.

Quinto, las visualizaciones de pronóstico deben interpretarse con cautela, ya que las bandas de confianza observadas son amplias y no permiten sostener conclusiones deterministas sobre el comportamiento futuro.

Cierre

En síntesis, el análisis muestra un comportamiento consistente entre el panorama general y el filtro de Antioquia, Medellín y Bello: concentración temporal en 2020, predominio de transmisión comunitaria, mayor volumen en adultos de 30-44 y 18-29 años, y mayor severidad en 60+. El valor del filtro específico está en aterrizar la lectura general a un territorio concreto, donde Medellín emerge como el principal foco local y donde la prioridad más clara sigue siendo la protección de la población adulta mayor.

## Autor

Proyecto academico/practico de visualizacion y analisis de datos con Streamlit, MongoDB Atlas, Docker y Render.
