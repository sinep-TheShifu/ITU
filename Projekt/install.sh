#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

apt-get install python3-pip -y

BIN=$(readlink "$0")
if [ "$BIN" = "" ]; then
       BIN="$0"
fi
DIR=$(pwd)
ROOT_HOME="/root"
TARGET_DIR="ShutdownToolServer"
TARGET_SERVICE="shutdown-tool-server.service"
mkdir -p "${ROOT_HOME}"/bin/"${TARGET_DIR}" || exit 1
cd "${ROOT_HOME}"/bin/"${TARGET_DIR}" || exit 1
cp -r "${DIR}"/main.py "${DIR}"/src "${DIR}"/LICENSE .
pip3 install -r src/requirements.txt || exit 1

SERVICE="
[Unit]
Description=ShutdownToolServer
After=multi-user.target

[Service]
Type=simple
WorkingDirectory=${ROOT_HOME}/bin/${TARGET_DIR}
ExecStart=/usr/bin/python3 main.py 0.0.0.0:60606 -no-debug
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
"

touch /etc/systemd/system/${TARGET_SERVICE} || exit 1
echo "${SERVICE}" > /etc/systemd/system/${TARGET_SERVICE}

systemctl daemon-reload
systemctl enable ${TARGET_SERVICE}
systemctl start ${TARGET_SERVICE}
