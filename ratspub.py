#!/bin/env python3 
from nltk.tokenize import sent_tokenize
import os
import re
import codecs
import sys

#gene=sys.argv[1]

## turn dictionary (synonyms) to regular expression
def undic(dic):
    return "|".join(dic.values())

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def getSentences(query, gene):
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
    q="\"(" + addiction.replace("|", " OR ")  + ") AND (" + drug.replace("|", " OR ", ) + ") AND " + gene + "\""
    sents=getSentences(q, gene)
    out=str()
    for sent in sents.split("\n"):
        for drug0 in drug_d:
            if findWholeWord(drug_d[drug0])(sent) :
                sent=re.sub(r'\b(%s)\b' % drug_d[drug0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"drug\t" + drug0+"\t"+sent+"\n"
        for add0 in addiction_d:
            if findWholeWord(add0)(sent) :
                sent=re.sub(r'\b(%s)\b' % add0, r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"addiction\t"+add0+"\t"+sent+"\n"
    return(out)

def gene_anatomical(gene):
    q="\"(" + brain.replace("|", " OR ")  + ") AND " + gene + "\""
    sents=getSentences(q,gene)
    out=str()
    for sent in sents.split("\n"):
        for brain0 in brain_d:
            if findWholeWord(brain_d[brain0])(sent) :
                sent=re.sub(r'\b(%s)\b' % brain_d[brain0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"brain\t"+brain0+"\t"+sent+"\n"
    return(out)

def gene_functional(gene):
    q="\"(" + function.replace("|", " OR ")  + ") AND " + gene + "\""
    sents=getSentences(q,gene)
    out=str()
    for sent in sents.split("\n"):
        for bio0 in function_d:
            if findWholeWord(function_d[bio0])(sent) :
                sent=re.sub(r'\b(%s)\b' % function_d[bio0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"function\t"+bio0+"\t"+sent+"\n"
    return(out)

def generate_nodes(nodes_d, nodecolor):
    # include all search terms even if there are no edges, just to show negative result 
    json0 =str() #"{ data: { id: '" + gene +  "'} },\n"
    for node in nodes_d:
        json0 += "{ data: { id: '" + node +  "', nodecolor: '" + nodecolor + "' } },\n"
    return(json0)

def generate_edges(data):
    json0=str()
    edgeCnts={}
    for line in  data.split("\n"):
        if len(line.strip())!=0:
            (source, cat, target, pmid, sent) = line.split("\t")
            edgeID=source+"|"+target
            if edgeID in edgeCnts:
                edgeCnts[edgeID]+=1
            else:
                edgeCnts[edgeID]=1
    for edgeID in edgeCnts:
        (source,target)=edgeID.split("|")
        json0+="{ data: { id: \'" + edgeID + "\', source: \'" + source + "\', target: '" + target + "\', sentCnt: '" + str(edgeCnts[edgeID]) + "',  url:'/sentences?edgeID=" + edgeID + "' } },\n"
    return(json0)



addiction_d = {"reward":"reward|reinforcement|conditioned place preference|CPP|self-administration|self-administered",
        "aversion":"aversion|aversive|CTA|withdrawal",
        "relapse":"relapse|reinstatement|craving|drug seeking",
        "sensitization":"sensitization",
        "addiction":"addiction|drug abuse",
        "intoxication":"intoxication|binge"
        }
addiction=undic(addiction_d)

drug_d = {"alcohol":"alcohol|alcoholism",
        "nicotine":"smoking|nicotine|tobacco",
        "cocaine":"cocaine",
        "opioid":"opioid|fentanyl|oxycodone|oxycontin|heroin|morphine",
        "amphetamine":"methamphetamine|amphetamine|METH",
        "cannabinoid":"marijuana|cannabinoid|tetrahydrocannabinol|thc|thc-9"
        }
drug=undic(drug_d)

brain_d ={"cortex":"cortex|pfc|vmpfc|il|pl|prelimbic|infralimbic",
          "striatum":"striatum|STR",
          "accumbens":"shell|core|NAcc|acbs|acbc",
          "hippocampus":"hippocampus|hipp|hip|ca1|ca3|dentate|gyrus",
          "amygadala":"amygadala|cea|bla|amy",
          "vta":"ventral tegmental|vta|pvta"
          }
# brain region has too many short acronyms to just use the undic function, so search PubMed using the following 
brain="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic"

function_d={"plasticity":"LTP|LTD|plasticity|synaptic|epsp|epsc",
            "signalling":"signalling|phosphorylation|glycosylation",
#            "regulation":"increased|decreased|regulated|inhibited|stimulated",
            "transcription":"transcription|methylation|histone|ribosome",
            "neurotransmission": "neurotransmission|glutamate|GABA|cholinergic|serotoninergic",
            }
function=undic(function_d)

#https://htmlcolorcodes.com/
n0=generate_nodes(function_d, "#D7BDE2")
n1=generate_nodes(addiction_d,"#A9CCE3")
n2=generate_nodes(drug_d, "#A3E4D7")
n3=generate_nodes(brain_d, "#F9E79F")
default_nodes=n0+n1+n2+n3
