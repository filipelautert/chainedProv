#!/bin/sh

MODES="F"
#MODES="S C D"
ROUNDS="0"
#ROUNDS="0 1 2 3 4 5 6 7 8 9"

LIST_EXECUTIONS="10"
#LIST_EXECUTIONS="1000"
LIST_THREADS="1"
#LIST_THREADS="1 20 40"


#clear environment
kill -9 $(ps -C python3 -o pid=)
docker kill $(docker ps -q)
./Tendermint/finaliza_cluster.sh
sleep 2


for ROUND in $ROUNDS; do

	echo "**********************"
	echo "**********************"
	echo "**********************"
	echo "**********************"
	echo "**********************"
	echo "**********************"
	echo "Iniciando round $ROUND"
	echo "**********************"
	echo "**********************"
	echo "**********************"
	echo "**********************"
	echo "**********************"

	for MODE in $MODES; do
		for EXECUTIONS in $LIST_EXECUTIONS; do 
			for THREADS in $LIST_THREADS; do 

				if test $MODE = 'S'; then 
					BACKEND=BC
					./Tendermint/inicia_single.sh
				elif test $MODE = 'C'; then
					BACKEND=BC
					./Tendermint/inicia_cluster.sh
				elif test $MODE = 'F'; then
					BACKEND=FOG
					./Tendermint/inicia_cluster.sh
					./Tendermint/inicia_single_fog.sh
				else
					BACKEND=BD
				fi

				echo "Starting mode $MODE with $EXECUTIONS executions and $THREADS threads"

				python3 app.py -s $BACKEND -m $MODE -e $EXECUTIONS -t $THREADS &
				sleep 120 # dá tempo de tudo subir e baixar o load

				python3 simple_client.py -e $EXECUTIONS  -t $THREADS -m $MODE -s $BACKEND
				sleep 5
				kill -9 $(ps -C python3 -o pid=)
				sleep 5

				if test $MODE = 'S'; then 
					docker kill $(docker ps -q)
				elif test $MODE = 'C'; then
					./Tendermint/finaliza_cluster.sh
				elif test $MODE = 'F'; then
					./Tendermint/finaliza_cluster.sh
					sleep 3
					docker kill $(docker ps -q)
				fi

				echo "Done!"
			done
		done
	done

done
