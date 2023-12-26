FROM python:3.10-alpine

WORKDIR app/

COPY . .

RUN python3 -m pip install --no-cache-dir --no-warn-script-location --upgrade pip && python3 -m pip install --no-cache-dir --no-warn-script-location --user -r requirements.txt