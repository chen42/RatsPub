#!/bin/env python3 
import os
import re
import time
from ratspub  import *

def gene_addiction_cnt(gene):
    q="\"(" + addiction.replace("|", "[tiab] OR ")  + ") AND (" + drug.replace("|", "[tiab] OR ", ) + ") AND (" + gene + ")\""
    count=os.popen('esearch -db pubmed  -query ' + q + ' | xtract -pattern ENTREZ_DIRECT -element Count ').read()
    if (len(count)==0):
        print("pause")
        time.sleep(15)
        return gene_addiction_cnt(gene)
    else:
        return (count)

out=open("gene_addiction_abstract_cnt_result.tab", "w+")

with open ("./ncbi_gene_symb_syno_name_txid9606.txt", "r") as f:
    for line in f:
        line=re.sub(r"\)|\(|\[|\]|\*|\'","",line.strip())
        if "\t" in line:
            (gene, synostring)=line.strip().split("\t")
            if "|" in synostring:
                synos=synostring.split("|") 
            elif len(synostring)>3:
                synos=synostring
            for syno in synos:
                if len(syno)>3:
                    gene+="|"+syno
        else:
            gene=line.strip()
        gene_q=gene.replace("|", " [tiab] OR ")
        gene_q+="[tiab]"
        count=gene_addiction_cnt(gene_q)
        print(gene+"\t"+count)
        out.write(gene+"\t"+count)
