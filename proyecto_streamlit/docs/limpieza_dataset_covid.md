# Limpieza del Dataset COVID usado en la app

## Contexto
La app esta consumiendo el dataset de **casos positivos de COVID-19 en Colombia** desde la API configurada en `.env`:

```env
API_URL=https://www.datos.gov.co/resource/gt2j-8ykr.json
```

Al momento de esta limpieza, la coleccion `datos_api` en MongoDB contenia **500 registros**. La limpieza se implemento para que:

- se aplique antes de guardar nuevos datos en MongoDB
- tambien se aplique al leer datos ya existentes
- el dataset quede mas claro para filtros, tablas y graficas

## Como estaba antes de limpiar
La estructura original de los 500 registros tenia **21 columnas**:

- `fecha_reporte_web`
- `id_de_caso`
- `fecha_de_notificaci_n`
- `departamento`
- `departamento_nom`
- `ciudad_municipio`
- `ciudad_municipio_nom`
- `edad`
- `unidad_medida`
- `sexo`
- `fuente_tipo_contagio`
- `ubicacion`
- `estado`
- `recuperado`
- `fecha_inicio_sintomas`
- `fecha_diagnostico`
- `fecha_recuperado`
- `tipo_recuperacion`
- `per_etn_`
- `fecha_muerte`
- `nom_grupo_`

### Problemas detectados
1. **Nombres de columnas con mala codificacion**
   - `fecha_de_notificaci_n`
   - `per_etn_`
   - `nom_grupo_`

2. **Fechas guardadas como texto largo**
   - Ejemplo antes: `2020-12-24 00:00:00`
   - Eso hacia mas ruidosa la visualizacion y el filtrado temporal.

3. **Categorias poco amigables para leer**
   - `sexo` venia como `M` y `F`
   - `departamento_nom` y `ciudad_municipio_nom` venian en mayusculas completas

4. **Valores no informativos escritos como texto**
   - `N/A` aparecia en `estado`, `recuperado` y `ubicacion`
   - Eso fragmentaba categorias en graficas y tablas

5. **Campos identificadores tratados como numericos**
   - `id_de_caso`
   - `departamento`
   - `ciudad_municipio`
   - Estos campos no son medidas analiticas, son codigos

6. **Faltaban variables derivadas utiles para analisis epidemiologico**
   - grupo de edad
   - anio y mes de reporte
   - tiempos entre sintomas, diagnostico, recuperacion y muerte

## Muestra del estado original
Algunos conteos previos de la coleccion antes de limpiar:

### Sexo
- `M`: 276
- `F`: 224

### Estado
- `Leve`: 479
- `Fallecido`: 18
- `N/A`: 3

### Recuperado
- `Recuperado`: 479
- `Fallecido`: 18
- `N/A`: 3

### Ubicacion
- `Casa`: 479
- `Fallecido`: 18
- `N/A`: 3

### Departamento
- `BOGOTA`: 144
- `VALLE`: 120
- `ANTIOQUIA`: 61

### Ciudad
- `BOGOTA`: 144
- `CALI`: 117
- `MEDELLIN`: 34

## Como se limpio
La limpieza se implemento en [data_cleaning.py](C:/Users/user/Desktop/streamlit-main/proyecto_streamlit/data_cleaning.py) y se conecto al flujo de guardado y lectura en [mongo_db.py](C:/Users/user/Desktop/streamlit-main/proyecto_streamlit/mongo_db.py).

### Reglas aplicadas
1. **Renombrado de columnas**
   - `fecha_de_notificaci_n` -> `fecha_de_notificacion`
   - `per_etn_` -> `per_etnica`
   - `nom_grupo_` -> `grupo_poblacional`

2. **Normalizacion de valores de texto**
   - eliminacion de espacios dobles
   - recorte de espacios al inicio y final
   - conversion de categorias a formato mas legible

3. **Estandarizacion de sexo**
   - `M` -> `Masculino`
   - `F` -> `Femenino`

