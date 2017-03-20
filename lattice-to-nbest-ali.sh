#!/bin/bash
# Yeonjung Hong

. ./path.sh

lat_dir=$1
model=$2
order=$3
graph_dir=$4
out_dir=$5

mkdir -p "$out_dir"/int/chunked
mkdir -p "$out_dir"/sym/chunked

lattice=$(ls "$lat_dir"/lat.all)

$KALDI_ROOT/src/latbin/lattice-to-nbest --n="$nbest" ark:"$lattice" ark:- | \
 $KALDI_ROOT/src/latbin/nbest-to-linear ark:- ark:- | \
 $KALDI_ROOT/src/bin/ali-to-phones --per-frame=true "$model" ark:- ark,t:"$out_dir"/int/all
$KALDI_ROOT/egs/wsj/s5/utils/int2sym.pl -f 2- "$graph_dir"/phones.txt "$out_dir"/int/all > "$out_dir"/sym/all

#############################[4] split the single n-best alignment file into separate n files
# USAGE: python chunk_nbest.py <nbest-ali-file> <chunked-nbest-dir>
python chunk_nbest.py "$out_dir"/int/all "$out_dir"/int/chunked
python chunk_nbest.py "$out_dir"/sym/all "$out_dir"/sym/chunked
