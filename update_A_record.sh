#!/bin/bash

# You have tu adjust theese values
cfAuthEmail="email@example.com"
cfAuthKey="10947107410saCLOUDFLAREanksdknaAPIasdalKEYde2ad" # found in cloudflare account settings
cfZone="yourdomain.com"
cfRecord="subdomain.yourdomain.com"

ip=$(curl -s http://ipv4.icanhazip.com)
ip_file="ip.txt"
id_file="cloudflare.ids"
log_file="cloudflare.log"

# LOGGER
log() {
	if [ "$1" ]; then
		echo "[$(date)] - $1" >> $log_file
	fi
}

# SCRIPT START
log "Check Initiated"

if [ -f $ip_file ]; then
	old_ip=$(cat $ip_file)
	if [ "$ip" == "$old_ip" ]; then
		log "IP has not changed"
		echo "IP has not changed."
		exit 0
	fi
fi

if [ -f $id_file ] && [ $(wc -l $id_file | cut -d " " -f 1) == 2 ]; then
	zone_identifier=$(head -1 $id_file)
	record_identifier=$(tail -1 $id_file)
else
	zone_identifier=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$cfZone" -H "X-Auth-Email: $cfAuthEmail" -H "X-Auth-Key: $cfAuthKey" -H "Content-Type: application/json" | sed 's/,/\n/g' | awk -F'"' '/id/{print $6}' | head -1)
	record_identifier=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$zone_identifier/dns_records?name=$cfRecord" -H "X-Auth-Email: $cfAuthEmail" -H "X-Auth-Key: $cfAuthKey" -H "Content-Type: application/json" | sed 's/,/\n/g' | awk -F'"' '/id/{print $6}' | head -1)
	[ ! -z ${zone_identifier} ] && echo "$zone_identifier" > $id_file
	[ ! -z ${record_identifier} ] && echo "$record_identifier" >> $id_file
fi

update=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$zone_identifier/dns_records/$record_identifier" -H "X-Auth-Email: $cfAuthEmail" -H "X-Auth-Key: $cfAuthKey" -H "Content-Type: application/json" --data "{\"id\":\"$zone_identifier\",\"type\":\"A\",\"name\":\"$cfRecord\",\"content\":\"$ip\"}")

if [[ -z ${update##*'"success":false'*} ]]; then
	message="API UPDATE FAILED. DUMPING RESULTS:\n$update"
	log "$message"
	echo -e "$message"
	exit 1 
else
	message="IP changed to: $ip"
	echo "$ip" > $ip_file
	log "$message"
	echo "$message"
fi

