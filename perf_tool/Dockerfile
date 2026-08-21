FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py \
    PYTHONUNBUFFERED=1

EXPOSE 5001

CMD ["python", "app.py"]
