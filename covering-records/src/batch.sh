#!/bin/bash
# usage: batch.sh RESTARTS HOPS SEED "kind:target:n ..."
R=$1; H=$2; S=$3; shift 3
for spec in $@; do
  IFS=: read kind target n <<< "$spec"
  python3 search.py $kind $target $n --restarts $R --hops $H --seed $S 2>&1 | grep -v -i warn
done
