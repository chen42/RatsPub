#!/bin/env python3 
import os, sys
import re
import time
from nltk.tokenize import sent_tokenize
from ratspub_keywords import *

def undic(dic):
    return "|".join(dic.values())

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def getSentences(query, genes):
    abstracts = os.popen("esearch -db pubmed -query " +  query + " | efetch -format uid |fetch-pubmed -path /run/media/hao/PubMed/Archive/ | xtract -pattern PubmedArticle -element MedlineCitation/PMID,ArticleTitle,AbstractText|sed \"s/-/ /g\"").read()
    gene_syno=genes.split("|")
    symb=gene_syno[0]
    out=str()
    for row in abstracts.split("\n"):
        tiab=row.split("\t")
        pmid = tiab.pop(0)
        tiab= " ".join(tiab)
        sentences = sent_tokenize(tiab)
          ## keep the sentence only if it contains the gene 
        for sent in sentences:
            for gene in gene_syno:
                if findWholeWord(gene)(sent):
                    sent=re.sub(r'\b(%s)\b' % gene, r'<strong>\1</strong>', sent, flags=re.I)
                    for drug0 in drug_d:
                        if findWholeWord(drug_d[drug0])(sent) :
                            sent=sent.replace("<b>","").replace("</b>","")
                            sent=re.sub(r'\b(%s)\b' % drug_d[drug0], r'<b>\1</b>', sent, flags=re.I)
                            out+=symb+"\t"+"drug\t" + drug0+"\t"+pmid+"\t"+sent+"\n"
                    for add0 in addiction_d:
                        if findWholeWord(addiction_d[add0])(sent) :
                            sent=sent.replace("<b>","").replace("</b>","")
                            sent=re.sub(r'\b(%s)\b' % addiction_d[add0], r'<b>\1</b>', sent, flags=re.I)
                            out+=symb+"\t"+"addiction\t"+add0+"\t"+pmid+"\t"+sent+"\n"
    return(out)

addiction=undic(addiction_d)
drug=undic(drug_d)


out=open("topGene_addiction_sentences.tab", "w+")
cnt=0

if len(sys.argv) != 2:
    print ("Please provide a sorted gene count file at the command line")
    sys.exit()

sorted_file=sys.argv[1] #  ncbi_gene_symb_syno_name_txid9606_absCnt_sorted_absCnt_sorted_absCnt_sorted_absCnt_sorted.txt
with open (sorted_file, "r") as f:
    for line in f:
        (genes, abstractCount)=line.strip().split("\t")
        genes=genes.replace("-","\ ")
        if int(abstractCount)>20:
            symb=genes.split("|")[0]
            print(symb+"-->"+genes)
            q="\'(\"" + addiction.replace("|", "\"[tiab] OR \"")  + "\") AND (\"" + drug.replace("|", "\"[tiab] OR \"", ) + "\") AND (\"" + genes.replace("|", "\"[tiab] OR \"", ) + "\")\'"
            sentences=getSentences(q,genes)
            out.write(sentences)
out.close()

os.system("cut -f 1,4 topGene_addiction_sentences.tab  |uniq |cut -f 1 |sort |uniq -c |sort -rn > topGeneAbstractCount.tab")
