#!/bin/bash

output_dir="/projects/assigned/course-scheduling/Course-Scheduling-System/workspace/output"
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi
/projects/assigned/course-scheduling/Course-Scheduling-System/env/bin/python3 ../bin/time-schedule.py config 1>output/log.stdout 2>output/log.stderr
#source activate /projects/assigned/course-scheduling/Course-Scheduling-System/env
#python3 ../bin/time-schedule.py config 
cp CoursesThisQuarter output/
cp config output/
cp ConflictCourses output/
cp InstructorPref output/
cp CourseInfo output/

