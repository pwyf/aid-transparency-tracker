#!/bin/bash

set -e

sudo echo "en_GB.UTF-8 UTF-8" >> /etc/locale.gen

sudo locale-gen


apt-get update
apt-get upgrade -y

apt-get install -y git python python-dev libxml2-dev libxslt1-dev libpq-dev sqlite rabbitmq-server python-pip xclip apache2 screen libapache2-mod-wsgi postgresql-10 uwsgi apache2 libapache2-mod-proxy-uwsgi uwsgi-plugin-python3 supervisor redis

pip install virtualenv

#adduser --quiet --disabled-password --shell /bin/bash --home /home/tracker tracker

echo "vagrant:pass" | chpasswd

# Set up the database

sudo su --login -c "psql -c \"CREATE USER vagrant WITH PASSWORD 'pass';\"" postgres
sudo su --login -c "psql -c \"CREATE DATABASE vagrant WITH OWNER vagrant ENCODING 'UTF8'  LC_COLLATE='en_GB.UTF-8' LC_CTYPE='en_GB.UTF-8'  TEMPLATE=template0 ;\"" postgres
sudo su --login -c "psql -c \"CREATE DATABASE impsched WITH OWNER vagrant ENCODING 'UTF8'  LC_COLLATE='en_GB.UTF-8' LC_CTYPE='en_GB.UTF-8'  TEMPLATE=template0 ;\"" postgres


cd /vagrant

#git clone --recursive --branch original-version https://github.com/pwyf/aid-transparency-tracker.git
#cd aid-transparency-tracker

virtualenv pyenv
echo "export FLASK_APP=iatidataquality/__init__.py" >> pyenv/bin/activate
source pyenv/bin/activate
pip install -r requirements.txt

cp vagrant/config.py .

mkdir dq dq/data dq/sample_work
mkdir impsched impsched/data impsched/data/temp impsched/data/xml

