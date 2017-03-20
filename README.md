# English pronunciation evaluation system

This is a pronunciation evaluation system based on Kaldi.
To make it sucessfully run, it is necessary to download Kaldi from here: https://github.com/kaldi-asr/kaldi.git

The folders or scripts listed below in this repo also originate from kaldi/egs/wsj/s5(https://github.com/kaldi-asr/kaldi/tree/master/egs/wsj/s5).
* local
* steps
* utils
* path.sh
* cmd.sh

# How to use
1. Edit the 1st line of path.sh such that your Kaldi directory is assigned to $KALDI_ROOT
2. Run plot_closest.sh    (e.g. . plot_closest.sh \<output-dir\> \<lattice-dir\> \<decoder-type\> \<nbest-order\>)
3. Check the plotted image under \<output-dir\>/Nbest/plot


