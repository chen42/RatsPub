#!/bin/env  python3
from flask import Flask, render_template, request, session, Response
import tempfile
import random
import string
from ratspub import *
import time

app=Flask(__name__)
app.config['SECRET_KEY'] = '#DtfrL98G5t1dC*4'

@app.route("/")
def root():
    return render_template('index.html')

@app.route('/progress')
def progress():
    # only 1-6 terms are allowed
    genes=request.args.get('query')
    genes=genes.replace(",", " ")
    genes=genes.replace(";", " ")
    genes=genes.split()
    if len(genes)>=6:
        message="<span class='text-danger'>Up to five terms can be searched at a time</span>"
        return render_template('index.html', message=message)
    elif len(genes)==0:
        message="<span class='text-danger'>Please enter a search term </span>"
        return render_template('index.html', message=message)
    # put the query in session cookie
    session['query']=genes
    # generate a unique session ID to track the results 
    tf_path=tempfile.gettempdir()
    session['path']=tf_path+"/tmp" + ''.join(random.choice(string.ascii_letters) for x in range(6))
    return render_template('progress.html')

@app.route("/search")
def search():
    genes=session['query']
    percent=round(100/(len(genes)*3),1)
    snt_file=session['path']+"_snt"
    cysdata=open(session['path']+"_cy","w+")
    sntdata=open(snt_file,"w+")
    def generate(genes, tf_name):
        sentences=str()
        edges=str()
        nodes=default_nodes
        progress=0
        for  gene in genes:
            nodes+="{ data: { id: '" + gene +  "', nodecolor:'#FADBD8', fontweight:700, url:'https://www.ncbi.nlm.nih.gov/gene/?term="+gene+"'} },\n"
            sent0=gene_addiction(gene)
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e0=generate_edges(sent0, tf_name)
            sent1=gene_functional(gene)
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e1=generate_edges(sent1, tf_name)
            sent2=gene_anatomical(gene)
            progress+=percent
            e2=generate_edges(sent2, tf_name)
            edges+=e0+e1+e2
            sentences+=sent0+sent1+sent2
            #save data before the last yield
            if (progress>99):
                progress=100
                sntdata.write(sentences)
                sntdata.close()
                cysdata.write(nodes+edges)
                cysdata.close()
            yield "data:"+str(progress)+"\n\n"
    return Response(generate(genes, snt_file), mimetype='text/event-stream')

@app.route('/cytoscape')
def cytoscape():
    with open(session['path']+"_cy","r") as f:
        elements=f.read()
        return render_template('cytoscape.html', elements=elements)

@app.route("/sentences")
def sentences():
    edge=request.args.get('edgeID')
    (tf_name, gene0, cat0)=edge.split("|")
    out="<h3>"+gene0 + " and " + cat0  + "</h3><hr>\n"
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
