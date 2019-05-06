#!/bin/env python3 
from nltk.tokenize import sent_tokenize
import os
import re
import codecs
import sys

gene=sys.argv[1]

addiction_terms="sensitization|intake|addiction|drug abuse|relapse|self-administered|self-administration|voluntary|reinstatement|binge|intoxication|withdrawal|chronic"

drugs="alcohol|alcoholism|smoking|nicotine|tobacco|methamphetamine|amphetamine|cocaine|opioid|fentanyl|oxycodone|oxycontin|heroin|morphine|marijuana|cannabinoid|tetrahydrocannabinol|thc"

brain_regions="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic"

brain_d ={"cortex":"cortex|pfc|vmpfc|il|pl|prelimbic|infralimbic",
          "striatum":"striatum|STR",
          "accumbens":"shell|core|NAcc|acbs|acbc",
          "hippocampus":"hippocampus|hipp|hip|ca1|ca3|dentate|gyrus",
          "amygadala":"amygadala|cea|bla|amy",
          "ventral tegmental":"ventral tegmental|vta"
          }

function="LTP|LTD|plasticity|regulate|glutamate|GABA|cholinergic|serotoninergic|synaptic|methylation|transcription|phosphorylation"

drugs_d = {"alcohol":"alcohol|alcoholism",
        "nicotine":"smoking|nicotine|tobacco",
        "amphetamine":"methamphetamine|amphetamine",
        "cocaine":"cocaine",
        "opioid":"opioid|fentanyl|oxycodone|oxycontin|heroin|morphine",
        "cannabinoid":"marijuana|cannabinoid|Tetrahydrocannabinol|thc"
        }

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
        for sent in sentences:
            if findWholeWord(gene)(sent):
                sent=re.sub(r'\b(%s)\b' % gene, r'<b>\1</b>', sent, flags=re.I)
                out+=pmid+"\t"+sent+"\n"
    return(out)

def gene_addiction(gene):
    q="\"(" + addiction_terms.replace("|", " OR ")  + ") AND (" + drugs.replace("|", " OR ", ) + ") AND " + gene + "\""
    sents=getSentences(q)
    out=str()
    for sent in sents.split("\n"):
        for drug0 in drugs_d:
            if findWholeWord(drugs_d[drug0])(sent) :
                sent=re.sub(r'\b(%s)\b' % drugs_d[drug0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+drug0+"\t"+sent+"\n"
    return(out)

def gene_brainRegion(gene):
    q="\"(" + brain_regions.replace("|", " OR ")  + ") AND " + gene + "\""
    sents=getSentences(q)
    out=str()
    for sent in sents.split("\n"):
        for brain0 in brain_d:
            if findWholeWord(brain_d[brain0])(sent) :
                sent=re.sub(r'\b(%s)\b' % brain_d[brain0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+brain0+"\t"+sent+"\n"
    return(out)

report=str()
out=gene_addiction(gene)
report+=out
out=gene_brainRegion(gene)
report+=out
with codecs.open(gene+"_addiction_sentences.tab", "w", encoding='utf8') as writer:
   writer.write(report)
   writer.close()



