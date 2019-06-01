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

@app.route("/about")
def about():
    return render_template('about.html')

@app.route('/progress')
def progress():
    # only 1-6 terms are allowed
    genes=request.args.get('query')
    genes=genes.replace(",", " ")
    genes=genes.replace(";", " ")
    genes=genes.split()
    if len(genes)>=100:
        message="<span class='text-danger'>Up to 100 terms can be searched at a time</span>"
        return render_template('index.html', message=message)
    elif len(genes)==0:
        message="<span class='text-danger'>Please enter a search term </span>"
        return render_template('index.html', message=message)
    # put the query in session cookie
    session['query']=genes
    # generate a unique session ID to track the results 
    tf_path=tempfile.gettempdir()
    session['path']=tf_path+"/tmp" + ''.join(random.choice(string.ascii_letters) for x in range(6))
    return render_template('progress.html', url_in="search", url_out="cytoscape")

@app.route("/search")
def search():
    genes=session['query']
    percent=round(100/(len(genes)*4),1)
    snt_file=session['path']+"_snt"
    cysdata=open(session['path']+"_cy","w+")
    sntdata=open(snt_file,"w+")
    zeroLinkNode=open(session['path']+"_0link","w+")
    def generate(genes, tf_name):
        sentences=str()
        edges=str()
        nodes=default_nodes
        progress=0
        searchCnt=0
        nodesToHide=str()
        for  gene in genes:
            gene=gene.replace("-"," ")
            # report progress immediately
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            #addiction terms must present with at least one drug
            addiction=undic(addiction_d) +") AND ("+undic(drug_d)
            sent0=gene_category(gene, addiction_d, addiction, "addiction")
            e0=generate_edges(sent0, tf_name)
            #  
            drug=undic(drug_d)
            sent1=gene_category(gene, drug_d, drug, "drug")
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e1=generate_edges(sent1, tf_name)
            #
            function=undic(function_d)
            sent2=gene_category(gene, function_d, function, "function")
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e2=generate_edges(sent2, tf_name)
            # brain has its own query terms that does not include the many short acronyms
            sent3=gene_category(gene, brain_d, brain_query_term, "brain")
            progress+=percent
            e3=generate_edges(sent3, tf_name)
            # gwas
            e4=searchArchived('gwas', gene)
            geneEdges=e0+e1+e2+e3+e4
            ## there is a bug here. zero link notes are not excluded anymore
            if len(geneEdges) >1:
                edges+=geneEdges
                nodes+="{ data: { id: '" + gene +  "', nodecolor:'#E74C3C', fontweight:700, url:'/startGeneGene?forTopGene="+gene+"'} },\n"
            else:
                nodesToHide+=gene +  " "
            sentences+=sent0+sent1+sent2+sent3
            #save data before the last yield
            searchCnt+=1
            if (searchCnt==len(genes)):
                progress=100
                sntdata.write(sentences)
                sntdata.close()
                cysdata.write(nodes+edges)
                cysdata.close()
                zeroLinkNode.write(nodesToHide)
                zeroLinkNode.close()
            yield "data:"+str(progress)+"\n\n"
    return Response(generate(genes, snt_file), mimetype='text/event-stream')

@app.route('/cytoscape')
def cytoscape():
    message2="<b> This  <i>Genes vs Keywords</i> graph is interactive: </b><li>Click on a line to see the indicated number of sentences <li> Click on a gene to search its relations with top 200 addiction genes<li>Click on a keyword to see the terms included in the search<li>Hover your pointer over a node will hide other links <li>Nodes can be moved around for better visibility, reload the page will restore the original layout<p>"
    with open(session['path']+"_cy","r") as f:
        elements=f.read()
    with open(session['path']+"_0link","r") as z:
        zeroLink=z.read()
        if (len(zeroLink)>0):
            message2+="<span style=\"color:darkred;\">No result was found for these genes: " + zeroLink + "</span>"
    return render_template('cytoscape.html', elements=elements, message2=message2)

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
           if (gene.upper() == gene0.upper() and cat.upper() == cat0.upper()) :
               out+= "<li> "+ text + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid +"\" target=_new>PMID:"+pmid+"<br></a>"
    return render_template('sentences.html', sentences="<ol>"+out+"</ol><p>")

## show the cytoscape graph for one gene from the top gene list
@app.route("/showTopGene")
def showTopGene():
    query=request.args.get('topGene')
    nodesEdges=searchArchived('topGene',query)
    message2="<li><strong>"+query + "</strong> is one of the top addiction genes. <li> An archived search is shown. Click on the blue circle to update the results and include keywords for brain region and gene function. <strong> The update may take a long time to finish.</strong> "
    return render_template("cytoscape.html", elements=nodesEdges, message="Top addiction genes", message2=message2)

