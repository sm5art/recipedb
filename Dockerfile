FROM python:3.6

COPY . /recipedb
WORKDIR /recipedb
RUN pip install -r requirements.txt
