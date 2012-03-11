#!/bin/bash

mkdir -p log

m2sh load -config mongrel2.conf
m2sh start -host localhost &

mongod -f mongodb.conf &

#python caustic/server.py > log/caustic.log 2>&1 &
