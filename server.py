from flask import Flask, render_template, request, redirect
import simplejson as json
from ratspub import *

app=Flask(__name__)
app.config['SECRET_KEY'] = '#DtfrL98G5t1dC*4'

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/search")
def search():
    global all_sentences 
    all_sentences=str()
    genes=request.args.get('query')
    genes=genes.replace(",", " ")
    genes=genes.replace(";", " ")
    genes=genes.split()
    nodes=default_nodes
    edges=str()
    for  gene in genes:
        nodes+="{ data: { id: '" + gene +  "', nodecolor:'#FADBD8', fontweight:700} },\n"
        sent0=gene_addiction(gene)
        e0=generate_edges(sent0)
        sent1=gene_functional(gene)
        e1=generate_edges(sent1)
        sent2=gene_anatomical(gene)
        e2=generate_edges(sent2)
        edges+=e0+e1+e2
        all_sentences+=sent0+sent1+sent2
    return render_template('cytoscape.html', elements=nodes+edges)

@app.route("/sentences")
def sentences():
    edge=request.args.get('edgeID')
    (gene0, cat0)=edge.split("|")
    print (gene0 + cat0)
    out=str()
    for sent in all_sentences.split("\n"):
        #print (sent) 
        if len(sent.strip())!=0:
           (gene,nouse,cat, pmid, text)=sent.split("\t") 
           if (gene == gene0 and cat == cat0) :
               out+= "<li> "+ text + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid +"\" target=_new>PMID:"+pmid+"<br></a>"
    return render_template('sentences.html', sentences=out)

if __name__ == '__main__':
    app.run(debug=True)
