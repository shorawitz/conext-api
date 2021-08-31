FROM ubuntu:20.04

RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install net-tools nginx python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
RUN pip3 install --upgrade pip
RUN pip3 install wheel uwsgi flask flask_restful supervisor pyModbusTCP

RUN rm -f /etc/nginx/fastcgi.conf /etc/nginx/fastcgi_params /etc/nginx/snippets/fastcgi-php.conf /etc/nginx/snippets/snakeoil.conf
COPY Docker/nginx_conf /etc/nginx/sites-available/default
COPY Docker/solarmonitor.ini /etc/uwsgi/solarmonitor.ini
COPY Docker/supervisord.conf /etc/supervisord.conf

RUN mkdir -p /opt/solarmonitor
RUN chown www-data:www-data /opt/solarmonitor
WORKDIR /opt/solarmonitor
COPY solarmonitor.py /opt/solarmonitor/solarmonitor.py
COPY Docker/uwsgi.py /opt/solarmonitor/uwsgi.py

#ENTRYPOINT nginx -g "daemon on;" && uwsgi --uid 101 --gid 101 --ini /opt/solarmonitor/solarmonitor.ini
ENTRYPOINT [ "/usr/local/bin/supervisord" ]
EXPOSE 80