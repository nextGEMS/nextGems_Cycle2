## How to use appetizer

You can get the latest version from https://github.com/koldunovn/appetizer

Basic usage is:

```bash
python /home/a/a270088/PYTHON/appetizer/appetizer.py appetizer_10u.yml
```

So, you need a .yaml file with configuration. Example is here:

https://github.com/koldunovn/appetizer/blob/main/appetizer_config.yml

### Submit it as a job on levante


```bash
#!/bin/bash
#SBATCH --job-name=aptzr
#SBATCH -p compute
#SBATCH --ntasks-per-node=128
#SBATCH --nodes=1
#SBATCH --time=08:00:00
#SBATCH -o slurm-out.out
#SBATCH -e slurm-err.out
#SBATCH -A ab0995

source /sw/etc/profile.levante
source ../env/levante.dkrz.de/shell

ulimit -s unlimited

echo Submitted job: $jobid
squeue -u $USER

# determine JOBID
JOBID=`echo $SLURM_JOB_ID |cut -d"." -f1`

date
python /home/a/a270088/PYTHON/appetizer/appetizer.py appetizer_10u.yml
date
```

### Example folder 

/home/a/a270088/PYTHON/nextgems/km4/appetizer/scripts

