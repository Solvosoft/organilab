# Use an official Python runtime as a parent image
FROM python:3.6.4-stretch
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /organilab/logs/
# Set the working directory to /app
WORKDIR /organilab
# Copy the current directory contents into the container at /app
ADD src /organilab
ADD requirements.txt /organilab

# Install any needed packages specified in requirements.txt
RUN apt-get update
RUN apt-get install -y  libxslt-dev libxml2-dev python3-setuptools python3-cffi libcairo2 libffi-dev libpq-dev

RUN pip install --trusted-host pypi.python.org --no-cache-dir -r requirements.txt
RUN pip install --trusted-host pypi.python.org --no-cache-dir gunicorn

RUN apt-get remove -y libxslt-dev libxml2-dev python3-setuptools python3-cffi libcairo2 libffi-dev libpq-dev
RUN apt-get -y autoremove
RUN apt-get -y clean

RUN python manage.py collectstatic --settings=organilab.settings

# EXPOSE port 8000 to allow communication to/from server
EXPOSE 80


