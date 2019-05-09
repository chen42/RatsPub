#!/bin/env  python3
from flask import Flask, render_template, request, redirect
import tempfile
import random
import string
from ratspub import *

app=Flask(__name__)
app.config['SECRET_KEY'] = '#DtfrL98G5t1dC*4'

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/search")
def search():
    tf_path=tempfile.gettempdir()
    tf_name=tf_path+"/tmp"+''.join(random.choice(string.ascii_letters) for x in range(6))
    all_sentences=str()
    genes=request.args.get('query')
    genes=genes.replace(",", " ")
    genes=genes.replace(";", " ")
    genes=genes.split()
    if len(genes)>=6:
        message="<span class='text-danger'>Up to five terms can be searched at a time</span>"
        return render_template('index.html', message=message)
    nodes=default_nodes
    edges=str()
    for  gene in genes:
        nodes+="{ data: { id: '" + gene +  "', nodecolor:'#FADBD8', fontweight:700, url:'https://www.ncbi.nlm.nih.gov/gene/?term="+gene+"'} },\n"
        sent0=gene_addiction(gene)
        e0=generate_edges(sent0, tf_name)
        sent1=gene_functional(gene)
        e1=generate_edges(sent1, tf_name)
        sent2=gene_anatomical(gene)
        e2=generate_edges(sent2, tf_name)
        edges+=e0+e1+e2
        all_sentences+=sent0+sent1+sent2
    #session['tmpfile']={'filename':tf_name}
    with open(tf_name,"w") as f:
        f.write(all_sentences)
        f.close()
    return render_template('cytoscape.html', elements=nodes+edges)

@app.route("/sentences")
def sentences():
    edge=request.args.get('edgeID')
    (tf_name, gene0, cat0)=edge.split("|")
    out="<h3>"+gene0 + " and " + cat0  + "</h3><hr>\n"
    print(tf_name)
    with open(tf_name, "r") as df:
        all_sents=df.read()
    for sent in all_sents.split("\n"):
        if len(sent.strip())!=0:
           (gene,nouse,cat, pmid, text)=sent.split("\t")
           if (gene == gene0 and cat == cat0) :
               out+= "<li> "+ text + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid +"\" target=_new>PMID:"+pmid+"<br></a>"
    return render_template('sentences.html', sentences="<ol>"+out+"</ol><p>")

@app.route("/shownode")
def shownode():
    node=request.args.get('node')
    allnodes={**brain_d, **drug_d, **function_d, **addiction_d}
    out="<p>"+node.upper()+"<hr><li>"+ allnodes[node].replace("|", "<li>")
    return render_template('sentences.html', sentences=out+"<p>")


if __name__ == '__main__':
    app.run(debug=True)
