
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -q -r priority_fee/requirements.txt -r alerting/requirements.txt -r scheduler/requirements.txt -r metrics_exporter/requirements.txt
CMD ["python","-c","print('solanabot container')"]
