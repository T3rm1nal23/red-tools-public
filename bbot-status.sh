#!/usr/bin/zsh
oldcount=0
olddatetime=0
while true
  do count=`cat output.txt|grep -E "VULNERABILITY|EMAIL_ADDRESS|PASSWORD|USERNAME|HASHED_PASSWORD|FINDING" |grep -Evi "Spoofed host header \(standard|nameserver-fingerprint|txt-finger|tls-sni-proxy|missing-sri|external-service|security-headers|Hijack|saas-service|tls-version|wildcard-tl|httponly-cookie|caa-fingerprint|ssl-dns-names|ssl-issuer|request-based.*\[dns|waf-detect|s3-detect|aws-detect|tech-detect" |wc -l`
  datetime=$(date +"%M")
  if [[ "$((datetime % 5))" -eq 0  && "$datetime" -ne "$olddatetime" ]]
  then
    echo "\nProgress:"
    cat debug.log|grep bbot.scanner|tail -n2
    cat debug.log|grep -i "modules running"|tail -n1
    cat scan.log|grep Request|tail -n1
    olddatetime=$datetime
  fi
  if [[ $count -ne $oldcount ]] 
  then 
    unprinted=$((count - oldcount))
    echo "\nNew Findings:\n"
    cat output.txt | grep -E "VULNERABILITY|EMAIL_ADDRESS|PASSWORD|USERNAME|HASHED_PASSWORD|FINDING" | \
      grep -Evi "Spoofed host header \(standard|nameserver-fingerprint|txt-finger|tls-sni-proxy|missing-sri|external-service|security-headers|Hijack|saas-service|tls-version|wildcard-tl|httponly-cookie|caa-fingerprint|ssl-dns-names|ssl-issuer|request-based.*\[dns|waf-detect|s3-detect|aws-detect|tech-detect" | \
      tail -n $unprinted | \
      awk '{
        gsub(/FINDING/, "\033[01;33m&\033[00m");
        gsub(/VULNERABILITY/, "\033[01;31m&\033[00m");
        print
  }'

#    cat output.txt|grep -E "VULNERABILITY|EMAIL_ADDRESS|PASSWORD|USERNAME|HASHED_PASSWORD|FINDING"|grep -Evi "Spoofed host header \(standard|nameserver-fingerprint|txt-finger|tls-sni-proxy|missing-sri|external-service|security-headers|Hijack|saas-service|tls-version|wildcard-tl|httponly-cookie|caa-fingerprint|ssl-dns-names|ssl-issuer|request-based.*\[dns|waf-detect|s3-detect|aws-detect|tech-detect" |tail -n $unprinted |sed -e 's/VULNERABILITY/^[[01;31mVULNERABILITY^[[00m/g' -e 's/FINDING/^[[01;33mFINDING^[[00m/g'
    echo ""
    oldcount=$count
  fi
  sleep 10
done
