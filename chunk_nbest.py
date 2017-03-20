# -*- coding: utf-8 -*-
# 2017-March-17
# Yeonjung Hong

import pandas as pd
import os
import shutil
import sys

inputfile = sys.argv[1]
directory = sys.argv[2]

# inputfile = 'temper_ali'
# directory = 'temper_ali_ch_test'
''' This is the function for chunking a file which contains nbest alignments or transcriptions into separate files for each nth order'''


# check if the directory for the chunked files exist
try:
    if os.path.isfile(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
except OSError, e:
    if e.errno != 17:
        raise
    pass

# read the nbest file as data frame with 3 columns(fileID, nth order, sequence(alignments or transcriptions))
with open(inputfile) as nbest:
    data = pd.read_csv(nbest, sep='-', header=None)
    data.columns = ['fid', 'seq']
    seq = pd.DataFrame(data.seq.str.split(' ', 1).tolist(),
                  columns=['order', 'seq'])
    data = pd.concat([ data['fid'], seq ], axis=1)
    nbest.close()

# output text files for each nbest data
for i in list(set(data['order'])):
    fname = i + "best"
    cond = data['order'] == i
    subset = data[cond]
    # subset = pd.DataFrame.dropna(data.where(data['order'] == i ))
    l = [list(t) for t in zip(subset['fid'], subset['seq'])]
    line = [' '.join(t) for t in l]
    with open(directory+'/'+fname,'w') as f:
        f.write( "\n".join(line))
        f.close()

