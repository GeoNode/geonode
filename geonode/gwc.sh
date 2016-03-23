#!/bin/bash
#
##############################################################################
# Script for GeoWeb Cache seeding, truncate.
# can be used to post seeding and truncate requests, with parameters
#
# examples:
#  # seed all world extend for 4326 for levels 5 to 6
# ./gwc.sh seed topp:states epsg:4326 -b -180 -90 180 90 -zs 5 -ze 6
#  # seed all with TIME parameter
# ./gwc.sh seed topp:states epsg:4326 -p TIME 2001-12-12T18:00:00.0Z
#
################################################################################
#
# author: Lorenzo Natali - lorenzo.natali@geo-solutions.it
# Copyright 2015, GeoSolutions Sas.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#
##############################################################################

##############################################################################
### CONSTANTS
##############################################################################
REST_PATH_SEED="/seed/"
REST_PATH_MASSTRUNCATE="/masstruncate"
CURL='curl'
CURL_ARGS=" -s "


##############################################################################
### VARIABLES,CONFIGURATION,DEFAULT VALUES
##############################################################################
URL="http://192.168.56.101:8080/geoserver/gwc/rest"
user="admin"
password="geoserver"
format="image/png8"
zoomStart="10"
zoomStop="15"
threadCount=01
verbose=

# Post initialization
auth="${user}:${password}"

##############################################################################
### METHODS
##############################################################################
usage()
{
cat << EOF
usage: $0 <type> <layerName> <gridsetName> [options]
usage: $0 masstruncate <layerName> [options]
 - type :The Operation Type. One of "seed"," reseed","truncate"," masstruncate"
 - layerName :The name of the layer
 - gridsetName: the name of the gridSet (mandatory,except for masstruncate type)
 e.g. $0 seed layer epsg:4326
This script launch seeding and truncate tasks for GeoWebCache

OPTIONS:
   -a  | --auth        : Administrator credentials (user:password)
   -b  | --bounds      : the bounds in this format: -b minX minY maxX maxY
   -f  | --format      : format (default image/png8)
   -p  | --parameter   : -p name value (allow multiple values)
   -t  | --threadCount : default 01
   -zs | --zoomStart   : lower zoom level to seed/truncate (default 00)
   -ze | --zoomEnd     : greater zoom level to seed/truncate (default 04)
   -v  | --verbose     : show debug messages
   -u  | --url         : GWC rest url
   -h  | --help        : display this message
EOF
}
##############################################
# function getBody
# sets the body for seed,truncate,reseed.
##############################################
getBody()
{
    ### PARSE PARAMETERS
    if [ "$verbose" ];
        then
        echo "parameters:"
        echo $PARAMETERS_KEYS
        echo $PARAMETERS_VALUES
    fi

    PARAMETERS=
    for ((i=0;i<${#PARAMETERS_KEYS[@]};++i)); do
        PARAMETERS="${PARAMETERS}
        <entry>
          <string>${PARAMETERS_KEYS[i]}</string>
	  <string><![CDATA[${PARAMETERS_VALUES[i]}]]></string>
        </entry>"
    done

    if [ "$PARAMETERS" ] ;
    then
        PARAMETERS="<parameters>${PARAMETERS}</parameters>"
    fi

    #cat >TEMP_FILE ""
    REQUEST_BODY="
    <seedRequest>
      <name>${layer}</name>
      <type>${type}</type>
      <gridSetId>${gridSetId}</gridSetId>
       ${BOUNDS}
       ${ZOOMSTART}
       ${ZOOMSTOP}
      <format>${format}</format>
      <threadCount>${threadCount}</threadCount>
      ${PARAMETERS}
    </seedRequest>
    "
}
##############################################
# FUNCTION getMassTruncateBody
# sets the body for masstruncate requests
##############################################
getMassTruncateBody(){
    REQUEST_BODY="<truncateLayer><layerName>${layer}</layerName></truncateLayer>"
}
##############################################
# FUNCTION getMassTruncateUrl
# sets the url for masstruncate requests
##############################################
getMassTruncateUrl(){
    url="$URL$REST_PATH_MASSTRUNCATE"
}
##############################################
# FUNCTION getMassTruncateUrl
# sets the url for seed,reseed truncate requests
##############################################
getUrl(){
    url="${URL}${REST_PATH_SEED}${layer}.xml"

}
# FUNCTION getCurlOptions
# sets the curl options
##############################################
getCurlOptions(){
    if [ "$verbose" ];
    then
        CURL_ARGS="$CURL_ARGS -v "
    else
        CURL_ARGS="$CURL_ARGS"
    fi

}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##############################################################################
## SCRIPT START
##############################################################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

##############################################################################
## Read Options
##############################################################################
#Set auth argument to override

#First of all, read mandatory arguments
#seed,reseed,truncate,masstruncate
type=$1
#e.g. met9:airmass
layer=$2

#if type masstruncate the third argument is not required, so minArg is
# set properly to shift the arguments and check the argument number validity
if [ "$type" = "masstruncate" ];
    then
    minArg=2
  else
     minArg=3
fi

if [ "$#" -lt $minArg ]; then
    echo "Illegal number of parameters"
    usage
    exit
fi

#Check operation type allowed
if [ "$type" != "seed" ] && [ "$type" != "reseed" ] && [ "$type" != "truncate" ] && [ "$type" != "masstruncate" ]; then
     echo "Operation Unknown : $type"
    usage
    exit
fi

###############################
## Read Additional Agrguments
###############################
gridSetId=$3
shift $minArg
while :
do
    case "$1" in
	  -a | --auth)
	       auth=$2
	       shift 2
	  ;;
      -b | --bounds)
        minX=$2
        minY=$3
        maxX=$4
        maxY=$5
	    BOUNDS="<bounds>
        <coords>
          <double>${minX}</double>
          <double>${minY}</double>
          <double>${maxX}</double>
          <double>${maxY}</double>
        </coords>
         </bounds>"
      shift 5
	  ;;

	  -h | --help)
	      usage  # Call your function
	      # no shifting needed here, we're done.
	      exit 0
	  ;;

	  -p | --parameter)
          PARAMETERS_KEYS+=("$2")
	      PARAMETERS_VALUES+=("$3")
	      shift 3
	  ;;

      -t | --threadCount)
	      threadCount="$2" # You may want to check validity of $2
	      shift 2
	  ;;

      -f | --format)
              format="$2" # You may want to check validity of $2
              shift 2
          ;;

      -u | --url)
	      URL="$2" # You may want to check validity of $2
	      shift 2
	  ;;

      -v | --verbose)
          #  It's better to assign a string, than a number like "verbose=1"
	      #  because if you're debugging script with "bash -x" code like this:
	      #    if [ "$verbose" ] ...
	      #  You will see:
	      #    if [ "verbose" ] ...
              #  Instead of cryptic
	      #    if [ "1" ] ...
	      #
	      verbose="verbose"
	      shift
	  ;;

	  -zs | --zoomStart)
	      zoomStart="$2" # You may want to check validity of $2
	      shift 2
	  ;;

	  -ze | --zoomStop)
	      zoomStop="$2" # You may want to check validity of $2
	      shift 2
	  ;;

      --) # End of all options
	  shift
	  break
	   ;;
      -*)
	  echo "Error: Unknown option: $1" >&2
	  exit 1
	  ;;
      *)  # No more options
	  break

    esac
