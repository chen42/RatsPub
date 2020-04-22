import os

## save all pmids for the top genes so that I don't have to search for these. 

def getPMID(query):
    print (query)
    pmids=os.popen("esearch -db pubmed -query \"" +  query + "\" | efetch -format uid").read()
    return(pmids)

def collectTerms():
    pmids_f=open("topGene_all.pmid","w+")
    with open("./topGene_symb_alias.txt", "r") as top:
        q=str()
        cnt=0
        for one in top:
            cnt+=1
            (symb, alias)=one.split("\t")
            q+="|"+symb+"|"+alias.strip()
            if (cnt==5):
                print ("\n")
                q=q[1:]
                q=q.replace(";", "[tiab] OR ")+"[tiab]"
                pmids=getPMID(q)
                pmids_f.write(pmids)
                cnt=0
                q=str()
        print("there should be nothing following the word empty"+q)

collectTerms()
os.system("sort topGene_all.pmid |uniq > topGene_uniq.pmid" )
os.system("rm topGene_all.pmid")
print ("results are in topGen_uniq.pmid")

