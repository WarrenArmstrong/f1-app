FROM python:3.7

COPY ./app .
COPY ./etl .
COPY README.md .

ARG KAGGLE_USERNAME
ARG KAGGLE_KEY

ENV KAGGLE_USERNAME=$KAGGLE_USERNAME
ENV KAGGLE_KEY=$KAGGLE_KEY

RUN pip install -U pip
RUN pip install -r requirements.txt

RUN python etl.py

EXPOSE 5000
CMD ["gunicorn", "-b", ":5000", "wsgi:server"]