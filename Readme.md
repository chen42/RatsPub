# RatsPub: Relationship with Addiction Through Searches of PubMed

http://rats.pub

RatsPub searches PubMed to find sentences that contain the query terms (e.g., gene symbols) and a drug addiction related keyword. Over 300 of these keywords are organized into six categories:
* names of abused drugs, e.g., opioids
* terms describing addiction, e.g., relapse
* key brain regions implicated in addiction, e.g., ventral striatum
* neurotrasmission, e.g., dopaminergic
* synaptic plasticity, e.g., long term potentiation
* intracellular signaling, e.g., phosphorylation

Live searches are conducted through PubMed to get relevant PMIDs, which are then used to retrieve the abstracts from a local archive. The relationships are presented as an interactive cytoscape graph. The nodes can be moved around to better reveal the connections. Clicking on the links will bring up the corresponding sentences in a new browser window. Stress related sentences are further classified into either systemic or cellular stress using a convolutional neural network.

## Top addiction related genes

0. extract gene symbol, alias and name from NCBI gene_info for taxid 9606.
1. search PubMed to get a count of these names/alias, with addiction keywords and drug name 
2. sort the genes with top counts, retrieve the abstracts and extract sentences with the 1) symbols and alias and 2) one of the keywords. manually check if there are stop words need to be removed. 
3. sort the genes based on the number of abstracts with useful sentences.
4. generate the final list, include symbol, alias, and name

## dependencies

* [local copy of PubMed](https://dataguide.nlm.nih.gov/edirect/archive.html)
* python flask
* python nltk

## planned
* NLP analysis of the senences (topic modeling, ranking, etc.)
