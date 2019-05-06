#!/bin/env python3 
from nltk.tokenize import sent_tokenize
import os
import re
import codecs
import sys

gene=sys.argv[1]

## turn dictionary (synonyms) to regular expression
def undic(dic):
    return "|".join(dic.keys())+"|"+"|".join(dic.values())

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def getSentences(query):
    abstracts = os.popen("esearch -db pubmed -query " +  query + " | efetch -format uid |fetch-pubmed -path /run/media/hao/PubMed/Archive/ | xtract -pattern PubmedArticle -element MedlineCitation/PMID,ArticleTitle,AbstractText").read()
    out=str()
    for row in abstracts.split("\n"):
        tiab=row.split("\t")
        pmid = tiab.pop(0)
        tiab= " ".join(tiab)
        sentences = sent_tokenize(tiab)
        ## keep the sentence only if it contains the gene 
        for sent in sentences:
            if findWholeWord(gene)(sent):
                sent=re.sub(r'\b(%s)\b' % gene, r'<b>\1</b>', sent, flags=re.I)
                out+=pmid+"\t"+sent+"\n"
    return(out)

def gene_addiction(gene):
    # search gene name & drug name  in the context of addiction terms (i.e., exclude etoh affects cancer, or methods to extract cocaine) 
    q="\"(" + addiction.replace("|", " OR ")  + ") AND (" + drugs.replace("|", " OR ", ) + ") AND " + gene + "\""
    sents=getSentences(q)
    out=str()
    for sent in sents.split("\n"):
        for drug0 in drugs_d:
            if findWholeWord(drugs_d[drug0])(sent) :
                sent=re.sub(r'\b(%s)\b' % drugs_d[drug0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"drug\t" + drug0+"\t"+sent+"\n"
        for add0 in addiction.split("|"):
            if findWholeWord(add0)(sent) :
                sent=re.sub(r'\b(%s)\b' % add0, r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"addiction\t"+add0+"\t"+sent+"\n"
    return(out)

def gene_anatomical(gene):
    q="\"(" + brain.replace("|", " OR ")  + ") AND " + gene + "\""
    sents=getSentences(q)
    out=str()
    for sent in sents.split("\n"):
        for brain0 in brain_d:
            if findWholeWord(brain_d[brain0])(sent) :
                sent=re.sub(r'\b(%s)\b' % brain_d[brain0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"brain\t"+brain0+"\t"+sent+"\n"
    return(out)

def gene_biological(gene):
    q="\"(" + biological.replace("|", " OR ")  + ") AND " + gene + "\""
    sents=getSentences(q)
    out=str()
    for sent in sents.split("\n"):
        for bio0 in biological_d:
            if findWholeWord(biological_d[bio0])(sent) :
                sent=re.sub(r'\b(%s)\b' % biological_d[bio0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"function\t"+bio0+"\t"+sent+"\n"
    return(out)

addiction="reward|reinforcement|sensitization|intake|addiction|drug abuse|relapse|self-administered|self-administration|reinstatement|binge|intoxication|withdrawal|conditioned place preference|aversion|aversive|CPP"

drugs_d = {"alcohol":"alcohol|alcoholism",
        "nicotine":"smoking|nicotine|tobacco",
        "amphetamine":"methamphetamine|amphetamine",
        "cocaine":"cocaine",
        "opioid":"opioid|fentanyl|oxycodone|oxycontin|heroin|morphine",
        "cannabinoid":"marijuana|cannabinoid|Tetrahydrocannabinol|thc"
        }
drugs=undic(drugs_d)

brain_d ={"cortex":"cortex|pfc|vmpfc|il|pl|prelimbic|infralimbic",
          "striatum":"striatum|STR",
          "accumbens":"shell|core|NAcc|acbs|acbc",
          "hippocampus":"hippocampus|hipp|hip|ca1|ca3|dentate|gyrus",
          "amygadala":"amygadala|cea|bla|amy",
          "vta":"ventral tegmental|vta|pvta"
          }
# brain region has too many short acronyms to just use the undic function, so search PubMed using the following 
brain="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic"

biological_d={"plasticity":"LTP|LTD|plasticity|synaptic|epsp|epsc",
            "neurotransmission": "neurotransmission|glutamate|GABA|cholinergic|serotoninergic",
            "signalling":"signalling|phosphorylation|glycosylation",
#            "regulation":"increased|decreased|regulated|inhibited|stimulated",
            "transcription":"transcription|methylation|histone|ribosome",
            }
biological=undic(biological_d)

report=str()
out0=gene_addiction(gene)
report+=out0
out1=gene_anatomical(gene)
report+=out1
out2=gene_biological(gene)
report+=out2
with codecs.open(gene+"_addiction_sentences.tab", "w", encoding='utf8') as writer:
   writer.write(report)
   writer.close()



