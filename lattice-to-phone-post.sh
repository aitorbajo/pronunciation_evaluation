#!/bin/bash
# Yeonjung Hong
. ./path.sh

lat_dir=$1
model=$2
post_dir=$3

mkdir -p "$post_dir"

# unzip each lattice and concatenate them into a whole lattice
cat "$lat_dir"/lat.*.gz | gunzip -c > "$lat_dir"/lat.all

# extract phone posterior probability from the lattice
$KALDI_ROOT/src/latbin/lattice-to-post --acoustic-scale=0.1 ark:"$lat_dir"/lat.all ark:- | \
 $KALDI_ROOT/src/bin/post-to-phone-post "$model" ark:- ark,t:"$post_dir"/phone.post
