#!/bin/bash

m2sh load -config mongrel2.conf -db the.db 
m2sh start -db the.db -host localhost > log/mongrel.log 2>&1 &

mongod -f mongodb.conf > log/mongodb.log 2>&1 &

python caustic/server.py > log/caustic.log 2>&1 &
