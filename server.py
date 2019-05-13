#!/bin/env  python3
from flask import Flask, render_template, request, session, Response
import tempfile
import random
import string
from ratspub import *
import time
import os

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
            nodes+="{ data: { id: '" + gene +  "', nodecolor:'#E74C3C', fontweight:700, url:'/gene_gene?gene="+gene+"'} },\n"
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            sent0=gene_addiction(gene)
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

@app.route("/gene_gene")
def gene_gene():
    query=request.args.get("gene")
    tmp_ggPMID=session['path']+"_ggPMID"
    os.system("esearch -db pubmed -query \"" +  query + "\" | efetch -format uid |sort >" + tmp_ggPMID)
    abstracts=os.popen("comm -1 -2 top_150_addiction_genes_uniq.pmid " + tmp_ggPMID + " |fetch-pubmed -path /run/media/hao/PubMed/Archive/ | xtract -pattern PubmedArticle -element MedlineCitation/PMID,ArticleTitle,AbstractText|sed \"s/-/ /g\"").read()
    os.system("rm "+tmp_ggPMID)
    topGenes=dict()
    out=str()
    hitGenes=dict()
    with open("./top_150_genes_symb_alias.txt", "r") as top_f:
        for line in top_f:
            (symb, alias)=line.strip().split("\t")
            topGenes[symb]=alias
    for row in abstracts.split("\n"):
        tiab=row.split("\t")
        pmid = tiab.pop(0)
        tiab= " ".join(tiab)
        sentences = sent_tokenize(tiab)
        ## keep the sentence only if it contains the gene 
        for sent in sentences:
            if findWholeWord(query)(sent):
                sent=re.sub(r'\b(%s)\b' % query, r'<strong>\1</strong>', sent, flags=re.I)
                for symb in topGenes:
                    if findWholeWord(topGenes[symb])(sent) :
                        sent=sent.replace("<b>","").replace("</b>","")
                        sent=re.sub(r'\b(%s)\b' % topGenes[symb], r'<b>\1</b>', sent, flags=re.I)
                        out+=query+"\t"+"gene\t" + symb+"\t"+pmid+"\t"+sent+"\n"
                        if symb in hitGenes.keys():
                            hitGenes[symb]+=1
                        else:
                            hitGenes[symb]=1
    gg_file=session['path']+"_ggSent" #gene_gene
    with open(gg_file, "w+") as gg:
        gg.write(out)
        gg.close()
    nodecolor={'query':"#E74C3C", 'top150': "#ccd1d1"}
    nodes= "{ data: { id: '" + query +  "', nodecolor: '" + nodecolor['query'] + "', nodetype: 'ggquery', fontweight:700,  url:'/shownode?nodetype=ggquery&node="+query+"' } },\n"
    edges=str()
    for key in hitGenes.keys():
        #nodes += "{ data: { id: '" + key +  "', nodecolor: '" + nodecolor['top150'] + "', nodetype: 'top150', fontcolor:'#F2D7D5', url:'/shownode?nodetype=top150&node="+key+"' } },\n"
        nodes += "{ data: { id: '" + key +  "', nodecolor: '" + nodecolor['top150'] + "', nodetype: 'top150', url:'/shownode?nodetype=top150&node="+key+"' } },\n"
        edgeID=gg_file+"|"+query+"|"+key
        edges+="{ data: { id: '" + edgeID+ "', source: '" + query + "', target: '" + key + "', sentCnt: " + str(hitGenes[key]) + ",  url:'/sentences?edgeID=" + edgeID + "' } },\n"
    return render_template("cytoscape.html", elements=nodes+edges)


if __name__ == '__main__':
    app.run(debug=True)
