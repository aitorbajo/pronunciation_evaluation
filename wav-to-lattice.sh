#!/bin/bash
# Youngsun Cho, Yeonjung Hong
. ./path.sh || exit 1

dir_name=$1
decoder_type=$2

rm -rf "$dir_name"
mkdir -p "$dir_name"/wav 
mkdir "$dir_name"/data
mkdir "$dir_name"/am

# Model
cp -r model/am "$dir_name"/
cp -r model/"$decoder_type"/graph "$dir_name"/

# Input
cp input/*.wav "$dir_name"/wav/
# cp input/text tmp/data/

# 1) wavfile processing & wav.scp prep
touch "$dir_name"/data/wav.scp
touch "$dir_name"/data/utt2spk

cd "$dir_name"/wav
for wavfile in `ls *wav`;do

    sox ${wavfile} -r 16000 tmp.wav; # change sample rate to 16000
    mv tmp.wav ${wavfile}
    currdir=`pwd`
    uttname=`echo $wavfile | awk -F'.' {'print $1'}`
    spkname=`echo $uttname | awk -F'_' {'print $1'}`
    echo "$uttname" "$currdir"/"$wavfile" >> ../data/wav.scp
    echo "$uttname" "$spkname" >> ../data/utt2spk

done

../../utils/utt2spk_to_spk2utt.pl ../data/utt2spk > ../data/spk2utt

cd ../../

# 2) feature extraction
steps/make_mfcc.sh \
        --nj 1 \
        --mfcc-config conf/mfcc_hires.conf \
        --cmd "run.pl" \
        "$dir_name"/data \
        "$dir_name"/make_mfcc_hires \
        "$dir_name"/mfccdir_hires || exit 1;

    steps/compute_cmvn_stats.sh \
        "$dir_name"/data \
        "$dir_name"/make_mfcc_hires \
        "$dir_name"/mfccdir_hires || exit 1;


# 3) decode
    steps/decode_fmllr.sh \
    --nj 1 \
    --cmd "run.pl" \
    --skip_scoring "true"\
    "$dir_name"/graph \
    "$dir_name"/data \
    "$dir_name"/am/decode