4. **Conversion de valores no informativos a nulos**
   - `N/A`
   - `NA`
   - `None`
   - `Null`
   - cadenas vacias

5. **Formateo de fechas**
   - antes: `2020-12-24 00:00:00`
   - despues: `2020-12-24`

6. **Tratamiento correcto de identificadores**
   - `id_de_caso`, `departamento` y `ciudad_municipio` se conservaron como identificadores, no como medidas numericas de analisis

7. **Creacion de variables derivadas**
   - `grupo_edad`
   - `anio_reporte`
   - `mes_reporte`
   - `anio_diagnostico`
   - `mes_diagnostico`
   - `dias_sintomas_a_diagnostico`
   - `dias_diagnostico_a_recuperacion`
   - `dias_diagnostico_a_muerte`

## Por que se limpio asi
La limpieza se hizo con cuatro objetivos:

1. **Mejorar la legibilidad de tablas y graficas**
   - `Bogota` es mas legible que `BOGOTA`
   - `Femenino` y `Masculino` son mas claros que `F` y `M`

2. **Evitar categorias basura**
   - `N/A` ahora pasa a nulo real, lo cual evita mezclar ausencia de dato con una categoria valida

3. **Facilitar el filtrado en Streamlit**
   - fechas mas limpias
   - categorias mas estables
   - menos ruido en multiselects

4. **Crear variables utiles para analisis**
   - grupos etarios
   - tiempos entre eventos del caso
   - agregacion temporal por anio y mes

## Como quedo despues de limpiar
Despues de limpiar, la coleccion sigue teniendo **500 registros**, pero ahora tiene **29 columnas**, porque se preservo la informacion original y se agregaron variables derivadas.

### Ejemplos de cambios visibles
#### Sexo
- antes: `M`, `F`
- despues: `Masculino`, `Femenino`

#### Estado
- antes: `Leve`, `Fallecido`, `N/A`
- despues: `Leve`, `Fallecido`, `null`

#### Ubicacion
- antes: `Casa`, `Fallecido`, `N/A`
- despues: `Casa`, `Fallecido`, `null`

#### Departamento
- antes: `BOGOTA`, `VALLE`, `ANTIOQUIA`
- despues: `Bogota`, `Valle`, `Antioquia`

#### Fecha
- antes: `2020-12-24 00:00:00`
- despues: `2020-12-24`

### Nuevas variables utiles
#### Grupo de edad
Distribucion principal:
- `30-44`: 176 casos
- el resto se reparte entre `0-17`, `18-29`, `45-59` y `60+`

#### Anio de reporte
- minimo: 2020
- maximo: 2022

#### Mes de reporte
- hay 11 meses distintos en la muestra
- el mes mas frecuente es `2020-07` con 124 registros

#### Dias entre sintomas y diagnostico
- validos: 486 casos
- promedio: 10.04 dias
- mediana aproximada: 11 dias

#### Dias entre diagnostico y recuperacion
- validos: 479 casos
- promedio: 21.78 dias

#### Dias entre diagnostico y muerte
- validos: 20 casos
- promedio: 8.85 dias

## Impacto en las graficas
Con esta limpieza, las visualizaciones quedan mejor porque:

- los nombres de columnas ya no salen dañados
- las categorias se ven mas limpias y profesionales
- los filtros muestran opciones entendibles
- las fechas son mas faciles de agrupar
- ya puedes analizar por grupo etario y por tiempos entre eventos

## Recomendacion de uso
Para este dataset COVID, las mejores graficas despues de la limpieza son:

- barras por `departamento_nom`
- barras por `ciudad_municipio_nom`
- barras o torta por `sexo`
- barras por `estado`
- barras por `fuente_tipo_contagio`
- lineas por `fecha_diagnostico`, `anio_reporte` o `mes_reporte`
- barras por `grupo_edad`
- histogramas o cajas de `edad`
- analisis de `dias_sintomas_a_diagnostico`

## Resultado final
La limpieza dejo el dataset mas util para analisis, mas consistente para filtros y mas claro para presentar hallazgos en el dashboard.
