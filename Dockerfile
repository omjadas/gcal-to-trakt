FROM python:3.12.5-alpine

RUN pip install -U pip
RUN pip install pipenv

WORKDIR /app

COPY Pipfile* ./

RUN pipenv install --system

COPY . ./

CMD [ "python", "-u", "-m", "src.app" ]
