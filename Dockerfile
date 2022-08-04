FROM python:3.7
WORKDIR /app

RUN mkdir ./app
COPY ./app ./app
RUN pip install -U pip
RUN pip install -r ./app/requirements.txt


WORKDIR /app/app/etl
RUN python etl.py

EXPOSE 80
WORKDIR /app/app
CMD ["gunicorn", "-b", ":80", "wsgi:server"]