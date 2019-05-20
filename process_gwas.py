import re

with open("./addiction_gwas.tsv", "r") as f:
    for line in f:
        try:
            (pmid, trait0, gene0, gene1, snp, pval, trait1)=line.strip().split("\t")
        except:
            next
        key1="unassigned"
        key2="unassigned"
        trait=trait0+"; "+trait1
        genes=gene0+";"+gene1
        if re.search('cocaine', trait, flags=re.I):
            key1="addiction"
            key2="cocaine"
        elif re.search('smoking|congestive|nicotine', trait, flags=re.I):
            key1="addiction"
            key2="nicotine"
        elif re.search('opioid|morphin|heroin|methadone', trait, flags=re.I):
            key1="addiction"
            key2="opioid"
        elif re.search('amphetam', trait, flags=re.I):
            key1="addiction"
            key2="amphetamine"
        elif re.search('canabis', trait, flags=re.I):
            key1="addiction"
            key2="canabis"
        elif re.search('food', trait, flags=re.I):
            key1="addiction"
            key2="food"
        elif re.search('alcohol', trait, flags=re.I):
            key1="addiction"
            key2="alcohol"
        elif re.search('addiction|abuse', trait, flags=re.I):
            key1="addiction"
            key2="addiction"
        else:
            key1="behavior"
            key2="psychiatric"
        genes=genes.replace(" - ", ";")
        genes=genes.replace(",", ";")
        printed=dict()
        for gene in genes.split(";"):
            gene=gene.replace(" ","")
            if gene !="NR" and gene not in  printed:
                text="SNP:<b>"+snp+"</b>, P value: <b>"+pval+"</b>, Disease/trait:<b> "+trait0+"</b>, Mapped trait:<b> "+trait1+"</b>"
                print (gene+"\t"+"GWAS"+"\t"+key2+"_GWAS\t"+pmid+"\t"+text)
            printed[gene]=1
