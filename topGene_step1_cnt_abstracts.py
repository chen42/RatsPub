#!/bin/env python3 
import os
import sys
import re
import time
from ratspub_keywords import *

def undic(dic):
    return "|".join(dic.values())

def gene_addiction_cnt(gene):
    time.sleep(0.2)
    q="\'(\"" + addiction.replace("|", "\"[tiab] OR \"")  + "\") AND (\"" + drug.replace("|", "\"[tiab] OR \"", ) + "\") AND (\"" + gene + "\")\'"
    count=os.popen('esearch -db pubmed  -query ' + q + ' | xtract -pattern ENTREZ_DIRECT -element Count ').read()
    if (len(count)==0):
        print("pause")
        time.sleep(15)
        return gene_addiction_cnt(gene)
    else:
        return (count)

def removeStopWords(terms):
    out=str()
    for one in terms.upper().split("|"):
       if one not in stopWords:
            out+="|"+one
    return(out[1:])

def saveStopWord(w):
    with open (stopword_f,"a") as swf:
        swf.write(w+"\n")
    return


# either start with ncbi_gene_symb_syno_name_txid9606 for fresh new counts
# or recount the results after adding additional stopwords

if len(sys.argv)==2:
    input_f=sys.argv[1]
else:
    input_f="./ncbi_gene_symb_syno_name_txid9606.txt"
    input_f="./ncbi_gene_symb_syno_name_txid9606_p2.txt"

addiction=undic(addiction_d)
drug=undic(drug_d)
output_f=input_f.replace(".txt","_absCnt.txt")
out=open(output_f, "w+")

stopword_f="./stop_words_addiction_gene_search.txt"
with open (stopword_f, "r") as swf:
    stopWords=swf.read().upper().split("\n")
    swf.close()

with open (input_f, "r") as f:
    for line in f:
        rerun=0
        count=-1
        inputline=line
        if "'" in line:
            words=line.split("|")
            line=str()
            for word in words:
                # ' is used to mark/annotate a word is a stop word in the results
                if "'" in word:
                    word=word.replace("'","")
                    stopWords.append(word)
                    saveStopWord(word)
                    rerun=1
                # remove the ' mark 
                line+="|"+word
            line=line[1:]
        line=removeStopWords(line)
        # tab is added if there are abstracts counts
        if "\t" in line:
            (gene, count)=line.split("\t")
            if int(count)<100:
               rerun=1
        else:
            gene=line.strip()
        # remove synonyms with only two letters
        if "|" in gene:
            synos=gene.split("|")
            gene=str()
            for syno in synos:
                if len(syno)>2:
                    gene+="|"+syno
            gene=gene[1:]
        gene_q=gene.replace("|", "\"[tiab] OR \"")
        gene_q+="[tiab]"
        if rerun==1 or count== -1 :
            count=gene_addiction_cnt(gene_q)
        print("original line->\t"+inputline.strip())
        print("stopword rmed->\t"+line.strip())
        print("final  result->\t"+gene+"\t"+count)
        # only save the non_zero results
        if (int(count)>0):
            out.write(gene+"\t"+count)

sorted_f=out_f.replace(".txt","_sorted.txt")
os.system("sort -k2 -t$'\t' -rn " + out_f + " > " + sorted_f )


