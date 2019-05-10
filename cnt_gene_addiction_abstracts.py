#!/bin/env python3 
import os
import re
import time
from ratspub  import * 
## turn dictionary (synonyms) to regular expression

def gene_addiction_cnt(gene):
    q="\"(" + addiction.replace("|", "[tiab] OR ")  + ") AND (" + drug.replace("|", "[tiab] OR ", ) + ") AND (" + gene + ")\""
    count=os.popen('esearch -db pubmed  -query ' + q + ' | xtract -pattern ENTREZ_DIRECT -element Count ').read()
    return (count)

out=open("gene_addiction_cnt_result_part1.tab", "w+")

cnt=0
with open ("./ncbi_gene_symb_syno_txid9606_part1.txt", "r") as f:
    for line in f:
        line=re.sub(r"\)|\(|\[|\]|\*|\'","",line)
        (gene, synoms)=line.strip().split("\t")
        if (gene[0:3] != "LOC"):
            cnt+=1
            for syno in synoms.split("|"):
                if len(syno)>3:
                    gene+="|"+syno
            gene_q=gene.replace("|", " [tiab] OR ")
            gene_q+="[tiab]"
            count=gene_addiction_cnt(gene_q)
            if (len(count)==0):
                print("pause")
                time.sleep(10)
            print(gene+"\t"+count)
            out.write(gene+"\t"+count)

