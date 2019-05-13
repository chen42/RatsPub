#!/bin/env python3 
from nltk.tokenize import sent_tokenize
import os
import re

global function_d, brain_d, drug_d, addiction_d, brain_query_term

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

nodecolor={'function':"#A9CCE3", 'addiction': "#D7BDE2", 'drug': "#F9E79F", 'brain':"#A3E4D7"}
addiction_d = {"reward":"reward|hedonic|incentive|intracranial self stimulation|ICSS|reinforcement|reinforcing|conditioned place preference|CPP|self administration|self administered|drug reinforced|operant|instrumental response",
        "aversion":"aversion|aversive|CTA|withdrawal|conditioned taste aversion",
        "relapse":"relapse|reinstatement|craving|drug seeking|seeking",
        "sensitization":"sensitization",
        "addiction":"addiction|dependence|addictive|drug abuse|punishment|compulsive|escalation",
        "intoxication":"intoxication|binge"
        }
addiction=undic(addiction_d)
drug_d = {"alcohol":"alcohol|alcoholism|alcoholic|alcoholics",
        "nicotine":"smoking|nicotine|tobacco|smoker|smokers",
        "cocaine":"cocaine",
        "opioid":"opioid|opioids|fentanyl|oxycodone|oxycontin|heroin|morphine|methadone|buprenorphine|vicodin|hydrocodone|hycodan|kadian|percoset|hydromorphone|naloxone|codeine|suboxone|tramadol|kratom",
        "amphetamine":"methamphetamine|amphetamine|METH|AMPH",
        "cannabinoid":"endocannabinoid|cannabinoids|cannabis|endocannabinoids|marijuana|cannabidiol|cannabinoid|tetrahydrocannabinol|thc|thc 9|Oleoylethanolamide|palmitoylethanolamide|acylethanolamides"
        }
drug=undic(drug_d)
brain_d ={"cortex":"cortex|prefrontal|pfc|mPFC|vmpfc|corticostriatal|cortico limbic|corticolimbic|prl|prelimbic|infralimbic|orbitofrontal|cingulate|cerebral|insular|insula",
          "striatum":"striatum|STR|striatal|caudate|putamen|basal ganglia|globus pallidus|GPI",
          "accumbens":"accumbens|accumbal|shell|core|Nacc|NacSh|acbs|acbc",
          "hippocampus":"hippocampus|hippocampal|hipp|hip|ca1|ca3|dentate gyrus|subiculum|vhipp|dhpc|vhpc",
          "amygdala":"amygdala|cea|bla|amy",
          "vta":"ventral tegmental|vta|pvta|mesolimbic|limbic|midbrain|mesoaccumbens"
          }
# brain region has too many short acronyms to just use the undic function, so search PubMed using the following 
brain_query_term="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic"
function_d={"signalling":"signalling|signaling|phosphorylation|glycosylation",
            "transcription":"transcription|methylation|hypomethylation|hypermethylation|histone|ribosome",
            "neuroplasticity":"neuroplasticity|plasticity|long term potentiation|LTP|long term depression|LTD|synaptic|epsp|epsc|neurite|neurogenesis|boutons|mIPSC|IPSC|IPSP",
            "neurotransmission": "neurotransmission|neuropeptides|neuropeptide|glutamate|glutamatergic|GABA|GABAergic|dopamine|dopaminergic|DAergic|cholinergic|nicotinic|muscarinic|serotonergic|serotonin|5 ht|acetylcholine",
#            "regulation":"increased|decreased|regulated|inhibited|stimulated",
            }
function=undic(function_d)

#https://htmlcolorcodes.com/
n0=generate_nodes(function_d, 'function')
n1=generate_nodes(addiction_d, 'addiction')
n2=generate_nodes(drug_d, 'drug')
n3=generate_nodes(brain_d, 'brain')
default_nodes=n0+n1+n2+n3
