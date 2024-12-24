FROM python:3.9-slim

WORKDIR /app

COPY ./config/requirements.txt ./config

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 8000

CMD ["python", "api/main.py"]
