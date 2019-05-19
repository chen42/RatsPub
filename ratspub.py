#!/bin/env python3 
from nltk.tokenize import sent_tokenize
import os
import re
from ratspub_keywords import *

global function_d, brain_d, drug_d, addiction_d, brain_query_term, pubmed_path


## turn dictionary (synonyms) to regular expression
def undic(dic):
    return "|".join(dic.values())

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def getSentences(query, gene):
    abstracts = os.popen("esearch -db pubmed -query " +  query + " | efetch -format uid |fetch-pubmed -path "+ pubmed_path + " | xtract -pattern PubmedArticle -element MedlineCitation/PMID,ArticleTitle,AbstractText|sed \"s/-/ /g\"").read()
    out=str()
    for row in abstracts.split("\n"):
        tiab=row.split("\t")
        pmid = tiab.pop(0)
        tiab= " ".join(tiab)
        sentences = sent_tokenize(tiab)
        ## keep the sentence only if it contains the gene 
        for sent in sentences:
            if findWholeWord(gene)(sent):
                sent=re.sub(r'\b(%s)\b' % gene, r'<strong>\1</strong>', sent, flags=re.I)
                out+=pmid+"\t"+sent+"\n"
    return(out)

def gene_category(gene, cat_d, query, cat):
    #e.g. BDNF, addiction_d, undic(addiction_d) "addiction"
    q="\"(" + query.replace("|", " OR ")  + ") AND " + gene + "\""
    sents=getSentences(q, gene)
    out=str()
    for sent in sents.split("\n"):
        for key in cat_d:
            if findWholeWord(cat_d[key])(sent) :
                sent=sent.replace("<b>","").replace("</b>","") # remove other highlights
                sent=re.sub(r'\b(%s)\b' % cat_d[key], r'<b>\1</b>', sent, flags=re.I) # highlight keyword
                out+=gene+"\t"+ cat + "\t"+key+"\t"+sent+"\n"
    return(out)

def generate_nodes(nodes_d, nodetype):
    # include all search terms even if there are no edges, just to show negative result 
    json0 =str()
    for node in nodes_d:
        json0 += "{ data: { id: '" + node +  "', nodecolor: '" + nodecolor[nodetype] + "', nodetype: '"+nodetype + "', url:'/shownode?nodetype=" + nodetype + "&node="+node+"' } },\n"
    return(json0)

def generate_edges(data, filename):
    json0=str()
    edgeCnts={}
    for line in  data.split("\n"):
        if len(line.strip())!=0:
            (source, cat, target, pmid, sent) = line.split("\t")
            edgeID=filename+"|"+source+"|"+target
            if edgeID in edgeCnts:
                edgeCnts[edgeID]+=1
            else:
                edgeCnts[edgeID]=1
    for edgeID in edgeCnts:
        (filename, source,target)=edgeID.split("|")
        json0+="{ data: { id: '" + edgeID + "', source: '" + source + "', target: '" + target + "', sentCnt: " + str(edgeCnts[edgeID]) + ",  url:'/sentences?edgeID=" + edgeID + "' } },\n"
    return(json0)

# brain region has too many short acronyms to just use the undic function, so search PubMed using the following 
brain_query_term="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic|habenula"
function=undic(function_d)
addiction=undic(addiction_d)
drug=undic(drug_d)

nodecolor={'function':"#A9CCE3", 'addiction': "#D7BDE2", 'drug': "#F9E79F", 'brain':"#A3E4D7"}
#https://htmlcolorcodes.com/
n0=generate_nodes(function_d, 'function')
n1=generate_nodes(addiction_d, 'addiction')
n2=generate_nodes(drug_d, 'drug')
n3=generate_nodes(brain_d, 'brain')
default_nodes=n0+n1+n2+n3


host= os.popen('hostname').read().strip()
if host=="x1":
    pubmed_path="/run/media/hao/PubMed/Archive/"
elif host=="hchen3":
    pubmed_path="/media/hao/2d554499-6c5b-462d-85f3-5c49b25f4ac8/PubMed/Archive"

