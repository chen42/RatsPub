#!/bin/env python3 
from nltk.tokenize import sent_tokenize
import os
import re
from ratspub_keywords import *
from gene_synonyms import *

global function_d, brain_d, drug_d, addiction_d, brain_query_term, pubmed_path, genes

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

def generate_nodes_json(nodes_d, nodetype):
    # include all search terms even if there are no edges, just to show negative result 
    nodes_json0 =str()
    for node in nodes_d:
        nodes_json0 += "{ \"id\": \"" + node +  "\", \"nodecolor\": \"" + nodecolor[nodetype] + "\", \"nodetype\": \"" + nodetype + "\", \"url\":\"/shownode?nodetype=" + nodetype + "&node="+node+"\" },\n"
    return(nodes_json0)

def generate_edges(data, filename):
    pmid_list=[]
    json0=str()
    edgeCnts={}
    for line in  data.split("\n"):
        if len(line.strip())!=0:
            (source, cat, target, pmid, sent) = line.split("\t")
            edgeID=filename+"|"+source+"|"+target
            if (edgeID in edgeCnts) and (pmid+target not in pmid_list):
                edgeCnts[edgeID]+=1
                pmid_list.append(pmid+target)
            elif (edgeID not in edgeCnts) and (pmid+target not in pmid_list):
                edgeCnts[edgeID]=1
                pmid_list.append(pmid+target)
    for edgeID in edgeCnts:
        (filename, source,target)=edgeID.split("|")
        json0+="{ data: { id: '" + edgeID + "', source: '" + source + "', target: '" + target + "', sentCnt: " + str(edgeCnts[edgeID]) + ",  url:'/sentences?edgeID=" + edgeID + "' } },\n"
    return(json0)

def generate_edges_json(data, filename):
    pmid_list=[]
    edges_json0=str()
    edgeCnts={}
    for line in  data.split("\n"):
        if len(line.strip())!=0:
            (source, cat, target, pmid, sent) = line.split("\t")
            edgeID=filename+"|"+source+"|"+target
            if (edgeID in edgeCnts) and (pmid+target not in pmid_list):
                edgeCnts[edgeID]+=1
                pmid_list.append(pmid+target)
            elif (edgeID not in edgeCnts) and (pmid+target not in pmid_list):
                edgeCnts[edgeID]=1
                pmid_list.append(pmid+target)
    for edgeID in edgeCnts:
        (filename, source,target)=edgeID.split("|")
        edges_json0+="{ \"id\": \"" + edgeID + "\", \"source\": \"" + source + "\", \"target\": \"" + target + "\", \"sentCnt\": \"" + str(edgeCnts[edgeID]) + "\",  \"url\":\"/sentences?edgeID=" + edgeID + "\" },\n"
    return(edges_json0)

def searchArchived(sets, query, filetype):
    if sets=='topGene':
        dataFile="topGene_addiction_sentences.tab"
        nodes= "{ data: { id: '" + query +  "', nodecolor: '" + "#2471A3" + "', fontweight:700, url:'/progress?query="+query+"' } },\n"

    elif sets=='GWAS':
        dataFile="gwas_addiction.tab"
        nodes=str()
    with open(dataFile, "r") as sents:
        pmid_list=[]
        cat1_list=[]
        catCnt={}
        for sent in sents:
            (symb, cat0, cat1, pmid, sent)=sent.split("\t")
            if (symb.upper() == query.upper()) :
                if (cat1 in catCnt.keys()) and (pmid+cat1 not in pmid_list):
                    pmid_list.append(pmid+cat1)
                    catCnt[cat1]+=1
                elif (cat1 not in catCnt.keys()):
                    catCnt[cat1]=1
                    pmid_list.append(pmid+cat1)

    nodes= "{ data: { id: '" + query +  "', nodecolor: '" + "#2471A3" + "', fontweight:700, url:'/progress?query="+query+"' } },\n"
    edges=str()
    gwas_json=str()
    for key in catCnt.keys():
        if sets=='GWAS':
            nc=nodecolor["GWAS"]
            nodes += "{ data: { id: '" + key +  "', nodecolor: '" + nc + "', url:'https://www.ebi.ac.uk/gwas/search?query="+key.replace("_GWAS","")+"' } },\n"
        elif key in drug_d.keys():
            nc=nodecolor["drug"]
            nodes += "{ data: { id: '" + key +  "', nodecolor: '" + nc + "', url:'/shownode?node="+key+"' } },\n"
        else:
            nc=nodecolor["addiction"]
            nodes += "{ data: { id: '" + key +  "', nodecolor: '" + nc + "', url:'/shownode?node="+key+"' } },\n"
        edgeID=dataFile+"|"+query+"|"+key
        edges+="{ data: { id: '" + edgeID+ "', source: '" + query + "', target: '" + key + "', sentCnt: " + str(catCnt[key]) + ",  url:'/sentences?edgeID=" + edgeID + "' } },\n"
        gwas_json+="{ \"id\": \"" + edgeID + "\", \"source\": \"" + query + "\", \"target\": \"" + key + "\", \"sentCnt\": \"" + str(catCnt[key]) + "\",  \"url\":\"/sentences?edgeID=" + edgeID + "\" },\n"
    if(filetype == 'cys'):
        return(nodes+edges)
    else:
        return(gwas_json)
# brain region has too many short acronyms to just use the undic function, so search PubMed using the following 
brain_query_term="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic|habenula"
function=undic(function_d)
addiction=undic(addiction_d)
drug=undic(drug_d)

gene_s=undic(genes)

nodecolor={'function':"#A9CCE3", 'addiction': "#D7BDE2", 'drug': "#F9E79F", 'brain':"#A3E4D7", 'GWAS':"#AEB6BF", 'stress':"#EDBB99", 'psychiatric':"#F5B7B1"}
#https://htmlcolorcodes.com/ third column down

n0=generate_nodes(function_d, 'function')
n1=generate_nodes(addiction_d, 'addiction')
n2=generate_nodes(drug_d, 'drug')
n3=generate_nodes(brain_d, 'brain')
n4=generate_nodes(stress_d, 'stress')
n5=generate_nodes(psychiatric_d, 'psychiatric')
n6=''

nj0=generate_nodes_json(function_d, 'function')
nj1=generate_nodes_json(addiction_d, 'addiction')
nj2=generate_nodes_json(drug_d, 'drug')
nj3=generate_nodes_json(brain_d, 'brain')
nj4=generate_nodes_json(stress_d, 'stress')
nj5=generate_nodes_json(psychiatric_d, 'psychiatric')
nj6=''



pubmed_path=os.environ["EDIRECT_PUBMED_MASTER"]

if ( not pubmed_path): 
    pubmed_path="~/Documents/RatsPub/PubMed"
pubmed_path +="/Archive"

'''
print (pubmed_path)
host= os.popen('hostname').read().strip()
if host=="x1":
    pubmed_path="/run/media/hao/PubMed/Archive/"
elif host=="hchen3":
    pubmed_path="/media/hao/2d554499-6c5b-462d-85f3-5c49b25f4ac8/PubMed/Archive"
elif host=="penguin2":
    pubmed_path="/export2/PubMed/Archive"
elif host=="hchen":
    pubmed_path="~/Dropbox/ChenLab/Hakan/RatsPub/PubMed/Archive"
'''
