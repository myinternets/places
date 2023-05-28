FROM qdrant/qdrant

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt install -y  build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev

RUN wget https://www.python.org/ftp/python/3.11.3/Python-3.11.3.tgz
RUN tar -xzvf Python-3.11.3.tgz
RUN cd Python-3.11.3 && ./configure --enable-optimizations && make -j 2 && make altinstall
RUN pip3.11 install --upgrade pip
COPY . /app

WORKDIR /app

RUN pip3.11 install -r requirements.txt
RUN python3.11 setup.py develop

RUN pip3.11 install supervisor

WORKDIR /qdrant
RUN ["./qdrant"]

