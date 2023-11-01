#!/bin/sh

# Inject ServerName and ServerAlias (if specified) into the Apache httpd configuration

APACHE_CONFIG="/etc/apache2/sites-available/000-default.conf"
if [ ! -z ${BAIKAL_SERVERNAME+x} ]
then
  sed -i "s/# InjectedServerName .*/ServerName $BAIKAL_SERVERNAME/g" $APACHE_CONFIG
fi

if [ ! -z ${BAIKAL_SERVERALIAS+x} ]
then
  sed -i "s/# InjectedServerAlias .*/ServerAlias $BAIKAL_SERVERALIAS/g" $APACHE_CONFIG
fi

if [ ! -z ${APACHE_AuthLDAPURL+x} ]
then
  sed -i "s|# InjectedAuthLDAPURL .*|AuthLDAPURL $APACHE_AuthLDAPURL|g" $APACHE_CONFIG
fi

if [ ! -z ${APACHE_AuthLDAPBindDN+x} ]
then
  sed -i "s/# InjectedAuthLDAPBindDN .*/AuthLDAPBindDN $APACHE_AuthLDAPBindDN/g" $APACHE_CONFIG
fi

if [ ! -z ${APACHE_AuthLDAPBindPassword+x} ]
then
  sed -i "s/# InjectedAuthLDAPBindPassword .*/AuthLDAPBindPassword $APACHE_AuthLDAPBindPassword/g" $APACHE_CONFIG
fi