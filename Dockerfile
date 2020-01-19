FROM python:3.8 as deps

RUN pip install -U pip
RUN pip install pipenv

WORKDIR /app

COPY Pipfile* ./

RUN pipenv install --system

COPY . ./

CMD [ "python", "-u", "src/app.py" ]
