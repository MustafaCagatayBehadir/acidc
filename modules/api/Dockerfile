FROM python:3.10-slim

WORKDIR /api

COPY etc/requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY modules/api ./

ENTRYPOINT python main.py --nso_ip ${NSO_HOST} --port ${NSO_PORT} --username ${NSO_USERNAME} --password ${NSO_PASSWORD} --fabric ${NSO_FABRIC}