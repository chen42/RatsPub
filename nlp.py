import string
import re
import os
from os import listdir
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from collections import Counter
import numpy as np
from numpy import array
import keras
from keras.models import Model
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Embedding
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras import metrics
from keras import optimizers
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

def predict_sent(sent_for_pred):
    max_length = 64
    tokens = clean_doc(sent_for_pred, vocab)
    tokens = [w for w in tokens if w in vocab]
    # convert to line
    line = ' '.join(tokens)
    line = [line]
    tokenized_sent = tokenizer.texts_to_sequences(line)
    tokenized_sent = pad_sequences(tokenized_sent, maxlen=max_length, padding='post')
    model = create_model(23154, 64)
    # load the weights
    checkpoint_path = "./nlp/weights.ckpt"
    model.load_weights(checkpoint_path)
    predict_sent = model.predict(tokenized_sent, verbose=0)
    percent_sent = predict_sent[0,0]
    if round(percent_sent) == 0:
        return 'neg'
    else:
        return 'pos'