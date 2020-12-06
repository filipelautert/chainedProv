#!/bin/sh


cd ../executions-logs

for i in $(ls -hrt *CLIENT*); do 
	echo -n $i 
	grep finalized $i | awk -F " " '{ printf("%s;%s;%s;%s\n", $6, $8, $11, $14)}'
done
