import re
import sys

## generate the html page for the top genes

## put gene names and alias in a dictionary
#ncbi_gene_symb_syno_name_txid9606_absCnt_sorted_absCnt_sorted_absCnt_absCnt_sorted.txt
if (len(sys.argv) != 2):
    print ("please provide the name of a sorted gene abstract count file")
    sys.exit()

geneNames={}
with open (sys.argv[1],"r") as f:
    for line in f:
        (genes, count)=line.strip().split("\t")
        gene=genes.split("|")
        names=re.sub(r'^.*?\|', "", genes)
        geneNames[gene[0]]=names.strip().replace("|", "; ")

out=str()
html=str()
with open("./topGeneAbstractCount.tab" ,"r") as gc:
    cnt=0
    for  line in gc:
        cnt+=1
        line=re.sub(r'^\s+','',line)
        print (line)
        pmid_cnt, symb=line.strip().split()
        out+= symb+"\t"+geneNames[symb]+"\n"
        html+="<li><a href=\"/showTopGene?topGene="+symb+"\">"+symb+"</a> <span style=\"font-size:small; color:grey\">("+geneNames[symb]+")</span><br>\n"
        if cnt==100:
            break

with open("topGene_symb_alias.txt", "w+")  as tg:
    tg.write(out)
    tg.close()


htmlout='''
{% extends "layout.html" %}
{% block content %}

<h4> Top addiction related genes </h4>

<br>
These genes are ranked by the number of PubMed abstracts that contain the name of the gene and one or more addiction related keyword. Alias were obtained from NCBI gene database and have been curated to remove most, but not all, false matches.
<hr>

<ol>''' + html  + '''
</ol>
{% endblock %}
'''

with open("./templates/topAddictionGene.html", "w+")  as html_f:
    html_f.write(htmlout)
    html_f.close()

