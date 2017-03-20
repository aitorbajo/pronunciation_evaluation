#!/bin/bash
# Yeonjung Hong
. ./path.sh

ali_dir=$1
out_dir=$2

mkdir -p "$out_dir"

reference=$(ls input/*.txt)
arr=("$ali_dir"/sym/chunked/*) # symbolized alignment
for f in "${arr[@]}"; do
	fname="$(basename "$f")"
	echo "$out_dir"/"${fname%.*}"_score
	$KALDI_ROOT/src/bin/align-text --special-symbol="'***'" ark:"$reference" ark:"${f}" ark,t:- | utils/scoring/wer_per_utt_details.pl --special-symbol "'***'" --nooutput-hyp --nooutput-ref --nooutput-ops > "$out_dir"/"${fname%.*}"_score
done
