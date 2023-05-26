FROM python:3.11

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    rm -rf /var/lib/apt/lists/*

ENV LANG fr_FR.UTF-8
ENV LC_ALL fr_FR.UTF-8

RUN pip3 install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock /app/

WORKDIR /app

RUN pipenv install --system --deploy --ignore-pipfile

COPY app /app

ENTRYPOINT [ "python3", "app.py" ]
