FROM python:3.7

COPY ./app .

RUN pip install -U pip
RUN pip install -r requirements.txt

WORKDIR /etl
RUN python etl.py

EXPOSE 80
WORKDIR /
CMD ["gunicorn", "-b", ":80", "wsgi:server"]