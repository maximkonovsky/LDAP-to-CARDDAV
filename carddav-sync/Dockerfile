FROM python:3-alpine

RUN apk --no-cache add build-base openldap-dev python3-dev
RUN pip3 install ldap3 sqlalchemy requests vobject lxml mysql-connector-python
#python-ldap

#WORKDIR /carddav

COPY ./vcf /carddav/vcf/
COPY ./carddavutil /carddav/carddavutil/
COPY ./sync.py /carddav/

VOLUME [ "/carddav" ]

ENTRYPOINT [ "python3", "/carddav/sync.py"]