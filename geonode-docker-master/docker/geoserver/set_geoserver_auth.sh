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
echo -e "OAUTH2_API_KEY=$OAUTH2_API_KEY\n"
echo -e "OAUTH2_CLIENT_ID=$OAUTH2_CLIENT_ID\n"
echo -e "OAUTH2_CLIENT_SECRET=$OAUTH2_CLIENT_SECRET\n"
echo -e "GEOSERVER_LOCATION=$GEOSERVER_LOCATION\n"
echo -e "GEONODE_LOCATION=$GEONODE_LOCATION\n"
echo -e "GEONODE_GEODATABASE=$GEONODE_GEODATABASE\n"
echo -e "GEONODE_GEODATABASE_USER=$GEONODE_GEODATABASE_USER\n"
echo -e "GEONODE_GEODATABASE_PASSWORD=$GEONODE_GEODATABASE_PASSWORD\n"
echo -e "auth_conf_source=$auth_conf_source\n"
echo -e "auth_conf_target=$auth_conf_target\n"

# Elegance is the key -> adding an empty last line for Mr. “sed” to pick up
echo " " >> "$auth_conf_source"

cat "$auth_conf_source"

tagname=( ${@:3:7} )

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
        authApiKey)
            echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$OAUTH2_API_KEY'"
            newvalue=`echo -ne "$tagvalue" | sed -re "s@.*@$OAUTH2_API_KEY@"`;;
        cliendId)
            echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$OAUTH2_CLIENT_ID'"
            newvalue=`echo -ne "$tagvalue" | sed -re "s@.*@$OAUTH2_CLIENT_ID@"`;;
        clientSecret)
            echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$OAUTH2_CLIENT_SECRET'"
            newvalue=`echo -ne "$tagvalue" | sed -re "s@.*@$OAUTH2_CLIENT_SECRET@"`;;
        proxyBaseUrl | redirectUri | userAuthorizationUri | logoutUri )
            echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$GEOSERVER_LOCATION'"
            newvalue=`echo -ne "$tagvalue" | sed -re "s@^(https?://[^/]+)@${GEOSERVER_LOCATION%/}@"`;;
        baseUrl | accessTokenUri | checkTokenEndpointUrl )
            echo "DEBUG: Editing '$auth_conf_source' for tagname <$i> and replacing its value with '$GEONODE_LOCATION'"
            newvalue=`echo -ne "$tagvalue" | sed -re "s@^(https?://[^/]+)@${GEONODE_LOCATION%/}@"`;;
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
