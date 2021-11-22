#!/bin/bash
curl --proxy http://localhost:4242 http://loripsum.net/api/100/short/headers -s >> /golem/output/output.txt
for i in {1..3}; do 
    curl --proxy http://localhost:4242 http://httpbin.org/uuid -H  "accept: application/json" -s | jq '.uuid' >> /golem/output/output.txt
done
echo "time measured run" >> /golem/output/output.txt
{ time curl http://httpbin.org/uuid -H  "accept: application/json" -s | jq '.uuid'  >> /golem/output/output.txt ; } 2>> /golem/output/output.txt
