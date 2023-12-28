FROM python:3.10-slim-bullseye

#Specify the directory
WORKDIR /app

#Copy the location to the same place it already is
COPY . /app

#Install libraries
RUN pip install -r requirements.txt

CMD ["python", "__main__.py"]
