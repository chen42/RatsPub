# RatsPub: Relationship with Addiction Through Searches of PubMed

This app searches PubMed to find sentences that contain the query terms (e.g., gene symbols) and a drug addiction related keyword. These keywords belong to the following categories:
* names of abused drugs, e.g., opioids
* terms describing addiction, e.g., relapse
* key brain regions implicated in addiction, e.g., ventral striatum
* neurotrasmission, e.g., dopaminergic
* synaptic plasticity, e.g., long term potentiation
* intracellular signaling, e.g., phosphorylation

Live searches are conducted through PubMed to get relevant PMIDs, which are then used to retrieve the abstracts from a local archive. The relationships are presented as an interactive cytoscape graph. The nodes can be moved around to better reveal the connections. Clicking on the links will bring up the corresponding sentences in a new browser window.

## dependencies

* [local copy of PubMed](https://dataguide.nlm.nih.gov/edirect/archive.html)
* python flask
* cytoscape.js
