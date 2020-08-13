# ./gwas_catalog_v1.0.2-associations_e100_r2020-08-05.tsv


cut -f 2,8,14,15,28,35,22  $1 |grep -P -i "schizo|autism|smoking|addiction|cocaine|opioid|morphin|cannabis|depression|anxiety|bipolar|behavior|mental|amphetamine|nicotine|chornic obstructive|psychiatric|methadone|heroin|alcohol|drug dependence"|grep -v -i intergenic |grep -v BMI >addiction_gwas.tsv

python ./process_gwas.py > ../gwas_addiction.tab

echo "../gwas_addiction.tab updated"

