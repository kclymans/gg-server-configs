#!/bin/sh
cd /7d2d

PARAMS=$@

CONFIGFILE=
while test $# -gt 0
do
        if [ `echo $1 | cut -c 1-12` = "-configfile=" ]; then
                CONFIGFILE=`echo $1 | cut -c 13-`
        fi
        shift
done

if [ "$CONFIGFILE" = "" ]; then
        echo "No config file specified. Call this script like this:"
        echo "  ./startserver.sh -configfile=serverconfig.xml"
        exit 1
else
        if [ -f "$CONFIGFILE" ]; then
                echo Using config file: $CONFIGFILE
        else
                echo "Specified config file $CONFIGFILE does not exist."
                exit 1
        fi
fi

export LD_LIBRARY_PATH=.
#export MALLOC_CHECK_=0


remote_config=https://raw.githubusercontent.com/kclymans/gg-server-configs/refs/heads/main/7d2d/serverconfig.xml
source "$HOME/.secrets"

# Define variables to check
vars=("SERVER_PASS")

# Loop through each variable to check if it is set and non-empty
for var in "${vars[@]}"; do
    if [[ ! -v $var ]]; then
        echo "$var is not set"
        exit 0
    elif [[ -z "${!var}" ]]; then
        echo "$var is set to the empty string"
        exit 0
    else
        echo "$var FOUND: ${!var}"
    fi
done

# Download the remote config and update placeholders in one sed command
curl -s -o "$CONFIGFILE" "$remote_config" && \
sed -i -e "s/SERVER_PASS/$SERVER_PASS/g" "$CONFIGFILE"

exec ./7DaysToDieServer.x86_64 -logfile /7d2d/7DaysToDieServer_Data/output_log__`date +%Y-%m-%d__%H-%M-%S`.txt -quit -batchmode -nographics -dedicated $PARAMS