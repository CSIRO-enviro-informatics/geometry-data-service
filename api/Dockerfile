FROM python:3.7

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install python3-psycopg2

RUN pip install -r requirements.txt
EXPOSE 3000
CMD python ./app.py
