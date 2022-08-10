FROM python:3.7

COPY ./app ./app
COPY ./etl ./etl
COPY README.md .

ARG KAGGLE_USERNAME
ARG KAGGLE_KEY

ENV KAGGLE_USERNAME=$KAGGLE_USERNAME
ENV KAGGLE_KEY=$KAGGLE_KEY

RUN pip install -U pip
RUN pip install -r app/requirements.txt

WORKDIR /etl
RUN python etl.py

EXPOSE 5000
WORKDIR /app
CMD ["gunicorn", "-b", ":5000", "wsgi:server"]