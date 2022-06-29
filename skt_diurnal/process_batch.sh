#!/bin/bash 

## to submit several batch jobs in levante 
## E. Dutra Jun 2022
set -eux 



# resol=tco2559-ng5
# resol=tco3999-ng5
# resol=tco1279-orca025

resol="ngc2012"
# resol="ngc2009"

WDIR=/home/b/b381666/nextgems/skt_process
cd $WDIR
mkdir -p subs 
cd subs 

for yr in {2020..2027}
do 
for mm in 04 05 06 07 08
do
ddate=${yr}${mm}

tag=${resol}_${ddate}

cat > sub_$tag << EOF
#!/bin/bash
#SBATCH --job-name=$tag
#SBATCH -p shared
#SBATCH --ntasks-per-node=1
#SBATCH --nodes=1
#SBATCH --time=12:00:00
#SBATCH -o sub_${tag}.out
#SBATCH -e sub_${tag}.err
#SBATCH --mem=3Gb 
# #SBATCH --reservation=nextGEMS
#SBATCH -A bb1153

module load python3

cd /home/b/b381666/nextgems/skt_process
# python3 -u process_ifs_skt.py ${resol} ${ddate}
python3 -u process_icon_skt.py ${resol} ${ddate}
EOF

sbatch sub_$tag
# exit
done 
done 
