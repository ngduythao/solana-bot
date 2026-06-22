FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 9100
CMD ["bash","-lc","python -m uvicorn metrics_exporter.app:app --host 0.0.0.0 --port 9100"]
