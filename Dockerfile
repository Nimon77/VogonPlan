FROM python:3.9

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG fr_FR.UTF-8
ENV LC_ALL fr_FR.UTF-8

COPY . /app

WORKDIR /app

RUN pip3 install --no-cache-dir --upgrade pip && \
	pip3 install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python3", "botv2.py" ]