done


#TODO remove maybe not neded
TEMP_FILE="temp_file_${RANDOM_NUMBER}"


###############################################
## Get Body and URL of REST REQUEST
###############################################

# default values setup
#RANDOM_NUMBER=$(( ( RANDOM % 1000 )  + 1 ))
ZOOMSTART="<zoomStart>${zoomStart}</zoomStart>"
ZOOMSTOP="<zoomStop>${zoomStop}</zoomStop>"


# Generate body depending on the request type
if [ "$type" = "masstruncate" ];
    then
    getMassTruncateBody
    getMassTruncateUrl
  else
    getBody
    getUrl
fi

if [ -n "$verbose" ];
    then
    echo "doing request to ${url}"
    echo "request body:"
    echo $REQUEST_BODY

fi

#Add options to CURL constants
getCurlOptions

#############
# REQUEST
#############
RESPONSE=$($CURL -u $auth -H "Content-type: text/xml" -H "Accept: text/xml" -XPOST $CURL_ARGS -i -d "$REQUEST_BODY" "$url" )

# Parse response
STATUS=$(echo $RESPONSE | grep HTTP/1.1 | tail -1 | awk {'print $2'})
STATUSTEXT=$(echo $RESPONSE | grep HTTP/1.1 | tail -1 | awk {'print $3'})


if [ -n "$verbose" ];
    then
    echo "Server Response ${url}"
    echo $RESPONSE
fi

if [ "$STATUS" != 200 ];
then
    >&2 echo "ERROR: Remote service \""$url"\" returned error. HTTP Status: $STATUS"
    exit 1

else
    echo "SUCCESS" #maybe no output on standard output?
    exit 0
fi
