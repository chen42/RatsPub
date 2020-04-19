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
        do_search=0
        inputline=line
        line=line.replace("-","\ ")
        # remove the annotated stopword
        if "'" in line:
            do_search=1
            words=line.split("|")
            line=str()
            for word in words:
                # ' is used to mark/annotate a word is a stop word in the results
                # remove the ' mark 
                if "'" in word:
                    word=word.replace("'","")
                    stopWords.append(word)
                    saveStopWord(word)
                line+="|"+word
            line=line[1:]
        line=removeStopWords(line)
        # tab is added if there are abstracts counts
        if "\t" in line:
            (gene, count)=line.split("\t")
            # rerun if count is low, these are less annotated
        #    if int(count)<50:
        #        do_search=1
        else:
            #no count, 
            gene=line.strip()
            do_search=1
        if do_search==1:
            # remove synonyms with only two letters
            if "|" in gene:
                synos=gene.split("|")
                # keep the gene name regardless number of characters
                gene=synos[0]
                #print ("gene: "+gene + " synos -->" + str(synos[1:]))
                for syno in synos[1:]:
                    #synonyms must be at least 3 characters
                    if len(syno)>3:
                        gene+="|"+syno
            gene_q=gene.replace("|", "\"[tiab] OR \"")
            gene_q+="[tiab]"
            count=gene_addiction_cnt(gene_q)
            print("original line->\t"+inputline.strip())
            print("stopword rmed->\t"+line.strip())
            print("final  result->\t"+gene+"\t"+count)
            out.write(gene+"\t"+count)
        else:
            print("original resl->\t"+inputline.strip())
            out.write(inputline)

sorted_f=output_f.replace(".txt","_sorted.txt")
os.system("sort -k2 -t$'\t' -rn " + output_f + " > " + sorted_f )


