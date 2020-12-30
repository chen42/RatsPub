#!/bin/env  python3
from flask import Flask, render_template, request, session, Response, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import json
import shutil
from flask import jsonify
from datetime import datetime
import bcrypt
import hashlib
import tempfile
import random
import string
from ratspub import *
import time
import os
import re
import pytz

from os import listdir
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from collections import Counter
import numpy as np
from numpy import array
import tensorflow
import tensorflow.keras
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.layers import *
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Embedding
from tensorflow.keras import metrics
from tensorflow.keras import optimizers
import pickle

app=Flask(__name__)
#datadir="/export/ratspub/"
datadir = "."
app.config['SECRET_KEY'] = '#DtfrL98G5t1dC*4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+datadir+'userspub.sqlite'
db = SQLAlchemy(app)
nltk.data.path.append("./nlp/")

# the sqlite database
class users(db.Model):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

def clean_doc(doc, vocab):
    doc = doc.lower()
    tokens = doc.split()
    re_punc = re.compile('[%s]' % re.escape(string.punctuation))    
    tokens = [re_punc.sub('' , w) for w in tokens]    
    tokens = [word for word in tokens if len(word) > 1]
    stop_words = set(stopwords.words('english'))
    tokens = [w for w in tokens if not w in stop_words]
    porter = PorterStemmer()
    stemmed = [porter.stem(word) for word in tokens]
    return tokens

# load tokenizer
with open('./nlp/tokenizer.pickle', 'rb') as handle:
    tokenizer = pickle.load(handle)

# load vocabulary
with open('./nlp/vocabulary.txt', 'r') as vocab:
    vocab = vocab.read()

def tf_auc_score(y_true, y_pred):
    return tensorflow.metrics.auc(y_true, y_pred)[1]

from tensorflow.keras import backend as K
K.clear_session()

