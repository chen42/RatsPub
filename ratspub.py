#!/bin/env python3 
from nltk.tokenize import sent_tokenize
import os
import re

## turn dictionary (synonyms) to regular expression
def undic(dic):
    return "|".join(dic.values())

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def getSentences(query, gene):
    abstracts = os.popen("esearch -db pubmed -query " +  query + " | efetch -format uid |fetch-pubmed -path /run/media/hao/PubMed/Archive/ | xtract -pattern PubmedArticle -element MedlineCitation/PMID,ArticleTitle,AbstractText|sed \"s/-/ /g\"").read()
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

def gene_addiction(gene):
    # search gene name & drug name  in the context of addiction terms (i.e., exclude etoh affects cancer, or methods to extract cocaine) 
    q="\"(" + addiction.replace("|", " OR ")  + ") AND (" + drug.replace("|", " OR ", ) + ") AND " + gene + "\""
    sents=getSentences(q, gene)
    out=str()
    for sent in sents.split("\n"):
        for drug0 in drug_d:
            if findWholeWord(drug_d[drug0])(sent) :
                sent=sent.replace("<b>","").replace("</b>","")
                sent=re.sub(r'\b(%s)\b' % drug_d[drug0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"drug\t" + drug0+"\t"+sent+"\n"
        for add0 in addiction_d:
            if findWholeWord(addiction_d[add0])(sent) :
                sent=sent.replace("<b>","").replace("</b>","")
                sent=re.sub(r'\b(%s)\b' % addiction_d[add0], r'<b>\1</b>', sent, flags=re.I)
                out+=gene+"\t"+"addiction\t"+add0+"\t"+sent+"\n"
    return(out)

def gene_anatomical(gene):
    q="\"(" + brain.replace("|", " OR ")  + ") AND " + gene + "\""
    sents=getSentences(q,gene)
    out=str()
    for sent in sents.split("\n"):
        for brain0 in brain_d:
            if findWholeWord(brain_d[brain0])(sent) :
                sent=sent.replace("<b>","").replace("</b>","")
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
                sent=sent.replace("<b>","").replace("</b>","")
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

addiction_d = {"reward":"reward|hedonic|incentive|intracranial self stimulation|ICSS|reinforcement|conditioned place preference|CPP|self administration|self administered|drug reinforced|operant|instrumental response",
        "aversion":"aversion|aversive|CTA|withdrawal|conditioned taste aversion",
        "relapse":"relapse|reinstatement|craving|drug seeking|seeking",
        "sensitization":"sensitization",
        "addiction":"addiction|dependence|addictive|drug abuse|punishment|compulsive|escalation",
        "intoxication":"intoxication|binge"
        }
addiction=undic(addiction_d)

drug_d = {"alcohol":"alcohol|alcoholism|alcoholic",
        "nicotine":"smoking|nicotine|tobacco",
        "cocaine":"cocaine",
        "opioid":"opioid|opioids|fentanyl|oxycodone|oxycontin|heroin|morphine|methadone|buprenorphine",
        "amphetamine":"methamphetamine|amphetamine|METH",
        "cannabinoid":"endocannabinoid|cannabinoids|endocannabinoids|marijuana|cannabidiol|cannabinoid|tetrahydrocannabinol|thc|thc 9|Oleoylethanolamide|palmitoylethanolamide|acylethanolamides"
        }
drug=undic(drug_d)

brain_d ={"cortex":"cortex|prefrontal|pfc|mPFC|vmpfc|corticostriatal|cortico limbic|corticolimbic|prl|prelimbic|infralimbic|orbitofrontal|cingulate|cerebral|insular|insula",
          "striatum":"striatum|STR|striatal|caudate|putamen|basal ganglia|globus pallidus",
          "accumbens":"accumbens|accumbal|shell|core|Nacc|NacSh|acbs|acbc",
          "hippocampus":"hippocampus|hippocampal|hipp|hip|ca1|ca3|dentate gyrus|subiculum|vhipp|dhpc|vhpc",
          "amygdala":"amygdala|cea|bla|amy",
          "vta":"ventral tegmental|vta|pvta|mesolimbic|limbic|midbrain|mesoaccumbens"
          }
# brain region has too many short acronyms to just use the undic function, so search PubMed using the following 
brain="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic"

function_d={"neuroplasticity":"neuroplasticity|plasticity|long term potentiation|LTP|long term depression|LTD|synaptic|epsp|epsc|neurite|neurogenesis|boutons|mIPSC|IPSC|IPSP",
            "signalling":"signalling|signaling|phosphorylation|glycosylation",
#            "regulation":"increased|decreased|regulated|inhibited|stimulated",
            "transcription":"transcription|methylation|hypomethylation|hypermethylation|histone|ribosome",
            "neurotransmission": "neurotransmission|neuropeptides|neuropeptide|glutamate|glutamatergic|GABA|GABAergic|dopamine|dopaminergic|DAergic|cholinergic|nicotinic|muscarinic|serotonergic|serotonin|5 ht|acetylcholine",
            }
function=undic(function_d)

#https://htmlcolorcodes.com/
n0=generate_nodes(function_d, "#D7BDE2")
n1=generate_nodes(addiction_d,"#A9CCE3")
n2=generate_nodes(drug_d, "#A3E4D7")
n3=generate_nodes(brain_d, "#F9E79F")
default_nodes=n0+n1+n2+n3
