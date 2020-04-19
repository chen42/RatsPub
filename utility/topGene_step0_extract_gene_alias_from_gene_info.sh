#!/bin/bash
#-e "s/\(|\)/ /g"  -e "s/\[|\]/ /g" 
grep ^9606 ~/Downloads/gene_info |cut -f 3,5,12|grep -v ^LOC|grep -v -i pseudogene |sed -e "s/\t-//"  -e "s/\t/|/2"  -e "s/\t-//"  -e "s/\t/\|/" -e "s/(\|)\|\[\|\]\|{\|}/ /g" | sort >ncbi_gene_symb_syno_name_txid9606.txt 

