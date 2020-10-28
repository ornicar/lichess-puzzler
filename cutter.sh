#!/bin/sh

FILE=$1
PARTS=$2
CHUNK_SIZE=100000

for i in $(seq 1 $PARTS); do
  START=$(((i - 1) * CHUNK_SIZE))
  END=$(((i) * CHUNK_SIZE))
  SEDR="${START},\$!d;${END}q"
  IFILE="$FILE.$CHUNK_SIZE.$i"
  echo "$SEDR > $IFILE"
  sed $SEDR $FILE > $IFILE
done
