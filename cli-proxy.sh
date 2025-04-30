#!/usr/bin/zsh

if test -f  "/usr/local/share/ca-certificates/burp_suite.crt"
then 
  echo "Burp Suite Certificate found"
else
  crt="notfound"
fi
if [ ! -z $crt ]
then
  if test -f "/home/$USER/Downloads/cacert.der"
  then 
    echo "Burp cert found, but not in correct format and/or directory"
    sudo openssl x509 -in ~/Downloads/cacert.der -inform DER -out /usr/local/share/ca-certificates/burp_suite.crt
    sudo update-ca-certificates
  else
    echo "Please go to http://burp/cert in your browser while proxied through BUrp and download the certificate."
    echo "Then re-run the script to add it to your cert store"
    exit
  fi
fi

if [ -z "$1" ]
then
  echo "usage = on for turning proxy on and off for turning proxy off"
elif  [ $1 = 'on' ]
then
  if [ ! -z $2 ]
  then
	echo "Turning Proxy On"
	  export HTTP_PROXY="http://127.0.0.1:"$2
	  export HTTPS_PROXY="http://127.0.0.1:"$2
	  echo "HTTP_PROXY Variable is:"
	  echo $HTTP_PROXY
	  echo "HTTPS_PROXY Variable is:"
	  echo $HTTPS_PROXY
  else
    echo "Turning Proxy On"
    export HTTP_PROXY="http://127.0.0.1:8080"
    export HTTPS_PROXY="http://127.0.0.1:8080"
    echo "HTTP_PROXY Variable is:"
    echo $HTTP_PROXY
    echo "HTTPS_PROXY Variable is:"
    echo $HTTPS_PROXY
  fi
elif [ $1 = 'off' ]
then
  echo "Turning Proxy Off"
  unset HTTP_PROXY
  unset HTTPS_PROXY
  echo "HTTP_PROXY Variable is:"
  echo $HTTP_PROXY
  echo "HTTPS_PROXY Variable is:"
  echo $HTTPS_PROXY
else
  echo "usage = on for turning proxy on and off for turning proxy off"
fi
