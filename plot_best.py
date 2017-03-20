# -*- coding: utf-8 -*-
# This script chooses among the nbest transcriptions based on best csid ratio and save the plot!
# Yeonjung Hong

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import re
import numpy as np
import glob
import os
import sys
import shutil


align_dir = sys.argv[1]
conf_path = sys.argv[2]
edit_dist_path = sys.argv[3]
graph_dir = sys.argv[4]

align_chunked_sym_path = align_dir + "/sym/chunked"
phones = graph_dir + "/phones.txt"
main_dir = os.path.split(align_dir)[0]
plot_dir = main_dir + "/plot"

try:
    if os.path.isfile(plot_dir):
        shutil.rmtree(plot_dir)
    os.makedirs(plot_dir)
except OSError, e:
    if e.errno != 17:
        raise
    pass


# read the texts and concatenate them
dist_list = glob.glob(edit_dist_path +'/*best_score')

all = pd.DataFrame()
for i in dist_list:
    with open(i) as txt:
        data = pd.read_csv(txt, sep=' ', header=None)
        data.columns = ['fileID', 'csid', 'c', 's', 'i', 'd']
        data['nbest'] = i
        all = all.append(data)
all.reset_index(drop=True)
all['score'] = all['c']/all.sum(axis=1)

result = []
for t in list(set(all['fileID'])):
    gp = all[all['fileID'] == t]
    best = gp[gp['score'] == gp['score'].max()].reset_index(drop=True)
    result.append(best)


closest = pd.concat(result)



####### the work done til now is to find the closest sequence to the reference among the given nbest lattice result
####### the work from now on is to find the corresponding alignments' posterior probability

# closest -> fileID -> nbest -> ali -> all.post

# get phone-ID mapping
with open(phones) as phone_list:
    phone_id = {"phone": [], "phoneID": []}
    for line in phone_list:
        tmp = line.split(' ')
        phone_id["phone"].append(tmp[0])
        phone_id["phoneID"].append(re.findall("\d+", tmp[1])[0])


# pattern for the posterior probability
pat2extract = (
    "(?<=\[\s).*?(?=\s\])").format()

# initialize the whole dictionary
hyp_closest_to_ref = {}

# match the closest and nbest
for i in list(set(closest['fileID'])): # for each fileID

    # get the order number among the nbest candidates
    order_num = ''.join(re.findall('\d+', os.path.basename(closest[closest['fileID'] == i]['nbest'][0])))

    # get the closest phone alignment for the given fileID
    with open(align_chunked_sym_path + '/' + order_num + 'best') as ali:
        for line in ali:
            if re.match(i, line):
                l = line.split(' '); l.pop()
                alignment = l[1:]

    # get confidence for the corresponding alignment
    with open(conf_path + '/' + order_num + 'best.conf') as conf:
        for line in conf:
            if re.match(i, line):
                l = re.findall(pat2extract, line)
                confidence = map(float, l[0].split(' '))

    # raise error if the length of the alignment and confidence do not match
    if len(alignment) != len(confidence):
        raise ValueError("The length of alignment and its confidence do not match..")

    # init the main dictionary
    phone_post = {}
    for phone in phone_id["phone"]:
        phone_post[phone] = []

    # stack the probability sequence
    for idx in range(len(alignment)):
        phone_post[alignment[idx]].append(confidence[idx])
        other_phone = [x for x in phone_post.keys() if x != alignment[idx]]
        [phone_post[x].append(float(0)) for x in other_phone]

    hyp_closest_to_ref[i] = phone_post

################################################# now start plotting!
    fig, ax = plt.subplots(figsize=(20,5))
    t = np.array(range(len(alignment)))
    p = 100 * np.array(confidence)
    line, = ax.plot(t, p, 'b-o')
    for m, txt in enumerate(alignment):
        ax.annotate(txt, (t[m], p[m]))
    plt.title(i)
    plt.ylabel('Posterior Probability')
    plt.grid(True)
    plt.ylim((0,100))
    # plt.xlim((0,43))
    # plt.show()

    fig.savefig(plot_dir + "/" + i+'.png')
    plt.close(fig)
