#!/bin/bash

while getopts j:r:m:l: opt
do
    case "${opt}" in
        j) RUN_JOBS=${OPTARG};;
        r) RUNCOUNT_LIMIT=${OPTARG};;
        m) MTHD=${OPTARG};;
        l) JOB_RESOURCES=${OPTARG};;
#        v) VARS+=${OPTARG};;
    esac
done
DATE=$(date +%Y_%m_%d_%H%M%S)
VARS=${@:9}

echo ${MTHD}" algorithm params: "${VARS}
echo "date: "$DATE

LOGDIR=/work/ws/nemo/fr_mv135-rlAgents-0/logs/SMAC/$MTHD/$DATE
#LOGDIR=$HOME/logs/HO/$MTHD/$DATE
mkdir -p $LOGDIR
echo "made logdir "$LOGDIR

MSUB_OUTPUT=$LOGDIR/msub_output
mkdir -p $MSUB_OUTPUT
echo "made msub output dir "$MSUB_OUTPUT

for ((idx_job=1; idx_job<=$RUN_JOBS; idx_job++)); do
    echo -e "Submitting job: "${idx_job}
#    echo "$(date +%Y_%m_%d_%H%M%S)"

    ARGS=(${MTHD} ${LOGDIR} ${DATE} ${idx_job} ${RUNCOUNT_LIMIT} ${VARS})
    echo ARGUMENTS
    echo "${ARGS[*]}"

    msub -N smac-run-${idx_job} -j oe -o $MSUB_OUTPUT/output.o${idx_job} -v SCRIPT_FLAGS="${ARGS[*]}" -l ${JOB_RESOURCES} /home/fr/fr_fr/fr_mv135/src/RLAgentsFlappyBird/HPO_scripts/run_SMAC_instance.sh
#    msub -N smac-run-${idx_job} -j oe -o $MSUB_OUTPUT/output.o${idx_job} -v SCRIPT_FLAGS="${ARGS[*]}" -l nodes=1:ppn=10,pmem=1gb,walltime=15:00:00 /home/fr/fr_fr/fr_mv135/src/RLAgentsFlappyBird/run_SMAC_instance.sh
#    msub -N smac-run-${idx_job} -j oe -o $MSUB_OUTPUT/output.o${idx_job} -v SCRIPT_FLAGS="${ARGS[*]}" -l nodes=1:ppn=10,pmem=1gb,walltime=1:00:00 /home/fr/fr_fr/fr_mv135/src/RLAgentsFlappyBird/run_SMAC_instance.sh
done
