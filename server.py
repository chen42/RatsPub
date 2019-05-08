from flask import Flask, render_template, request, redirect
import simplejson as json
from gatpub import *

app=Flask(__name__)
app.config['SECRET_KEY'] = '#DtfrL98G5t1dC*4'

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/network", methods=['GET', 'POST'])
def network():
    edges_list=[]
    nodes_list=[]
    if request.method == 'POST':
        term = request.form
        genes=term['query']
        genes=genes.replace(",", " ")
        genes=genes.replace(";", " ")
        genes=genes.split()
        nodes=default_nodes
        edges=str()
        for  gene in genes:
            nodes+="{ data: { id: '" + gene +  "', nodecolor:'#FADBD8', fontweight:700} },\n"
            tmp0=gene_addiction(gene)
            e0=generate_edges(tmp0)
            tmp1=gene_functional(gene)
            e1=generate_edges(tmp1)
            tmp2=gene_anatomical(gene)
            e2=generate_edges(tmp2)
            edges+=e0+e1+e2
        return render_template('network.html', elements=nodes+edges)
if __name__ == '__main__':
    app.run(debug=True)
