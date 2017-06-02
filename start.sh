#!/bin/bash
NODE_DIR="/home/vagrant/node-v6.10.1-linux-x64"
PYTHON=/usr/local/bin/python3

if [ -d $NODE_DIR ]; then
    PATH=$NODE_DIR/bin:$PATH
    LD_LIBRARY_PATH=$NODE_DIR/lib:$LD_LIBRARY_PATH
fi

if [ ! -d "CVT/assets/bundles" ]; then
	mkdir CVT/assets/bundles
else
	rm CVT/assets/bundles/*
fi

function check_err() {
	if [ "$?" -ne "0" ]; then
		echo $?
		exit 1
	fi
}

echo "checking npm packages..."
npm install --save && check_err
echo "running webpack..."
node_modules/.bin/webpack --config CVT/CVT/webpack.config.js
check_err
cd CVT
echo "running django migrations..."
$PYTHON manage.py makemigrations main
check_err
$PYTHON manage.py migrate
check_err
nohup redis-server &
nohup sudo $PYTHON manage.py runserver 0.0.0.0:8000 &
nohup /usr/local/bin/celery -A CVT beat -l debug&
nohup /usr/local/bin/celery -A CVT worker -l debug

