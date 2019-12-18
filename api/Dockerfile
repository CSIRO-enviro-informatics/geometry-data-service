FROM python:3.7

RUN apt-get update && apt-get install -y libpq-dev python3-dev

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
#Temporary fix until https://github.com/RDFLib/pyLDAPI/issues/21 is fixed
#Manually install a fork of pyldapi
RUN pip install git+https://github.com/jyucsiro/pyLDAPI.git@fix-issue-21
EXPOSE 3000
CMD python ./app.py
