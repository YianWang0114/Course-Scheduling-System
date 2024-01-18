#!/bin/bash
output_dir="./output"
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi
source ~/.bashrc
source activate /projects/assigned/course-scheduling/Course-Scheduling-System/env
python3 ../bin/time-schedule.py config 1>output/log.stdout 2>output/log.stderr
#/projects/assigned/course-scheduling/Course-Scheduling-System/env/bin/python3 ../bin/time-schedule.py config 1>output/log.stdout 2>output/log.stderr
cp config output/


