import string
import re
import os
from os import listdir
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from collections import Counter
import numpy as np
from numpy import array
import sklearn
from sklearn import metrics
from sklearn.metrics import confusion_matrix
import tensorflow as tf
import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import plot_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Dropout, Embedding, Conv1D, MaxPooling1D
from tensorflow.keras.preprocessing.text import text_to_word_sequence
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras import metrics, optimizers
import pickle

def clean_doc(doc, vocab):
    doc = doc.lower()
    # split into tokens by white space
    tokens = doc.split()
    # remove punctuation from each word
    re_punc = re.compile('[%s]' % re.escape(string.punctuation))    
    tokens = [re_punc.sub('' , w) for w in tokens]    
    # filter out short tokens
    tokens = [word for word in tokens if len(word) > 1]
    # filter out stop words
    stop_words = set(stopwords.words('english'))
    tokens = [w for w in tokens if not w in stop_words]
    # stemming of words
    porter = PorterStemmer()
    stemmed = [porter.stem(word) for word in tokens]
    #print(stemmed[:100])
    return tokens

# loading
with open('./nlp/tokenizer.pickle', 'rb') as handle:
    tokenizer = pickle.load(handle)
with open('./nlp/vocabulary.txt', 'r') as vocab:
    vocab = vocab.read()

print(len(vocab.split()))

def create_model(vocab_size, max_length):
    model = Sequential()
    model.add(Embedding(vocab_size, 32, input_length=max_length))
    model.add(Conv1D(filters=16, kernel_size=4, activation='relu'))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(10, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    opt = tf.keras.optimizers.Adamax(learning_rate=0.002, beta_1=0.9, beta_2=0.999)
    model.compile(loss='binary_crossentropy', optimizer=opt, metrics=[tf.keras.metrics.AUC()])
    #plot_model(model, to_file='model.png', show_shapes=True)
    return model

model = create_model(23154, 64)
model.summary()

checkpoint_path = "./nlp/weights.ckpt"
model.load_weights(checkpoint_path)


err=0
pr=0
total=0
max_length=64
pos_list = []
neg_list = []
for k in range(30000,35000):
    file_name = "./sentences/yes_all/yes_"+str(k)+".txt"
    try:     
        file = open(file_name,"r") 
        sent =  file.readline()
        tokens = clean_doc(sent,vocab)
        tokens = [w for w in tokens if w in vocab]
        line = ' '.join(tokens)
        line = [line]
        Xtrain_ex = tokenizer.texts_to_sequences(line)
        Xtrain_ex = pad_sequences(Xtrain_ex, maxlen=max_length, padding='post')
        yhat_pos = model.predict(Xtrain_ex, verbose=0)
        percent_pos = yhat_pos[0,0]
        pos_list.append(yhat_pos[0,0])
        total = total+1
        if round(percent_pos) == 0:
            err = err +1      
        if (percent_pos < 0.9 and percent_pos > 0.1):
            pr = pr+1    
    except FileNotFoundError:
        pass
    file.close()
    
for t in range(30000,35000):
    file_name = "./sentences/no_all/no_"+str(t)+".txt"
    try:     
        file = open(file_name,"r") 
        sent =  file.readline()
        tokens = clean_doc(sent,vocab)
        tokens = [w for w in tokens if w in vocab]
        line = ' '.join(tokens)
        line = [line]
        Xtrain_ex = tokenizer.texts_to_sequences(line)
        Xtrain_ex = pad_sequences(Xtrain_ex, maxlen=max_length, padding='post')
        yhat_neg = model.predict(Xtrain_ex, verbose=0)
        percent_pos = yhat_neg[0,0]
        neg_list.append(yhat_neg[0,0])   
        total = total+1
        if round(percent_pos) == 1:
            err = err +1 
        if (percent_pos < 0.9 and percent_pos > 0.1):
            pr = pr+1    
    except FileNotFoundError:
        pass
    file.close()

err_pos = 0
for i in range(len(pos_list)):
    #print(round(pos_list[i]))
    if (pos_list[i] < 0.5):
        err_pos += 1
print("Error for system stress class", err_pos)

err_neg = 0
for i in range(len(neg_list)):
    #print((neg_list[i]))
    if (round(neg_list[i]) > 0.5):
        err_neg += 1
print("Error for cellular stress class",err_neg)
print((err_pos + err_neg)/10000)

pos_list_int = []
for i in range(5000):
    if(pos_list[i]<0.5):
        pos_list_int.append(0)
    else:
        pos_list_int.append(1)
        
neg_list_int = []
for i in range(5000):
    if(neg_list[i]>0.5):
        neg_list_int.append(0)
    else:
        neg_list_int.append(1)

listofzeros = [0] * 5000
listofones= []
for i in range(5000):
    listofones.append(1)
y_true = listofones + listofzeros
y_pred_int = pos_list_int + neg_list_int
confusion_matrix(y_true, y_pred_int)

pos_list_np = np.array(pos_list)
neg_list_np = np.array(neg_list)

y_pred_np = np.array(pos_list+neg_list)
y_true_np = np.array(y_true)


fpr, tpr, thresholds = metrics.roc_curve(y_true_np, y_pred_np, pos_label=0)
print(metrics.auc(fpr, tpr))
print(sklearn.metrics.roc_auc_score(y_true_np, y_pred_np))

plt.gcf().subplots_adjust(bottom=0.15)
data1 = pos_list_np
data2 = neg_list_np
bins = np.arange(0, 1+1e-8, 0.1)
plt.hist(data1, bins=bins, alpha=0.5, color = 'red')
plt.hist(data2, bins=bins, alpha=0.5, color = 'blue')
plt.xlabel("predicted probabilities \n blue: CS red:SS")
plt.ylabel('number of sentences')
plt.savefig('stress_pred.png', dpi=300)
plt.show()
