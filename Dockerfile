# Start with a Python image.
FROM python:2.7-alpine

# Some stuff that everyone has been copy-pasting
# since the dawn of time.
ENV PYTHONUNBUFFERED 1

RUN apk update && apk upgrade && apk add gcc postgresql-dev musl-dev

RUN pip install PyGreSQL python-dateutil

ADD StatRestaurant /StatRestaurant

WORKDIR /StatRestaurant

EXPOSE 80

CMD ["/usr/bin/env", "python", "/StatRestaurant/webserver.py"]
