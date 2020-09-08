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
import tensorflow as tf
import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import plot_model
from tensorflow.keras.models import Sequential, Dense, Flatten, Dropout, Embedding, Conv1D, MaxPooling1D
from tensorflow.keras.preprocessing.text import text_to_word_sequence
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras import metrics, optimizers
import pickle

def load_doc(filename):
    file = open(filename, 'r')
    text = file.read()
    file.close()
    return text

def clean_doc(doc, vocab):
    #tokens = text_to_word_sequence(doc, filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n',lower=True, split=' ')
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

# load all docs in a directory
def train_valid(directory, vocab, is_train):
    documents = list()
    for filename in listdir(directory):
        if is_train and (filename.endswith('1.txt') or filename.endswith('2.txt')):
            continue
        if not is_train and not (filename.endswith('1.txt') or filename.endswith('2.txt')):
            continue
        path = directory + '/' + filename
        doc = load_doc(path)
        tokens_train_valid = clean_doc(doc, vocab)      
        tokens_train_valid = [w for w in tokens_train_valid if w in vocab]
        tokens_train_valid = ' '.join(tokens_train_valid)
        documents.append(tokens_train_valid)
    return documents

def add_doc_to_vocab(filename, vocab):
    doc = load_doc(filename)
    tokens = clean_doc(doc, vocab)
    vocab.update(tokens)

def form_vocabulary(directory, vocab):
    for filename in listdir(directory):
        if not filename.endswith(".txt"):
            next
        path = directory + '/' + filename
        add_doc_to_vocab(path, vocab)

def load_dataset(vocab, is_train):
    neg = train_valid('sentences/no_10000', vocab, is_train)
    pos = train_valid('sentences/yes_10000', vocab, is_train)
    docs = neg + pos
    labels = array([0 for _ in range(len(neg))] + [1 for _ in range(len(pos))])
    return docs, labels

def tokenize_data(train_docs, valid_docs, maxlen):
    # create the tokenizer
    tokenizer = Tokenizer()
    # fit the tokenizer on the documents
    tokenizer.fit_on_texts(vocab)
    # encode training data set
    Xtrain = tokenizer.texts_to_sequences(train_docs)
    Xtrain = pad_sequences(Xtrain, maxlen=max_length, padding='post')
    # encode training data set
    Xvalid = tokenizer.texts_to_sequences(valid_docs)
    Xvalid = pad_sequences(Xvalid, maxlen=max_length, padding='post')
    return Xtrain, Xvalid, tokenizer

def save_list(lines, filename):
    data = '\n'.join(lines)
    file = open(filename, 'w')
    file.write(data)
    file.close()

vocab = Counter()
# add all docs to vocab
form_vocabulary('sentences/no_10000', vocab)
form_vocabulary('sentences/yes_10000', vocab)
save_list(vocab, 'vocab.txt')

# load the vocabulary
vocab_filename = 'vocab.txt'
vocab = load_doc(vocab_filename)
vocab = set(vocab.split())
save_list(vocab, 'vocab_last.txt')
# load training and validation data
train_docs, ytrain = load_dataset(vocab, True)
valid_docs, yvalid = load_dataset(vocab, False)
max_length = max([len(s.split()) for s in train_docs])
print("Maximum length:",  max_length)
Xtrain, Xvalid, tokenizer = tokenize_data(train_docs, valid_docs, max_length)

# saving
with open('tokenizer.pickle', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

print(len(vocab))

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
#    model.summary()
    return model

model = create_model(len(vocab)+1, max_length)

checkpoint_path = "training/cp-{epoch:04d}.ckpt"
checkpoint_dir = os.path.dirname(checkpoint_path)

# Create a callback that saves the model's weights
cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path, save_weights_only=True, verbose=1)

# Train the model with the new callback
model_fit=model.fit(Xtrain, ytrain, epochs=20,batch_size=64, validation_data=(Xvalid,yvalid),callbacks=[cp_callback]) 

# Plot training & validation accuracy values
plt.plot(model_fit.history['auc'])
plt.plot(model_fit.history['val_auc'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='lower right')
plt.savefig('model_accuracy.png')
plt.show()

# Plot training & validation loss values
plt.plot(model_fit.history['loss'])
plt.plot(model_fit.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper right')
plt.savefig('model_loss.png')
plt.show()
