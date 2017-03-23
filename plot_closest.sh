#!/bin/bash
# Yeonjung Hong

. ./path.sh
chmod +x chunk_nbest.py
chmod +x plot_best.py


#### [USAGE] . plot_closest.sh <dir-to-store-all> <decoder-type> <nbest> 
#### e.g. . plot_closest.sh temper uniG 20 

# configuration
dir_name=$1
decoder_type=$2
nbest=$3



lat_dir="$dir_name"/am/decode
model="$dir_name"/am/final.mdl
graph_dir="$dir_name"/graph
maindir="$dir_name"/"$nbest"best

mkdir -p "$maindir"



#############################[1] decode the given wav files

# USAGE: . wav-to-lattice.sh <dir-output> <decoder-type>
. wav-to-lattice.sh "$dir_name" "$decoder_type"

#############################[2] get posterior probability from the created lattice (trans-id converted into phone-id)

# USAGE: . lattice-to-phone.sh <lattice-dir> <model> <post-dir-output>
. lattice-to-phone-post.sh "$lat_dir" "$model" "$maindir"/post

#############################[3] get n-best alignments (both with symbol and integer) from the created lattice

# USAGE: . lattice-to-nbest-ali.sh <lattice-dir> <model> <nbest-order> <graph-dir> <ali-dir-output>
. lattice-to-nbest-ali.sh "$lat_dir" "$model" "$nbest" "$graph_dir" "$maindir"/ali

#############################[5] align the n-best alignments with the reference (the answer) using edit distance (correct/subsitution/insertion/deletion)

# USAGE: . compare-to-ref.sh <ali-dir> <score-dir-output>
. compare-to-ref.sh "$maindir"/ali "$maindir"/edit_dist

#############################[6] get the confidence level from the alignment given the whole pocdsterior probability information

# USAGE: . nbest-ali-to-conf.sh <ali-dir> <post-dir> <conf-dir-output>
. nbest-ali-to-conf.sh "$maindir"/ali "$maindir"/post "$maindir"/conf

#############################[7] choose the alignment closest to the reference and save the plotted image

# USAGE: python plot_best.py <ali-dir> <conf-dir> <score-dir> <graph-dir>
python plot_best.py "$maindir"/ali "$maindir"/conf "$maindir"/edit_dist "$graph_dir"