# create the CNN model
def create_model(vocab_size, max_length):
    model = Sequential()
    model.add(Embedding(vocab_size, 32, input_length=max_length))
    model.add(Conv1D(filters=16, kernel_size=4, activation='relu'))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(10, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    opt = tensorflow.keras.optimizers.Adamax(lr=0.002, beta_1=0.9, beta_2=0.999)
    model.compile(loss='binary_crossentropy', optimizer=opt, metrics=[tf_auc_score])
    return model

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/login", methods=["POST", "GET"])
def login():
    email = None
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        found_user = users.query.filter_by(email=email).first()
        if (found_user and (bcrypt.checkpw(password.encode('utf8'), found_user.password))):
            session['email'] = found_user.email
            print(bcrypt.hashpw(session['email'].encode('utf8'), bcrypt.gensalt()))
            session['hashed_email'] = hashlib.md5(session['email'] .encode('utf-8')).hexdigest()
            session['name'] = found_user.name
            session['id'] = found_user.id
        else:
            flash("Invalid username or password!", "loginout")
            return render_template('signup.html')
    flash("Login Succesful!", "loginout")
    return render_template('index.html')

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        found_user = users.query.filter_by(email=email).first()
        if (found_user and (bcrypt.checkpw(password.encode('utf8'), found_user.password)==False)):
            flash("Already registered, but wrong password!", "loginout")
            return render_template('signup.html')        
        session['email'] = email
        session['hashed_email'] = hashlib.md5(session['email'] .encode('utf-8')).hexdigest()
        session['name'] = name
        password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        user = users(name=name, email=email, password = password)       
        if found_user:
            session['email'] = found_user.email
            session['hashed_email'] = hashlib.md5(session['email'] .encode('utf-8')).hexdigest()
            session['id'] = found_user.id
            found_user.name = name
            db.session.commit()
        else:
            db.session.add(user)
            db.session.commit()
            newuser = users.query.filter_by(email=session['email']).first()
            session['id'] = newuser.id
        flash("Login Succesful!", "loginout")
        return render_template('index.html')
    else:
        if 'email' in session:
            flash("Already Logged In!")
            return render_template('index.html')
        return render_template('signup.html')

@app.route("/signin", methods=["POST", "GET"])
def signin():
    email = None
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        found_user = users.query.filter_by(email=email).first()
        if (found_user and (bcrypt.checkpw(password.encode('utf8'), found_user.password))):
            session['email'] = found_user.email
            session['hashed_email'] = hashlib.md5(session['email'] .encode('utf-8')).hexdigest()
            session['name'] = found_user.name
            session['id'] = found_user.id
            flash("Login Succesful!", "loginout")
            return render_template('index.html')
        else:
            flash("Invalid username or password!", "loginout")
            return render_template('signup.html')   
    return render_template('signin.html')

# change password 
@app.route("/<nm_passwd>", methods=["POST", "GET"])
def profile(nm_passwd):
    try:
        if "_" in str(nm_passwd):
            user_name = str(nm_passwd).split("_")[0]
            user_passwd = str(nm_passwd).split("_")[1]
            user_passwd = "b\'"+user_passwd+"\'"
            found_user = users.query.filter_by(name=user_name).first()
            if request.method == "POST":
                password = request.form['password']
                session['email'] = found_user.email
                session['hashed_email'] = hashlib.md5(session['email'] .encode('utf-8')).hexdigest()
                session['name'] = found_user.name
                session['id'] = found_user.id
                password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
                found_user.password = password
                db.session.commit()
                flash("Your password is changed!", "loginout")
                return render_template('index.html')
            # remove reserved characters from the hashed passwords
            reserved = (";", "/", "?", ":", "@", "=", "&", ".")
            def replace_reserved(fullstring):
                for replace_str in reserved:
                    fullstring = fullstring.replace(replace_str,"")
                return fullstring
            replaced_passwd = replace_reserved(str(found_user.password))
            if replaced_passwd == user_passwd:
                return render_template("/passwd_change.html", name=user_name)
            else:
                return "This url does not exist"
        else: 
            return "This url does not exist"
    except (AttributeError):
        return "This url does not exist"

@app.route("/logout")
def logout():
    if 'email' in session:
        global user1
        if session['name'] != '':
            user1 = session['name']
        else: 
            user1 = session['email']
    flash("You have been logged out, {user1}", "loginout")
    session.pop('email', None)
    session.clear()
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route('/progress')
def progress():
    #get the type from checkbox
    search_type = request.args.getlist('type')
    if (search_type == []):
        search_type = ['GWAS', 'function', 'addiction', 'drug', 'brain', 'stress', 'psychiatric', 'cell']
    session['search_type'] = search_type
    # only 1-100 terms are allowed
    genes=request.args.get('query')
    genes=genes.replace(",", " ")
    genes=genes.replace(";", " ")
    genes=re.sub(r'\bLOC\d*?\b', "", genes, flags=re.I)
    genes=genes.replace(" \'", " \"")
    genes=genes.replace("\' ", "\" ")
    genes=genes.replace("\'", "-")
    genes1 = [f[1:-1] for f in re.findall('".+?"', genes)]
    genes2 = [p for p in re.findall(r'([^""]+)',genes) if p not in genes1]
    genes2_str = ''.join(genes2)
    genes2 = genes2_str.split()
    genes3 = genes1 + genes2
    genes = [re.sub("\s+", '-', s) for s in genes3]

    #if len(genes)>=30:
    #    message="<span class='text-danger'>Up to 30 terms can be searched at a time</span>"
    #    return render_template('index.html', message=message)
    if len(genes)==0:
        message="<span class='text-danger'>Please enter a search term </span>"
        return render_template('index.html', message=message)
    tf_path=tempfile.gettempdir()
    #tf_path = "/tmp/"

    genes_for_folder_name =""
    if len(genes) == 1:
        marker = ""
        genes_for_folder_name =str(genes[0])
    elif len(genes) == 2:
        marker = ""
        genes_for_folder_name =str(genes[0])+"_"+str(genes[1])
    elif len(genes) == 3:
        marker = ""
        genes_for_folder_name =str(genes[0])+"_"+str(genes[1])+"_"+str(genes[2])
    else:
        genes_for_folder_name =str(genes[0])+"_"+str(genes[1])+"_"+str(genes[2])
        marker="_m"

    # generate a unique session ID depending on timestamp to track the results 
    timestamp = datetime.utcnow().replace(microsecond=0)
    timestamp = timestamp.replace(tzinfo=pytz.utc)
    timestamp = timestamp.astimezone(pytz.timezone("America/Chicago"))
    timeextension = str(timestamp)
    timeextension = timeextension.replace(':', '_')
    timeextension = timeextension.replace('-', '_')
    timeextension = timeextension.replace(' ', '_')
    timeextension = timeextension.replace('_06_00', '')
    session['timeextension'] = timeextension
    user_login=0
    #create a folder for the search
    if ('email' in session):
        os.makedirs(datadir + "/user/"+str(session['hashed_email'])+"/"+str(timeextension)+"_0_"+genes_for_folder_name+marker,exist_ok=True)
        session['user_folder'] = datadir+"/user/"+str(session['hashed_email'])
        session['path_user'] = datadir+"/user/"+str(session['hashed_email'])+"/"+str(timeextension)+"_0_"+genes_for_folder_name+marker+"/"
        session['rnd'] = timeextension+"_0_"+genes_for_folder_name+marker
        rnd = session['rnd']
    else:
        rnd = "tmp" + ''.join(random.choice(string.ascii_letters) for x in range(6)) 
        session['path']=tf_path+ "/" + rnd
        #os.makedirs(datadir+ session['path'])
        os.makedirs(session['path'])
    
    genes_session = ''
    for gen in genes:
        genes_session += str(gen) + "_"
    genes_session = genes_session[:-1]
    session['query']=genes

    return render_template('progress.html', url_in="search", url_out="cytoscape?rnd="+rnd+"&genequery="+genes_session)

@app.route("/search")
def search():
    genes=session['query']
    timeextension=session['timeextension']
    percent=round(100/(len(genes)*6),1) # 6 categories 
    if ('email' in session):
        sessionpath = session['path_user'] + timeextension
        path_user=session['path_user']
        user_login=1
    else:
        user_login=0
        sessionpath = session['path']
        #path_user=datadir+session['path']+"/"
        path_user=session['path']+"/"

    snt_file=sessionpath+"_snt"
    cysdata=open(sessionpath+"_cy","w+")
    sntdata=open(snt_file,"w+")
    zeroLinkNode=open(sessionpath+"_0link","w+")
    search_type = session['search_type']
    #consider the types got from checkbox
    temp_nodes = ""
    json_nodes = "{\"data\":["
    if ("function" in search_type):
        temp_nodes += n0
        json_nodes += nj0
    if ("addiction" in search_type):
        temp_nodes += n1   
        json_nodes += nj1    
    if ("drug" in search_type):
        temp_nodes += n2
        json_nodes += nj2
    if ("brain" in search_type):
        temp_nodes += n3
        json_nodes += nj3
    if ("stress" in search_type):
        temp_nodes += n4
        json_nodes += nj4
    if ("psychiatric" in search_type):
        temp_nodes += n5  
        json_nodes += nj5   
    if ("cell" in search_type):
        temp_nodes += n6  
        json_nodes += nj6   
    if ("GWAS" in search_type):
        temp_nodes += n7  
        json_nodes += nj7
    json_nodes = json_nodes[:-2]
    json_nodes =json_nodes+"]}"

    def generate(genes, tf_name):
        with app.test_request_context():
            sentences=str()
            edges=str()
            nodes = temp_nodes
            progress=0
            searchCnt=0
            nodesToHide=str()
            json_edges = str()
            
            genes_or = ' or '.join(genes)
            all_d=undic(addiction_d) +"|"+undic(drug_d)+"|"+undic(function_d)+"|"+undic(brain_d)+"|"+undic(stress_d)+"|"+undic(psychiatric_d)+"|"+undic(cell_d)
            #print(all_d)
            abstracts_raw = getabstracts(genes_or,all_d)

            sentences_ls=[]
            for row in abstracts_raw.split("\n"):
                tiab=row.split("\t")
                #print(tiab)
                pmid = tiab.pop(0)
                tiab= " ".join(tiab)
                sentences_tok = sent_tokenize(tiab)
                for sent_tok in sentences_tok:
                    sent_tok = pmid + ' ' + sent_tok
                    sentences_ls.append(sent_tok)

            for gene in genes:
                gene=gene.replace("-"," ")
                # report progress immediately
                progress+=percent
                yield "data:"+str(progress)+"\n\n"
                #addiction terms must present with at least one drug
                addiction=undic(addiction_d) +") AND ("+undic(drug_d)
                sent0=gene_category(gene, addiction_d, addiction, "addiction", sentences_ls)
                #print(sent0)
                e0=generate_edges(sent0, tf_name)
                ej0=generate_edges_json(sent0, tf_name)
                # drug
                drug=undic(drug_d)
                sent1=gene_category(gene, drug_d, drug, "drug", sentences_ls)
                progress+=percent
                yield "data:"+str(progress)+"\n\n"
                e1=generate_edges(sent1, tf_name)
                ej1=generate_edges_json(sent1, tf_name)
                # function
                function=undic(function_d)
                sent2=gene_category(gene, function_d, function, "function", sentences_ls)
                progress+=percent
                yield "data:"+str(progress)+"\n\n"
                e2=generate_edges(sent2, tf_name)
                ej2=generate_edges_json(sent2, tf_name)
                # brain has its own query terms that does not include the many short acronyms
                brain = undic(brain_d)
                sent3=gene_category(gene, brain_d, brain, "brain", sentences_ls)
                progress+=percent
                e3=generate_edges(sent3, tf_name)
                ej3=generate_edges_json(sent3, tf_name)
                # stress
                stress=undic(stress_d)
                sent4=gene_category(gene, stress_d, stress, "stress", sentences_ls)
                progress+=percent
                yield "data:"+str(progress)+"\n\n"
                e4=generate_edges(sent4, tf_name)
                ej4=generate_edges_json(sent4, tf_name)
                # psychiatric 
                psychiatric=undic(psychiatric_d)
                sent5=gene_category(gene, psychiatric_d, psychiatric, "psychiatric", sentences_ls)
                progress+=percent
                yield "data:"+str(progress)+"\n\n"
                e5=generate_edges(sent5, tf_name)
                ej5=generate_edges_json(sent5, tf_name)
                # cell 
                cell=undic(cell_d)
                sent6=gene_category(gene, cell_d, cell, "cell", sentences_ls)
                progress+=percent
                yield "data:"+str(progress)+"\n\n"
                e6=generate_edges(sent6, tf_name)
                ej6=generate_edges_json(sent6, tf_name)
                # GWAS
                e7=searchArchived('GWAS', gene, 'cys')
                ej7=searchArchived('GWAS', gene , 'json')
                #consider the types got from checkbox
                geneEdges = ""
                if ("addiction" in search_type):
                    geneEdges += e0
                    json_edges += ej0
                if ("drug" in search_type):
                    geneEdges += e1   
                    json_edges += ej1    
                if ("function" in search_type):
                    geneEdges += e2
                    json_edges += ej2
                if ("brain" in search_type):
                    geneEdges += e3
                    json_edges += ej3
                if ("stress" in search_type):
                    geneEdges += e4
                    json_edges += ej4
                if ("psychiatric" in search_type):
                    geneEdges += e5  
                    json_edges += ej5  
                if ("cell" in search_type):
                    geneEdges += e6  
                    json_edges += ej6  
                if ("GWAS" in search_type):
                    geneEdges += e7  
                    json_edges += ej7                           
                if len(geneEdges) >1:
                    edges+=geneEdges
                    nodes+="{ data: { id: '" + gene +  "', nodecolor:'#E74C3C', fontweight:700, url:'/synonyms?node="+gene+"'} },\n"
                else:
                    nodesToHide+=gene +  " "
                sentences+=sent0+sent1+sent2+sent3+sent4+sent5+sent6
                sent0=None 
                sent1=None
                sent2=None
                sent3=None
                sent4=None
                sent5=None
                sent6=None
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
            #edges in json format
            json_edges="{\"data\":["+json_edges
            json_edges = json_edges[:-2]
            json_edges =json_edges+"]}"
            #write edges to txt file in json format also in user folder
            with open(path_user+"edges.json", "w") as temp_file_edges:
                temp_file_edges.write(json_edges) 
    with open(path_user+"nodes.json", "w") as temp_file_nodes:
        temp_file_nodes.write(json_nodes)
    return Response(generate(genes, snt_file), mimetype='text/event-stream')

@app.route("/tableview/")
def tableview():
    genes_url=request.args.get('genequery')
    rnd_url=request.args.get('rnd')
    tf_path=tempfile.gettempdir()
    if ('email' in session):
        filename = rnd_url.split("_0_")[0]
        genes_session_tmp = datadir+"/user/"+str(session['hashed_email'])+"/"+rnd_url+"/"+filename
        gene_url_tmp = "/user/"+str(session['hashed_email'])+"/"+rnd_url
        try:
            with open(datadir+gene_url_tmp+"/nodes.json") as jsonfile:
                jnodes = json.load(jsonfile)
        except FileNotFoundError:
            flash("You logged out!")
            return render_template('index.html')
        jedges =''
        file_edges = open(datadir+gene_url_tmp +'/edges.json', 'r')
        for line in file_edges.readlines():
            if ':' not in line:
                nodata_temp = 1
            else: 
                nodata_temp = 0
                with open(datadir+gene_url_tmp +"/edges.json") as edgesjsonfile:
                    jedges = json.load(edgesjsonfile)
                break
    else:
        genes_session_tmp=tf_path+"/"+rnd_url
        gene_url_tmp = genes_session_tmp
        try:
            with open(gene_url_tmp+"/nodes.json") as jsonfile:
                jnodes = json.load(jsonfile)
        except FileNotFoundError:
            flash("You logged out!")
            return render_template('index.html')
        jedges =''
        file_edges = open(gene_url_tmp +'/edges.json', 'r')
        for line in file_edges.readlines():
            if ':' not in line:
                nodata_temp = 1
            else: 
                nodata_temp = 0
                with open(gene_url_tmp +"/edges.json") as edgesjsonfile:
                    jedges = json.load(edgesjsonfile)
                break
    genename=genes_url.split("_")
    if len(genename)>3:
        genename = genename[0:3]
        added = ",..."
    else:
        added = ""
    gene_name = str(genename)[1:]
    gene_name=gene_name[:-1]
    gene_name=gene_name.replace("'","")
    gene_name = gene_name+added
    num_gene = gene_name.count(',')+1

    message3="<b> Actions: </b><li> <font color=\"#E74C3C\">Click on the abstract count to read sentences linking the keyword and the gene</font> <li> Click on a gene to search its relations with top 200 addiction genes. <li> Click on a keyword to see the terms included in the search. <li>View the results in <a href='\\cytoscape/?rnd={}&genequery={}'\ ><b> a graph.</b></a>".format(rnd_url,genes_url)
    return render_template('tableview.html', genes_session_tmp = genes_session_tmp, nodata_temp=nodata_temp, num_gene=num_gene, jedges=jedges, jnodes=jnodes,gene_name=gene_name, message3=message3, rnd_url=rnd_url, genes_url=genes_url)

@app.route("/tableview0/")
def tableview0():
    genes_url=request.args.get('genequery')
    rnd_url=request.args.get('rnd')
    tf_path=tempfile.gettempdir()
    if ('email' in session):
        filename = rnd_url.split("_0_")[0]
        genes_session_tmp = datadir+"/user/"+str(session['hashed_email'])+"/"+rnd_url+"/"+filename
        gene_url_tmp = "/user/"+str(session['hashed_email'])+"/"+rnd_url
        try:
            with open(datadir+gene_url_tmp+"/nodes.json") as jsonfile:
                jnodes = json.load(jsonfile)
        except FileNotFoundError:
            flash("You logged out!")
            return render_template('index.html')
        jedges =''
        file_edges = open(datadir+gene_url_tmp+'/edges.json', 'r')
        for line in file_edges.readlines():
            if ':' not in line:
                nodata_temp = 1
            else: 
                nodata_temp = 0
                with open(datadir+gene_url_tmp+"/edges.json") as edgesjsonfile:
                    jedges = json.load(edgesjsonfile)
                break
    else:
        genes_session_tmp=tf_path+"/"+rnd_url
        gene_url_tmp = genes_session_tmp
        try:
            with open(gene_url_tmp+"/nodes.json") as jsonfile:
                jnodes = json.load(jsonfile)
        except FileNotFoundError:
            flash("You logged out!")
            return render_template('index.html')
        jedges =''
        file_edges = open(gene_url_tmp+'/edges.json', 'r')
        for line in file_edges.readlines():
            if ':' not in line:
                nodata_temp = 1
            else: 
                nodata_temp = 0
                with open(gene_url_tmp+"/edges.json") as edgesjsonfile:
                    jedges = json.load(edgesjsonfile)
                break
    genes_url=request.args.get('genequery')
    genename=genes_url.split("_")
    if len(genename)>3:
        genename = genename[0:3]
        added = ",..."
    else:
        added = ""
    gene_name = str(genename)[1:]
    gene_name=gene_name[:-1]
    gene_name=gene_name.replace("'","")
    gene_name = gene_name+added
    num_gene = gene_name.count(',')+1
    message4="<b> Notes: </b><li> These are the keywords that have <b>zero</b> abstract counts. <li>View all the results in <a href='\\cytoscape/?rnd={}&genequery={}'><b> a graph.</b></a>".format(rnd_url,genes_url)
    return render_template('tableview0.html',nodata_temp=nodata_temp, num_gene=num_gene, jedges=jedges, jnodes=jnodes,gene_name=gene_name, message4=message4)

@app.route("/userarchive")
def userarchive():
    if ('email' in session):
        if os.path.exists(datadir+"/user/"+str(session['hashed_email'])) == False:
            flash("Search history doesn't exist!")
            return render_template('index.html')
        else:
            session['user_folder'] = datadir+"/user/"+str(session['hashed_email'])
    else:
        flash("You logged out!")
        return render_template('index.html')
    session_id=session['id']
    def sorted_alphanumeric(data):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
        return sorted(data, key=alphanum_key)
    dirlist = sorted_alphanumeric(os.listdir(session['user_folder']))  
    folder_list = []
    directory_list = []
    gene_list=[]
    for filename in dirlist:
        folder_list.append(filename)
        gene_name = filename.split('_0_')[1]
        if gene_name[-2:] == '_m':
            gene_name = gene_name[:-2]
            gene_name = gene_name + ", ..."
        gene_name = gene_name.replace('_', ', ')
        gene_list.append(gene_name)
        gene_name=""
        filename=filename[0:4]+"-"+filename[5:7]+"-"+filename[8:13]+":"+filename[14:16]+":"+filename[17:19]
        directory_list.append(filename)
    len_dir = len(directory_list)
    message3="<b> Actions: </b><li> Click on the Date/Time to view archived results.  <li>The Date/Time are based on US Central time zone. "
    return render_template('userarchive.html', len_dir=len_dir, gene_list = gene_list, folder_list=folder_list, directory_list=directory_list, session_id=session_id, message3=message3)

# delete this search
@app.route('/remove', methods=['GET', 'POST'])
def remove():
    if('email' in session):
        remove_folder = request.args.get('remove_folder')
        shutil.rmtree(datadir+"/user/"+str(session['hashed_email']+"/"+remove_folder), ignore_errors=True)
        return redirect(url_for('userarchive'))
    else:
        flash("You logged out!")
        return render_template('index.html')

@app.route('/date', methods=['GET', 'POST'])
def date():
    select_date = request.args.get('selected_date')
    #open the cache folder for the user
    tf_path=datadir+"/user"
    if ('email' in session):
        time_extension = str(select_date)
        time_extension = time_extension.split('_0_')[0]
        gene_name1 = str(select_date).split('_0_')[1]
        time_extension = time_extension.replace(':', '_')
        time_extension = time_extension.replace('-', '_')
        session['user_folder'] = tf_path+"/"+str(session['hashed_email'])
        genes_session_tmp = tf_path+"/"+str(session['hashed_email'])+"/"+select_date+"/"+time_extension
        with open(tf_path+"/"+str(session['hashed_email'])+"/"+select_date+"/nodes.json", "r") as jsonfile:
            jnodes = json.load(jsonfile)
        jedges =''
        file_edges = open(tf_path+"/"+str(session['hashed_email'])+"/"+select_date+"/edges.json", "r")
        for line in file_edges.readlines():
            if ':' not in line:
                nodata_temp = 1
            else: 
                nodata_temp = 0
                with open(tf_path+"/"+str(session['hashed_email'])+"/"+select_date+"/edges.json", "r") as edgesjsonfile:
                    jedges = json.load(edgesjsonfile)
                break
        gene_list_all=[]
        gene_list=[]
        if nodata_temp == 0:
            for p in jedges['data']:
                if p['source'] not in gene_list:
                    gene_list_all.append(p['source'])
                    gene_list.append(p['source'])
            if len(gene_list)>3:
                gene_list = gene_list[0:3]
                added = ",..."
            else:
                added = ""
            gene_name = str(gene_list)[1:]
            gene_name=gene_name[:-1]
            gene_name=gene_name.replace("'","")
            gene_name = gene_name+added
            num_gene = gene_name.count(',')+1
        else: 
            gene_name1 = gene_name1.replace("_", ", ")
            gene_name = gene_name1
            num_gene = gene_name1.count(',')+1
            for i in range(0,num_gene):
                gene_list.append(gene_name1.split(',')[i])
        genes_session = ''
        for gen in gene_list_all:
            genes_session += str(gen) + "_"
        genes_session = genes_session[:-1]
    else:
        flash("You logged out!")
        return render_template('index.html')
    message3="<b> Actions: </b><li> <font color=\"#E74C3C\">Click on the abstract count to read sentences linking the keyword and the gene</font> <li> Click on a gene to search its relations with top 200 addiction genes. <li> Click on a keyword to see the terms included in the search. <li>View the results in <a href='\\cytoscape/?rnd={}&genequery={}'\ ><b> a graph.</b></a>".format(select_date,genes_session)
    return render_template('tableview.html',nodata_temp=nodata_temp, num_gene=num_gene,genes_session_tmp = genes_session_tmp, rnd_url=select_date ,jedges=jedges, jnodes=jnodes,gene_name=gene_name, genes_url=genes_session, message3=message3)

@app.route('/cytoscape/')
def cytoscape():
    genes_url=request.args.get('genequery')
    rnd_url=request.args.get('rnd')
    tf_path=tempfile.gettempdir()
    genes_session_tmp=tf_path + "/" + genes_url

    message2="<b> Actions: </b><li><font color=\"#E74C3C\">Click on a line to see the indicated number of abstracts </font> <li> Click on a gene to search its relations with top 200 addiction genes<li>Click on a keyword to see the terms included in the search<li>Hover your pointer over a node to hide other links <li>Move nodes around to adjust visibility, reload the page to restore the default layout<li>View the results in <a href='\\tableview/?rnd={}&genequery={}'\ ><b>a table. </b></a> <li>All results will appear in a new Browser window (or tab)".format(rnd_url,genes_url)
    if ('email' in session):
        filename = rnd_url.split("_0_")[0]
        rnd_url_tmp = datadir+"/user/"+str(session['hashed_email'])+"/"+rnd_url+"/"+filename
        try:
            with open(rnd_url_tmp+"_cy","r") as f:
                elements=f.read()
        except FileNotFoundError:
            flash("You logged out!")
            return render_template('index.html')
        with open(rnd_url_tmp+"_0link","r") as z:
            zeroLink=z.read()
            if (len(zeroLink)>0):
                message2+="<span style=\"color:darkred;\">No result was found for these genes: " + zeroLink + "</span>"
    else:
        rnd_url_tmp=tf_path +"/" + rnd_url
        try:
            with open(rnd_url_tmp+"_cy","r") as f:
                elements=f.read()
        except FileNotFoundError:
            flash("You logged out!")
            return render_template('index.html')
        with open(rnd_url_tmp+"_0link","r") as z:
            zeroLink=z.read()
            if (len(zeroLink)>0):
                message2+="<span style=\"color:darkred;\">No result was found for these genes: " + zeroLink + "</span>"
    return render_template('cytoscape.html', elements=elements, message2=message2)

@app.route("/sentences")
def sentences():
    def predict_sent(sent_for_pred):
        max_length = 64
        tokens = clean_doc(sent_for_pred, vocab)
        tokens = [w for w in tokens if w in vocab]
        # convert to line
        line = ' '.join(tokens)
        line = [line]
        tokenized_sent = tokenizer.texts_to_sequences(line)
        tokenized_sent = pad_sequences(tokenized_sent, maxlen=max_length, padding='post') 
        predict_sent = model.predict(tokenized_sent, verbose=0)
        percent_sent = predict_sent[0,0]
        if round(percent_sent) == 0:
            return 'neg'
        else:
            return 'pos'
    pmid_list=[]
    pmid_string=''
    edge=request.args.get('edgeID')
    (tf_name, gene0, cat0)=edge.split("|")
    if(cat0=='stress'):
        model = create_model(23154, 64)
        model.load_weights("./nlp/weights.ckpt")
    out3=""
    out_pos = ""
    out_neg = ""
    num_abstract = 0
    stress_cellular = "<br><br><br>"+"</ol><b>Sentence(s) describing celluar stress (classified using a deep learning model):</b><hr><ol>"
    stress_systemic = "<b></ol>Sentence(s) describing systemic stress (classified using a deep learning model):</b><hr><ol>"
    with open(tf_name, "r") as df:
        all_sents=df.read()
    for sent in all_sents.split("\n"):
        if len(sent.strip())!=0:
            (gene,nouse,cat, pmid, text)=sent.split("\t")
            if (gene.upper() == gene0.upper() and cat.upper() == cat0.upper()) :
                out3+= "<li> "+ text + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid +"\" target=_new>PMID:"+pmid+"<br></a>"
                num_abstract += 1
                if(pmid+cat0 not in pmid_list):
                    pmid_string = pmid_string + ' ' + pmid
                    pmid_list.append(pmid+cat0)
                if(cat0=='stress'):
                    out4 = predict_sent(text)
                    if(out4 == 'pos'):
                        out_pred_pos = "<li> "+ text + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid +"\" target=_new>PMID:"+pmid+"<br></a>"                    
                        out_pos += out_pred_pos
                    else:
                        out_pred_neg = "<li>"+ text + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid +"\" target=_new>PMID:"+pmid+"<br></a>"                    
                        out_neg += out_pred_neg
    out1="<h3>"+gene0 + " and " + cat0  + "</h3>\n"
    if len(pmid_list)>1:
        out2 = str(num_abstract) + ' sentences in ' + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid_string +"\" target=_new>"+ str(len(pmid_list)) + ' studies' +"<br></a>" + "<br><br>"
    else:
        out2 = str(num_abstract) + ' sentence(s) in '+ " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid_string +"\" target=_new>"+ str(len(pmid_list)) + ' study' +"<br></a>" "<br><br>"
    if(out_neg == "" and out_pos == ""):
        out= out1+ out2 +out3
    elif(out_pos != "" and out_neg!=""):
        out = out1 + out2 + stress_systemic+out_pos + stress_cellular + out_neg
    elif(out_pos != "" and out_neg ==""):
        out= out1+ out2 + stress_systemic + out_pos
    elif(out_neg != "" and out_pos == ""):
        out = out1 +out2+stress_cellular+out_neg
    K.clear_session()
    return render_template('sentences.html', sentences="<ol>"+out+"</ol><p>")
## show the cytoscape graph for one gene from the top gene list
@app.route("/showTopGene")
def showTopGene():
    query=request.args.get('topGene')
    nodesEdges=searchArchived('topGene',query, 'cys')
    message2="<li><strong>"+query + "</strong> is one of the top addiction genes. <li> An archived search is shown. Click on the blue circle to update the results and include keywords for brain region and gene function. <strong> The update may take a long time to finish.</strong> "
    return render_template("cytoscape.html", elements=nodesEdges, message="Top addiction genes", message2=message2)

@app.route("/shownode")
def shownode():
    node=request.args.get('node')
    allnodes={**brain_d, **drug_d, **function_d, **addiction_d, **stress_d, **psychiatric_d, **cell_d}
    out="<p>"+node.upper()+"<hr><li>"+ allnodes[node].replace("|", "<li>")
    return render_template('sentences.html', sentences=out+"<p>")

@app.route("/synonyms")
def synonyms():
    node=request.args.get('node')
    node=node.upper()
    allnodes={**genes}
    try:
        synonym_list = list(allnodes[node].split("|")) 
        session['synonym_list'] = synonym_list
        session['main_gene'] = node.upper()
        out="<hr><li>"+ allnodes[node].replace("|", "<li>")
        synonym_list_str = ';'.join([str(syn) for syn in synonym_list]) 
        synonym_list_str +=';' + node
        case = 1
        return render_template('genenames.html', case = case, gene = node.upper(), synonym_list = synonym_list, synonym_list_str=synonym_list_str)
    except:
        try:
         #if(node in session['synonym_list']):
            synonym_list = session['synonym_list']
            synonym_list_str = ';'.join([str(syn) for syn in synonym_list]) 
            synonym_list_str +=';' + node
            case = 1
            return render_template('genenames.html', case=case, gene = session['main_gene'] , synonym_list = synonym_list, synonym_list_str=synonym_list_str)
        except:
            case = 2
            return render_template('genenames.html', gene = node, case = case)

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
        #abstracts = os.popen("esearch -db pubmed -query " +  query + " | efetch -format uid |fetch-pubmed -path "+ pubmed_path + " | xtract -pattern PubmedArticle -element MedlineCitation/PMID,ArticleTitle,AbstractText|sed \"s/-/ /g\"").read()
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
            print(sentword)
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
    db.create_all()
    app.run(debug=True, port=4201)
