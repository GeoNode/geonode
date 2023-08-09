#!/bin/bash

auth_conf_source="$1"
auth_conf_target="$2"
# Creating a temporary file for sed to write the changes to
temp_file="xml.tmp"
touch $temp_file

source /root/.bashrc
source /root/.override_env

test -z "$auth_conf_source" && echo "You must specify a source file" && exit 1
test -z "$auth_conf_target" && echo "You must specify a target conf directory" && exit 1

test ! -f "$auth_conf_source" && echo "Source $auth_conf_source does not exist or is not a file" && exit 1
test ! -d "$auth_conf_target" && echo "Target directory $auth_conf_target does not exist or is not a directory" && exit 1

# for debugging
echo -e "NGINX_BASE_URL=${NGINX_BASE_URL}\n"
if [ "$PUBLIC_PORT" == "443" ]; then
    SUBSTITUTION_URL="https://${DOCKER_HOST_IP}"
    if [ "$PUBLIC_PORT" != "443" ]; then
        SUBSTITUTION_URL="https://${DOCKER_HOST_IP}:${PUBLIC_PORT}"
    fi
else
    SUBSTITUTION_URL="http://${DOCKER_HOST_IP}"
    if [ "$PUBLIC_PORT" != "80" ]; then
        SUBSTITUTION_URL="http://${DOCKER_HOST_IP}:${PUBLIC_PORT}"
    fi
fi

echo -e "SUBSTITUTION_URL=$SUBSTITUTION_URL\n"
echo -e "auth_conf_source=$auth_conf_source\n"
echo -e "auth_conf_target=$auth_conf_target\n"

# Elegance is the key -> adding an empty last line for Mr. “sed” to pick up
echo " " >> "$auth_conf_source"

cat "$auth_conf_source"

tagname=( ${@:3:5} )

# for debugging
for i in "${tagname[@]}"
do
   echo "tagname=<$i>"
done

echo "DEBUG: Starting... [Ok]\n"

for i in "${tagname[@]}"
do
    echo "DEBUG: Working on '$auth_conf_source' for tagname <$i>"
    # Extracting the value from the <$tagname> element
    # echo -ne "<$i>$tagvalue</$i>" | xmlstarlet sel -t -m "//a" -v . -n
    tagvalue=`grep "<$i>.*<.$i>" "$auth_conf_source" | sed -e "s/^.*<$i/<$i/" | cut -f2 -d">"| cut -f1 -d"<"`

    echo "DEBUG: Found the current value for the element <$i> - '$tagvalue'"

    # Setting new substituted value
    case $i in
        proxyBaseUrl )
            if [ ${GEONODE_LB_HOST_IP} ]
            then
                echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$SUBSTITUTION_URL'"
                newvalue=`echo -ne "$tagvalue" | sed -re "s@http://localhost(:8.*0)@$SUBSTITUTION_URL@"`
            else
                echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$NGINX_BASE_URL'"
                newvalue=`echo -ne "$tagvalue" | sed -re "s@http://localhost(:8.*0)@$NGINX_BASE_URL@"`
            fi;;
        accessTokenUri | checkTokenEndpointUrl | baseUrl )
            echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$NGINX_BASE_URL'"
            newvalue=`echo -ne "$tagvalue" | sed -re "s@http://localhost(:8.*0)@$NGINX_BASE_URL@"`;;
        userAuthorizationUri | redirectUri | logoutUri )
            echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$SUBSTITUTION_URL'"
            newvalue=`echo -ne "$tagvalue" | sed -re "s@http://localhost(:8.*0)@$SUBSTITUTION_URL@"`;;
        *) echo -n "an unknown variable has been found";;
    esac

    echo "DEBUG: Found the new value for the element <$i> - '$newvalue'"
    # Replacing element’s value with $SUBSTITUTION_URL
    # echo -ne "<$i>$tagvalue</$i>" | xmlstarlet sel -t -m "//a" -v . -n
    sed -e "s@<$i>$tagvalue<\/$i>@<$i>$newvalue<\/$i>@g" "$auth_conf_source" > "$temp_file"
    cp "$temp_file" "$auth_conf_source"
done
# Writing our changes back to the original file ($auth_conf_source)
# no longer needed
# mv $temp_file $auth_conf_source

echo "DEBUG: Finished... [Ok] --- Final xml file is \n"
cat "$auth_conf_source"
