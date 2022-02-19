FROM python:3.8

ENV APP_HOME /app

WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y tzdata libgdal-dev
RUN pip install --upgrade pip
RUN pip install numpy matplotlib tqdm
RUN pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

COPY ./app/ /app

CMD ["python", "/app/merge_dems.py", "-o", "/output", "/input"]
