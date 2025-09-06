#!/bin/bash
set -e
echo '[' > index.json
SEP=''
# list everything except .git and the index file itself
find . -type f ! -path "./.git/*" ! -name "index.json" | while read -r f; do
  sz=$(wc -c < "$f")
  mt=$(date -r "$f" -u +%FT%TZ 2>/dev/null || stat -c %y "$f" | sed 's/ /T/' | cut -d. -f1) 
  url="https://raw.githubusercontent.com/morsim8-hub/jenny-portal/main/${f#./}"
  sha=$(openssl dgst -sha256 "$f" | awk '{print $2}')
  echo "$SEP  {\"path\":\"$f\",\"url\":\"$url\",\"size\":$sz,\"modified\":\"$mt\",\"sha256\":\"$sha\"}" >> index.json
  SEP=','
done
echo ']' >> index.json
