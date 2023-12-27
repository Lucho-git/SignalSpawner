FROM python:3.10-slim-bullseye

#Specify the directory
WORKDIR /app

#Copy the location to the same place it already is
COPY . /app

#Install libraries
RUN pip install -r requirements.txt

# Install Supervisor
RUN apt-get update && apt-get install -y supervisor

# Copy the supervisord configuration file to the container
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
