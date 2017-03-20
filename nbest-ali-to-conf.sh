#!/bin/bash
# Yeonjung Hong
. ./path.sh


ali_dir=$1
post_dir=$2
out_dir=$3

mkdir -p "$out_dir"


for entry in "$ali_dir"/int/chunked/* # integer-coded alignment
do
	fname=$(basename "$entry")
	$KALDI_ROOT/src/bin/get-post-on-ali ark:"$post_dir"/phone.post ark:"$entry" ark,t:"$out_dir"/"$fname".conf
done
