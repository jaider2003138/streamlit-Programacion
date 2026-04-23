FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY proyecto_streamlit/requirements.txt ./proyecto_streamlit/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r proyecto_streamlit/requirements.txt

COPY . .

EXPOSE 8501

CMD ["sh", "-c", "streamlit run proyecto_streamlit/app.py --server.address 0.0.0.0 --server.port ${PORT:-8501}"]
