FROM ubuntu:16.04


RUN apt-get update -y && apt-get install -y \
 python3-pip \
 python3.5

WORKDIR /keyword-service-app

COPY . /keyword-service-app

RUN pip3 install -r requirements.txt

ENV LANG=C.UTF-8

ENTRYPOINT [ "python3" ]

CMD [ "app.py" ]  
