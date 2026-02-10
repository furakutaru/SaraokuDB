FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn

COPY simple_app.py .

EXPOSE 8080

CMD ["python", "simple_app.py"]
