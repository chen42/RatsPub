#!/bin/env  python3
from flask import Flask, render_template, request, session, Response, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import json
import shutil
from flask import jsonify
from datetime import datetime
import bcrypt
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
import keras
from keras.models import Model
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers import *
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Embedding
from keras import metrics
from keras import optimizers
import pickle

app=Flask(__name__)
datadir="/export/ratspub/"
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

# create the CNN model
def create_model(vocab_size, max_length):
    model = Sequential()
    model.add(Embedding(vocab_size, 32, input_length=max_length))
    model.add(Conv1D(filters=16, kernel_size=4, activation='relu'))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(10, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    opt = keras.optimizers.Adamax(learning_rate=0.002, beta_1=0.9, beta_2=0.999)
    model.compile(loss='binary_crossentropy', optimizer=opt, metrics=[keras.metrics.AUC()])
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
        session['name'] = name
        password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        user = users(name=name, email=email, password = password)       
        if found_user:
            session['email'] = found_user.email
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
        search_type = ['GWAS', 'function', 'addiction', 'drug', 'brain', 'stress', 'psychiatric']
    session['search_type'] = search_type
    # only 1-100 terms are allowed
    genes=request.args.get('query')
    genes=genes.replace(",", " ")
    genes=genes.replace(";", " ")
    genes=re.sub(r'\bLOC\d*?\b', "", genes, flags=re.I)
    genes=genes.split()
    if len(genes)>=100:
        message="<span class='text-danger'>Up to 100 terms can be searched at a time</span>"
        return render_template('index.html', message=message)
    elif len(genes)==0:
        message="<span class='text-danger'>Please enter a search term </span>"
        return render_template('index.html', message=message)
    tf_path=tempfile.gettempdir()
    session['path']=tf_path+"/tmp" + ''.join(random.choice(string.ascii_letters) for x in range(6)) 
    # put the query in session cookie
    session['query']=genes 
    return render_template('progress.html', url_in="search", url_out="cytoscape")

@app.route("/search")
def search():
    genes=session['query']
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
    session['timestamp'] = timestamp    
    timeextension = str(timestamp)
    timeextension = timeextension.replace(':', '_')
    timeextension = timeextension.replace('-', '_')
    timeextension = timeextension.replace(' ', '_')
    timeextension = timeextension.replace('_06_00', '')
    user_login=0
    #create a folder for the search
    if ('email' in session):
        user_login=1
        os.makedirs(datadir+"user/"+str(session['email']+"/"+timeextension+"_0_"+genes_for_folder_name+marker),exist_ok=True)
        session['user_folder'] = datadir+"user/"+str(session['email'])
        user_folder=session['user_folder']
        session['path'] = datadir+"user/"+str(session['email'])+"/"+timeextension+"_0_"+genes_for_folder_name+marker+"/"+timeextension
    percent=round(100/(len(genes)*6),1) # 6 categories 
    snt_file=session['path']+"_snt"
    cysdata=open(session['path']+"_cy","w+")
    sntdata=open(snt_file,"w+")
    zeroLinkNode=open(session['path']+"_0link","w+")
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
    if ("GWAS" in search_type):
        temp_nodes += n6  
        json_nodes += nj6
    json_nodes = json_nodes[:-2]
    json_nodes =json_nodes+"]}"
    def generate(genes, tf_name):
        sentences=str()
        edges=str()
        nodes = temp_nodes
        progress=0
        searchCnt=0
        nodesToHide=str()
        json_edges = str()
        for gene in genes:
            gene=gene.replace("-"," ")
            # report progress immediately
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            #addiction terms must present with at least one drug
            addiction=undic(addiction_d) +") AND ("+undic(drug_d)
            sent0=gene_category(gene, addiction_d, addiction, "addiction")
            e0=generate_edges(sent0, tf_name)
            ej0=generate_edges_json(sent0, tf_name)
            # drug
            drug=undic(drug_d)
            sent1=gene_category(gene, drug_d, drug, "drug")
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e1=generate_edges(sent1, tf_name)
            ej1=generate_edges_json(sent1, tf_name)
            # function
            function=undic(function_d)
            sent2=gene_category(gene, function_d, function, "function")
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e2=generate_edges(sent2, tf_name)
            ej2=generate_edges_json(sent2, tf_name)
            # brain has its own query terms that does not include the many short acronyms
            sent3=gene_category(gene, brain_d, brain_query_term, "brain")
            progress+=percent
            e3=generate_edges(sent3, tf_name)
            ej3=generate_edges_json(sent3, tf_name)
            # stress
            stress=undic(stress_d)
            sent4=gene_category(gene, stress_d, stress, "stress")
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e4=generate_edges(sent4, tf_name)
            ej4=generate_edges_json(sent4, tf_name)
            # psychiatric 
            psychiatric=undic(psychiatric_d)
            sent5=gene_category(gene, psychiatric_d, psychiatric, "psychiatric")
            progress+=percent
            yield "data:"+str(progress)+"\n\n"
            e5=generate_edges(sent5, tf_name)
            ej5=generate_edges_json(sent5, tf_name)
            # GWAS
            e6=searchArchived('GWAS', gene, 'cys')
            ej6=searchArchived('GWAS', gene , 'json')
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
            if ("GWAS" in search_type):
                geneEdges += e6  
                json_edges += ej6                           
            ## there is a bug here. zero link notes are not excluded anymore
            if len(geneEdges) >1:
                edges+=geneEdges
                nodes+="{ data: { id: '" + gene +  "', nodecolor:'#E74C3C', fontweight:700, url:'/startGeneGene?forTopGene="+gene+"'} },\n"
            else:
                nodesToHide+=gene +  " "
            sentences+=sent0+sent1+sent2+sent3+sent4+sent5
            sent0=None 
            sent1=None
            sent2=None
            sent3=None
            sent4=None
            sent5=None
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
        #write edges to txt file in json format
        with open(datadir+"edges.json", 'w') as edgesjson:
            edgesjson.write(json_edges) 
        #write edges to txt file in json format also in user folder
        if (user_login == 1):
            with open(user_folder+"/"+timeextension+"_0_"+genes_for_folder_name+marker+"/edges.json", "w") as temp_file_edges:
                temp_file_edges.write(json_edges)       
    #write nodes to txt file in json format
    with open(datadir+"nodes.json", 'w') as nodesjson:
        #if (userlogin) == 1:             
        nodesjson.write(json_nodes)
    #write nodes to txt file in json format also in user folder
    if ('email' in session):
        with open(datadir+"user/"+str(session['email'])+"/"+timeextension+"_0_"+genes_for_folder_name+marker+"/nodes.json", "w") as temp_file_nodes:
            temp_file_nodes.write(json_nodes)
    return Response(generate(genes, snt_file), mimetype='text/event-stream')

@app.route("/tableview")
def tableview():
    with open(datadir+"nodes.json") as jsonfile:
        jnodes = json.load(jsonfile)
    jedges =''
    file_edges = open(datadir+'edges.json', 'r')
    for line in file_edges.readlines():
        if ':' not in line:
            nodata_temp = 1
        else: 
            nodata_temp = 0
            with open(datadir+"edges.json") as edgesjsonfile:
                jedges = json.load(edgesjsonfile)
            break
    genename=session['query'] 
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
    message3="<b> Actions: </b><li> <font color=\"red\">Click on the abstract count to read sentences linking the keyword and the gene.</font> <li> Click on a gene to search its relations with top 200 addiction genes. <li> Click on a keyword to see the terms included in the search. <li>View the results in <a href='cytoscape'><b> a graph.</b></a>"
    return render_template('tableview.html', nodata_temp=nodata_temp, num_gene=num_gene,session_path = session['path'], jedges=jedges, jnodes=jnodes,gene_name=gene_name, message3=message3)

@app.route("/tableview0")
def tableview0():
    with open(datadir+"nodes.json") as jsonfile:
        jnodes = json.load(jsonfile)
    jedges =''
    file_edges = open(datadir+'edges.json', 'r')
    for line in file_edges.readlines():
        if ':' not in line:
            nodata_temp = 1
        else: 
            nodata_temp = 0
            with open(datadir+"edges.json") as edgesjsonfile:
                jedges = json.load(edgesjsonfile)
            break
    genename=session['query'] 
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
    message4="<b> Notes: </b><li> These are the keywords that have <b>zero</b> abstract counts. <li>View all the results in <a href='cytoscape'><b> a graph.</b></a>"
    return render_template('tableview0.html',nodata_temp=nodata_temp, num_gene=num_gene,session_path = session['path'], jedges=jedges, jnodes=jnodes,gene_name=gene_name, message4=message4)

@app.route("/userarchive")
def userarchive():
    if os.path.exists(datadir+"user/"+str(session['email'])) == False:
        flash("Search history doesn't exist!")
        return render_template('index.html')
    if ('email' in session):
        session['user_folder'] = datadir+"user/"+str(session['email'])
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
    remove_folder = request.args.get('remove_folder')
    shutil.rmtree(datadir+"user/"+str(session['email']+"/"+remove_folder), ignore_errors=True)
    return redirect(url_for('userarchive'))

@app.route('/date', methods=['GET', 'POST'])
def date():
    select_date = request.args.get('selected_date')
    #open the cache folder for the user
    tf_path=datadir+"user"
    if ('email' in session):
        time_extension = str(select_date)
        time_extension = time_extension.split('_0_')[0]
        gene_name1 = str(select_date).split('_0_')[1]
        time_extension = time_extension.replace(':', '_')
        time_extension = time_extension.replace('-', '_')
        session['path'] = tf_path+"/"+str(session['email'])+"/"+select_date+"/"+time_extension
        session['user_folder'] = tf_path+"/"+str(session['email'])
    else:
        tf_path=tempfile.gettempdir()
        session['path']=tf_path+"/tmp" + ''.join(random.choice(string.ascii_letters) for x in range(6)) 
    with open(tf_path+"/"+str(session['email'])+"/"+select_date+"/edges.json", "r") as archive_file:
        with open(datadir+"edges.json", "w") as temp_file:
            for line in archive_file:
                temp_file.write(line)        
    with open(tf_path+"/"+str(session['email'])+"/"+select_date+"/nodes.json", "r") as archive_file:
        with open(datadir+"nodes.json", "w") as temp_file:
            for line in archive_file:
                temp_file.write(line) 
    with open(datadir+"nodes.json", "r") as jsonfile:
        jnodes = json.load(jsonfile)

    jedges =''
    file_edges = open(datadir+'edges.json', 'r')
    for line in file_edges.readlines():
        if ':' not in line:
            nodata_temp = 1
        else: 
            nodata_temp = 0
            with open(datadir+"edges.json") as edgesjsonfile:
                jedges = json.load(edgesjsonfile)
            break
    gene_list=[]
    if nodata_temp == 0:
        for p in jedges['data']:
            if p['source'] not in gene_list:
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
    session['query'] = gene_list
    message3="<b> Actions: </b><li><font color=\"red\">Click on the keywords to see the indicated number of abstracts </font><li> Click on a gene to search its relations with top 200 addiction genes<li>Click on a keyword to see the terms included in the search<li>Hover your pointer over a node to hide other links <li>Nodes can be moved around for better visibility, reload the page will restore the original layout<li> View the results in <a href='cytoscape'><b>a graph.</b></a>"
    return render_template('tableview.html', title='',nodata_temp=nodata_temp, date=select_date, num_gene=num_gene,session_path = session['path'], jedges=jedges, jnodes=jnodes,gene_name=gene_name, message3=message3)

@app.route('/cytoscape')
def cytoscape():
    message2="<b> Notes: </b><li><font color=\"red\">Click on a line to see the indicated number of abstracts </font> <li> Click on a gene to search its relations with top 200 addiction genes<li>Click on a keyword to see the terms included in the search<li>Hover your pointer over a node to hide other links <li>Nodes can be moved around for better visibility, reload the page will restore the original layout<li>View the results in <a href='tableview'><b>a table. </b></a>"
    with open(session['path']+"_cy","r") as f:
        elements=f.read()
    with open(session['path']+"_0link","r") as z:
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
    stress_systemic = "<b>Sentence(s) describing systemic stress (classified using a deep learning model):</b><hr>"
    with open(tf_name, "r") as df:
        all_sents=df.read()
    for sent in all_sents.split("\n"):
        if len(sent.strip())!=0:
            (gene,nouse,cat, pmid, text)=sent.split("\t")
            if (gene.upper() == gene0.upper() and cat.upper() == cat0.upper()) :
                out3+= "<li> "+ text + " <a href=\"https://www.ncbi.nlm.nih.gov/pubmed/?term=" + pmid +"\" target=_new>PMID:"+pmid+"<br></a>"
                num_abstract += 1
                if(pmid+cat0 not in pmid_list):
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
        out2 = str(num_abstract) + ' sentences in ' + str(len(pmid_list)) + ' studies' + "<br><br>"
    else:
        out2 = str(num_abstract) + ' sentence(s) in ' + str(len(pmid_list)) + ' study' "<br><br>"
    if(out_neg == "" and out_pos == ""):
        out= out1+ out2 +out3
    elif(out_pos != "" and out_neg!=""):
        out = out1 + out2 + stress_systemic+out_pos + stress_cellular + out_neg
    elif(out_pos != "" and out_neg ==""):
        out= out1+ out2 + stress_systemic + out_pos
    elif(out_neg != "" and out_pos == ""):
        out = out1 +out2+stress_cellular+out_neg
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
    allnodes={**brain_d, **drug_d, **function_d, **addiction_d, **stress_d, **psychiatric_d}
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
    app.run(debug=True, port=4200)
