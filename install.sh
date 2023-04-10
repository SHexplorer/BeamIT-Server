#!/usr/bin/env bash

# BeamIT-Server
# Author: SHexplorer
# https://github.com/Software-Engineering-DHBW-TINF20IT2/BeamIT-Server

INSTALLDIR="/opt/BeamIT-Server"
USER="beamit"
PYTHON=$(which python3)
SERVICE="/etc/systemd/system/beamit-server.service"

DB_NAME="beamit_server"
DB_USER="beamit"
DB_USER_PASS="$(openssl rand -base64 32)"
DB_CONF_FILE="$INSTALLDIR/db.conf"

if [ "$VERBOSE" = "yes" ]; then set -x; STD=""; else STD="silent"; fi
silent() { "$@" > /dev/null 2>&1; }
YW=$(echo "\033[33m")
RD=$(echo "\033[01;31m")
BL=$(echo "\033[36m")
GN=$(echo "\033[1;92m")
CL=$(echo "\033[m")
CM="${GN}✓${CL}"
CROSS="${RD}✗${CL}"
BFR="\\r\\033[K"


function header_info {
clear
cat <<"EOF"

 ███████████                                     █████ ███████████
░░███░░░░░███                                   ░░███ ░█░░░███░░░█
 ░███    ░███  ██████   ██████   █████████████   ░███ ░   ░███  ░ 
 ░██████████  ███░░███ ░░░░░███ ░░███░░███░░███  ░███     ░███    
 ░███░░░░░███░███████   ███████  ░███ ░███ ░███  ░███     ░███    
 ░███    ░███░███░░░   ███░░███  ░███ ░███ ░███  ░███     ░███    
 ███████████ ░░██████ ░░████████ █████░███ █████ █████    █████   
░░░░░░░░░░░   ░░░░░░   ░░░░░░░░ ░░░░░ ░░░ ░░░░░ ░░░░░    ░░░░░                     

---------------------------------------------------------------------


EOF
}

function msg_info() {
  local msg="$1"
  echo -ne " ${HOLD} ${YW}${msg}...\n"
}

function msg_ok() {
  local msg="$1"
  #echo -e "${BFR} ${CM} ${GN}${msg}${CL}"
  echo -e "${CM} ${GN}${msg}${CL}\n"
}

function msg_error() {
  local msg="$1"
  #echo -e "${BFR} ${CROSS} ${RD}${msg}${CL}"
  echo -e "${CROSS} ${RD}${msg}${CL}\n"
}

function check_root() {
  if [ "$EUID" -ne 0 ]; then
    msg_error "Please run as root"
    exit
  fi
}

function check_python_version() {
  if [ $(python3 -V 2>&1 | sed 's/.* \([0-9]\).\([0-9]\)\([0-9]\)*./\1\2\3/') -lt 3100 ]; then
    msg_error "Python version must be 3.10 or higher!"
    exit
  fi
}

function check_Install_Folder() {
    if [ -d "$INSTALLDIR" ]; then
      msg_error "Install-Folder $INSTALLDIR already exist, aborting"
      exit
    fi
}

create_user() {
  useradd --system --no-create-home $USER
}

copy_files() {
  if [ -f "./databaseconnector.py" ]; then
    mkdir $INSTALLDIR
    cp databaseconnector.py datahandler.py logutil.py main.py pwcrypt.py README.md run.py $INSTALLDIR
    mkdir $INSTALLDIR/SharedDataFiles
    chown -R beamit:beamit $INSTALLDIR
    chmod -R 755 $INSTALLDIR
    chmod -R 700 $INSTALLDIR/SharedDataFiles
  else
    msg_error "BeamIT-Server not locally found, aborting."
    exit
  fi
}

create_service() {
cat <<EOF > $SERVICE
[Unit]
Description=BeamIT Server
After=network.target

[Service]
WorkingDirectory=$INSTALLDIR
ExecStart=$PYTHON ./run.py
Type=simple
Restart=always
User=beamit
Group=beamit

[Install]
WantedBy=default.target
RequiredBy=network.target
EOF

  chmod 664 $SERVICE
  systemctl daemon-reload
}

setup_database() {
  $STD su postgres <<EOF
psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_USER_PASS';"
psql -c "CREATE DATABASE $DB_NAME WITH ENCODING 'UTF8' OWNER = $DB_USER;"
EOF

  cat <<EOF > $DB_CONF_FILE
[DBCONFIG]
name = $DB_NAME
user = $DB_USER
password = $DB_USER_PASS
EOF
  
  chown beamit:beamit $DB_CONF_FILE
  chmod 700 $DB_CONF_FILE
}

header_info

check_root

msg_info "Updating software repositorys"
$STD apt update

msg_info "Checking compability"
$STD apt install -y python3
check_python_version


msg_info "Installing Dependencies"

$STD apt install -y wget
$STD apt install -y postgresql
$STD apt install -y libpq-dev
$STD apt install -y python3
$STD apt install -y python3-pip

$STD pip3 install fastapi
$STD pip3 install uvicorn
$STD pip3 install psycopg2
$STD pip3 install python-multipart


msg_info "Installing BeamIT-Server"
echo ""

check_Install_Folder
msg_info "Creating User"
create_user

msg_info "Copying files"
copy_files

msg_info "Creating service"
create_service

msg_info "Creating database with user"
setup_database

msg_ok "Server installed. Start service with \"sudo systemctl start beamit-server.service\""
msg_ok "To run server on startup run \"sudo systemctl enable beamit-server.service\""
msg_ok "If you want to use https you have to put a .crt or .pem and .key x509 certificate in $INSTALLDIR. Make sure to restrict read permission only to beamit user"
