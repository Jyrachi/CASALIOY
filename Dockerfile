FROM python:3.11

WORKDIR /srv
RUN git clone https://github.com/su77ungr/CASALIOY.git
WORKDIR CASALIOY

RUN pip3 install poetry
RUN python3 -m poetry config virtualenvs.create false
RUN python3 -m poetry install
COPY example.env .env