@app.route("/shownode")
def shownode():
    node=request.args.get('node')
    allnodes={**brain_d, **drug_d, **function_d, **addiction_d}
    out="<p>"+node.upper()+"<hr><li>"+ allnodes[node].replace("|", "<li>")
    return render_template('sentences.html', sentences=out+"<p>")

@app.route("/startGeneGene")
def startGeneGene():
    session['forTopGene']=request.args.get('forTopGene')
    return render_template('progress.html', url_in="searchGeneGene", url_out="showGeneTopGene")

@app.route("/searchGeneGene")
def gene_gene():
    tmp_ggPMID=session['path']+"_ggPMID"
    gg_file=session['path']+"_ggSent" #gene_gene
    result_file=session['path']+"_ggResult"
    def generate(query):
        progress=1
        yield "data:"+str(progress)+"\n\n"
        os.system("esearch -db pubmed -query \"" +  query + "\" | efetch -format uid |sort >" + tmp_ggPMID)
        abstracts=os.popen("comm -1 -2 topGene_uniq.pmid " + tmp_ggPMID + " |fetch-pubmed -path "+pubmed_path+ " | xtract -pattern PubmedArticle -element MedlineCitation/PMID,ArticleTitle,AbstractText|sed \"s/-/ /g\"").read()
        os.system("rm "+tmp_ggPMID)
        progress=10
        yield "data:"+str(progress)+"\n\n"
        topGenes=dict()
        out=str()
        hitGenes=dict()
        with open("topGene_symb_alias.txt", "r") as top_f:
            for line in top_f:
                (symb, alias)=line.strip().split("\t")
                topGenes[symb]=alias.replace("; ","|")
        allAbstracts= abstracts.split("\n")
        abstractCnt=len(allAbstracts)
        rowCnt=0
        for row in allAbstracts:
            rowCnt+=1
            if rowCnt/10==int(rowCnt/10):
                progress=10+round(rowCnt/abstractCnt,2)*80
                yield "data:"+str(progress)+"\n\n"
            tiab=row.split("\t")
            pmid = tiab.pop(0)
            tiab= " ".join(tiab)
            sentences = sent_tokenize(tiab)
            ## keep the sentence only if it contains the gene 
            for sent in sentences:
                if findWholeWord(query)(sent):
                    sent=re.sub(r'\b(%s)\b' % query, r'<strong>\1</strong>', sent, flags=re.I)
                    for symb in topGenes:
                        allNames=symb+"|"+topGenes[symb]
                        if findWholeWord(allNames)(sent) :
                            sent=sent.replace("<b>","").replace("</b>","")
                            sent=re.sub(r'\b(%s)\b' % allNames, r'<b>\1</b>', sent, flags=re.I)
                            out+=query+"\t"+"gene\t" + symb+"\t"+pmid+"\t"+sent+"\n"
                            if symb in hitGenes.keys():
                                hitGenes[symb]+=1
                            else:
                                hitGenes[symb]=1
        progress=95
        yield "data:"+str(progress)+"\n\n"
        with open(gg_file, "w+") as gg:
            gg.write(out)
            gg.close()
        results="<h4>"+query+" vs top addiction genes</h4> Click on the number of sentences will show those sentences. Click on the <span style=\"background-color:#FcF3cf\">top addiction genes</span> will show an archived search for that gene.<hr>"
        topGeneHits={}
        for key in hitGenes.keys():
            url=gg_file+"|"+query+"|"+key
            if hitGenes[key]==1:
                sentword="sentence"
            else:
                sentword="sentences"
            topGeneHits[ "<li> <a href=/sentences?edgeID=" + url+ " target=_new>" + "Show " + str(hitGenes[key]) + " " + sentword +" </a> about "+query+" and <a href=/showTopGene?topGene="+key+" target=_gene><span style=\"background-color:#FcF3cf\">"+key+"</span></a>" ]=hitGenes[key]
        topSorted = [(k, topGeneHits[k]) for k in sorted(topGeneHits, key=topGeneHits.get, reverse=True)]
        for k,v in topSorted:
            results+=k
        saveResult=open(result_file, "w+")
        saveResult.write(results)
        saveResult.close()
        progress=100
        yield "data:"+str(progress)+"\n\n"
    ## start the run
    query=session['forTopGene']
    return Response(generate(query), mimetype='text/event-stream')

@app.route('/showGeneTopGene')
def showGeneTopGene ():
    with open(session['path']+"_ggResult", "r") as result_f:
        results=result_f.read()
    return render_template('sentences.html', sentences=results+"<p><br>")

## generate a page that lists all the top 150 addiction genes with links to cytoscape graph.
@app.route("/allTopGenes")
def top150genes():
    return render_template("topAddictionGene.html")

if __name__ == '__main__':
    app.run(debug=True, port=4200)
