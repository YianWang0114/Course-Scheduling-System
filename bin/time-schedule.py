"""
Author: Yian Wang
Supervisor: Professor Fei Xia
Organization: University of Washington, the Linguistics Department
Last Update: Dec 6, 2023

If you have any questions or need further clarification, please feel free to contact the author at wangyian@uw.edu.
"""

import pdb
import sys
import math
from datetime import datetime, timedelta
from collections import defaultdict
import pulp
import os
import csv
import shutil

#################################################################################
class Course:
    def __init__(self, courseId, courseName, instructorId, mustOnDays, mustStartSlot, mustEndSlot,\
                 lengPerSession, sessionsPerWeek, largeClass, exempted, isTASession, slotNum):
        self.courseId = courseId #int, e.g., 0
        self.courseName = courseName #string e.g., '200'
        self.instructorId = instructorId #int, e.g., 0
        self.mustOnDays = mustOnDays #list of int, e.g., [1,3,5]
        self.mustStartSlot = mustStartSlot #int, e.g., 0
        self.mustEndSlot = mustEndSlot #int, e.g., 19
        self.lengPerSession = lengPerSession #int, e.g., 110
        self.sessionsPerWeek = sessionsPerWeek #int, e.g., 2
        self.largeClass = largeClass #int, either 0 or 1
        self.exempted = exempted #int, either 0 or 1
        self.isTASession = isTASession #int, either 0 or 1
        self.slotNum = slotNum #int, = ceiling(lengPerSession / 30)

#################################################################################
def time_transfer(time_string, filename, line_number):
    '''
    Usage: This function transfer time from string to datetime object

    Inpurt:
    time_string(string): A specific time in the 24-hour clock format represented as a string, e.g., "10:30"

    Output: 
    time(datetime): The corresponding datetime object, e.g., datetime.datetime(1900, 1, 1, 10, 30)
    '''

    try:
        time = datetime.strptime(time_string, '%H:%M')
    except:
        sys.exit(f"Wrong time format. Time can not be '{time_string}' in {filename} file line {line_number}.")

    return time 

#################################################################################
def timeSlotName2Id(start, timeSlotName):
    '''
    Usage: This function transfer time from datetime object to slotid

    Input:
    start(datetime): A datetime object corresponding to instructional day starting time, e.g., datetime.datetime(1900, 1, 1, 8, 30)
    timeSlotName(datetime): A datetime object corresponding to a time you want to convert to slot id

    Output: 
    id(float): The corresponding slot id, e.g., 0,0. 

    Note: output is a float number. Depending on usage, you need to choose whether to ceiling or floor it. 
    '''

    id = (timeSlotName - start).total_seconds() / 60 / 30

    return id

#################################################################################
def timeSlotId2ISlot(start, timeSlotId):
    '''
    Usage: This function transfer time from slotId to string in "%H:%M" format

    Inpurt:
    start(datetime): A datetime object corresponding to instructional day starting time, e.g., datetime.datetime(1900, 1, 1, 8, 30)
    timeSlotId(int): A time slot, e.g., 12

    Output: 
    name(string): The corresponding time in "%H:%M" format, e.g., '14:30'
    '''

    name = start + timedelta(minutes=timeSlotId * 30)

    return name.strftime('%H:%M')

#################################################################################
def days2listint(days, filename, line_number):
    '''
    Usage: Maps days from 'MTWRF' to '01234'. 

    Inpurt:
    days(string): A string representing teaching days of a course, e.g., 'MWF'

    Output: 
    day_list(list): A list of int. e.g., [0,2,4] means a course is taught on Monday, Wednesday, and Friday
    '''

    day_list = []
    day_mapping = {'m': 0, 't': 1, 'w': 2, 'r': 3, 'f': 4}
    for day in days:
        if (day not in day_mapping):
            sys.exit(f"Days should be 'MTWRF'. Please modify line {line_number} of {filename} file.")
        else:
            day_list.append(day_mapping[day])

    return day_list

#################################################################################
def intlist2days(intlist):
    '''
    Usage: Maps teaching days from [0,2,4] to ['M', 'W', 'F']. 

    Inpurt:
    intlist(list): A list of int, e.g., [0,2,4]

    Output: 
    day_list(list): A list of string. e.g., ['M', 'W', 'F'] means a course is taught on Monday, Wednesday, and Friday
    '''

    day_mapping = {0: 'M', 1: 'T', 2: 'W', 3: 'R', 4: 'F'}
    day_list = [day_mapping[day] for day in intlist if day in day_mapping]

    return day_list

#################################################################################
def check_config(config):
    '''
    Usage: Check whether config file has all the parameter it should have. If not, exit with an error message.

    Input:
    config(dict): A dictionary that stores all the parameter we get from config file.
    '''

    parameter = ['UseDefaultPath', 'InstructDayStartsAt', 'InstructDayEndsAt', 'Class-default-end-time', 'BlockSchedulingStartsAt',\
        'BlockSchedulingEndsAt', '10PercRuleStartsAt', '10PercRuleEndsAt', 'RulePercentage', '50-min-class-start-time', '80-min-class-start-time',\
        '110-min-class-start-time', '170-min-class-start-time', 'Must-follow-block-policy', 'Penalty-for-violating-block-policy',\
        'Treat-same-day-preference-as-hard-constraint', 'Assume-same-day-if-not-specified', 'UWPolicyWeight', 'InstructorPrefWeight',\
        'CourseInfo', 'ConflictCourse', 'InstructorPref','CourseInstructor',\
        'OutputDir', 'DefaultCourseInfoFile', 'DefaultConflictCourseFile', 'DefaultInstructorPrefFile',\
        'DefaultCoursesThisQuarterFile', 'DefaultOutputDir']
    
    for i in parameter:
        if i not in config:
            sys.exit(f'{i} not in config file. Please modify.')
            
    return

#################################################################################
def convert_key_type(config, start_time):
    '''
    Usage: Convert some keys from string to appropriate data types(int, float, list...).
    
    Input:
    config(dict): A dictionary that stores all the parameter we get from config file.
    start_time(datetime): A datetime object corresponding to instructional day starting time. e.g., datetime.datetime(1900, 1, 1, 8, 30)
    '''

    # Define keys that should be treated as floats, integers, or list
    float_keys = ["RulePercentage", "Penalty-for-violating-block-policy", "UWPolicyWeight", "InstructorPrefWeight"]
    int_keys = ["UseDefaultPath", "Must-follow-block-policy" ,"Treat-same-day-preference-as-hard-constraint", "Assume-same-day-if-not-specified"]
    list_keys = ["50-min-class-start-time", "80-min-class-start-time", "110-min-class-start-time", "170-min-class-start-time"]

    # Convert values to the appropriate data types
    for key, value in config.items():
        if key in float_keys:
            config[key] = float(value)
        elif key in int_keys:
            config[key] = int(value)
        elif key in list_keys:
            new_list = []
            for timeName in value.split():
                slot = timeSlotName2Id(start_time, time_transfer(timeName, "config", -1)) 
                slotId = math.floor(slot) # slot can be an float num, we take the floor value
                new_list.append(slotId)
            config[key] = new_list

    return

#################################################################################
def read_config(file_name):
    '''
    Usage: Read the config file and store all the parameter. 

    Inpurt:
    file_name(string): config file's file name. e.g., 'config'

    Output: 
    config(dict): a dictionary that store all the information. 

    Format for config file:
    ###
      UseDefaultPath = 1
      InstructDayStartsAt = 8:30
    ###
    '''

    # Initialize a dictionary to store course information
    config = {}
    with open(file_name, "r") as file:
        for line in file:
            #Ignore empty lines and lines starting with "#"
            if line.startswith("#") or not line.strip():
                continue
            # Split each line into key and value
            try:
                key, value = line.strip().split("=")
            except:
                sys.exit("Incorrect config file format. Please have a '=' between variable name and value.")
            key = key.strip()
            value = value.strip().strip('"')
            # Store the values in the dictionary
            config[key] = value

    check_config(config) #Check if config file has all the parameters. If not, exits with an error message. 
    start_time = time_transfer(config['InstructDayStartsAt'], "config", -1)
    total_day_time = time_transfer(config['InstructDayEndsAt'], "config", -1) - start_time
    SlotNumPerday = math.ceil(total_day_time.total_seconds()/60/30) #A slot is 30 min

    convert_key_type(config, start_time) #Convert keys to appropriate data type.
    bstart = time_transfer(config['BlockSchedulingStartsAt'], "config", -1)
    config['BlockSchedulingStartsAtid'] = math.floor(timeSlotName2Id(start_time, bstart))
    bend = time_transfer(config['BlockSchedulingEndsAt'], "config", -1)
    config['BlockSchedulingEndsAtid'] = math.floor(timeSlotName2Id(start_time, bend - timedelta(hours=0, minutes=1)))
    tstart =  time_transfer(config['10PercRuleStartsAt'], "config", -1)
    config['10PercRuleStartsAtid'] = math.floor(timeSlotName2Id(start_time, tstart))
    tend = time_transfer(config['10PercRuleEndsAt'], "config", -1)
    config['10PercRuleEndsAtid'] = math.floor(timeSlotName2Id(start_time, tend))
    config['SlotNumPerday'] = SlotNumPerday

    useDefaultPath(config)

    return config

#################################################################################
def useDefaultPath(config):
    '''
    Usage: If "UseDefaultPath" is set to 1 in config file, use the default path instead.

    Input:
    config(dict): a dictionary that store all the information. 
    '''

    # Use default file path if UseDefaultPath is set to 1 in the config file
    if (config['UseDefaultPath'] == 1):
        config['CourseInfo'] = config['DefaultCourseInfoFile']
        config['ConflictCourse'] = config['DefaultConflictCourseFile']
        config['InstructorPref'] = config['DefaultInstructorPrefFile' or config['UseDefaultPath'] == 1]
        config['CourseInstructor'] = config['DefaultCoursesThisQuarterFile']
        config["OutputDir"] = config['DefaultOutputDir']
    
    return

#################################################################################
def defineID(instructor_name, course_name_before_slash, InstructorName2Id, InstructorId2Name, CourseName2Id, CourseId2Name):
    '''
    Usage: if insturtcor already has an id, return the id; else, define a new id for him/her. Do the same for course.

    Input:
    instructor_name(string): name of an instructor, e.g., 'McGarrity'
    course_name_before_slash(string): e.g., '200'
    InstructorName2Id(dict): maps instructor names to instructor ids. e.g., {'McGarrity': 0}
    InstructorId2Name(list): maps instructor ids to instructor names. e.g., ['McGarrity']
    CourseName2Id(dict): maps course names to course ids.
    CourseId2Name(list): maps course ids to course names.

    Output:
    instructor_id(int): e.g., 0
    course_id(int):e.g., 0
    '''

    # Generate course and instructor IDs
    if (instructor_name == '-'):
        instructor_id = -1  # Default to -1 if no instructor specified
    else:
        if (instructor_name.lower() not in InstructorName2Id):
            instructor_id = len(InstructorName2Id)
            InstructorName2Id[instructor_name.lower()] = instructor_id
            InstructorId2Name.append(instructor_name)
            assert(len(InstructorName2Id) == len(InstructorId2Name)) # Make sure they are of equal length
        else:
            instructor_id = InstructorName2Id[instructor_name.lower()]

    if (course_name_before_slash.lower() not in CourseName2Id):
        course_id = len(CourseName2Id)
        CourseName2Id[course_name_before_slash.lower()] = course_id
        CourseId2Name.append(course_name_before_slash)
        assert(len(CourseName2Id) == len(CourseId2Name)) # Make sure they are of equal length
    else:
        course_id = CourseName2Id[course_name_before_slash.lower()]

    return instructor_id, course_id

#################################################################################
def CourseInfoFromCTQ(information, Instructor2Courses, CourseInfo, config):
    '''
    Usage: Update course information read from CourseThisQuarter file.

    Input: 
    Instructor2Courses(dict): stores the course(s) that an instructor teaches.
    CourseInfo(list)
    instructor_id(int)
    course_id(int)
    course_name(string)
    config(dict)
    must_on_days(string)
    must_start_time(string)
    must_end_time(string)
    '''

    for instructor_id, course_id, course_name, must_on_days, must_start_time, must_end_time, line_number in information:
        Instructor2Courses[instructor_id].append(course_id)
        cur_course = CourseInfo[course_id]
        cur_course.courseId = course_id
        cur_course.courseName = course_name  #Full Name here
        cur_course.instructorId = instructor_id
        start_time = time_transfer(config['InstructDayStartsAt'], "config", -1)

        if (must_on_days != '-'):
            cur_course.mustOnDays = days2listint(must_on_days, "CourseThisQuarter", line_number) 

        if (must_start_time != '-'):
            mstart = time_transfer(must_start_time, "CTQ", line_number)
            cur_course.mustStartSlot = math.floor(timeSlotName2Id(start_time, mstart))

        if (must_end_time != '-'):
            mend = time_transfer(must_end_time, "CourseThisQuarter", line_number)
            cur_course.mustEndSlot = math.floor(timeSlotName2Id(start_time, mend - timedelta(hours=0, minutes=1)))

    return

#################################################################################
def readCTQline(values, TotalCourseNum, line_number):
    '''
    Usage: read lines from CourseThisQuarter, can read both txt format and csv format
    
    Input: 
    values(list): a list of information read from CTQ file
    TotalCourseNum(int)
    line_number(int): line number 

    Output:
    course_name(string): e.g., '450/550'
    course_name_before_slash(string): e.g., '450'
    instructor_name(string): e.g., 'cheng'
    must_on_days(string): e.g., 'mwf'
    must_start_time(string): e.g., '8:30'
    must_end_time(string): e.g., '15:20'
    TotalCourseNum(int): e.g., 1
    '''
    
    # Check the length of values, if not 5 or 8, exit
    if (len(values) != 5 and len(values) != 8):
        sys.exit(f"Warning: Incorrect CoursesThisQuarter format for line {line_number}. Each row should have 5 or 8 columns.")

    # Extract course name and instructor name
    course_name = values[0]
    course_name_before_slash = course_name.split('/')[0]
    instructor_name = values[1]
    must_on_days = values[2].lower()
    must_start_time = values[3]
    must_end_time = values[4]
    TotalCourseNum += 1

    return course_name, course_name_before_slash, instructor_name, must_on_days, must_start_time, must_end_time, TotalCourseNum

#################################################################################
def read_courseInstructor(file_name, config):
    '''
    Usage: Read the courseInstructor(courseThisQuarter) file and store all the parameter. 

    Input:
    file_name(string): courseInstructor(courseThisQuarter) file's file name. e.g., './courseThisQuarter'

    Output: 
    course_instructor(list): 
    course_instructor = [
    CourseName2Id(dict): maps course names to course ids.
    CourseId2Name(list): maps course ids to course names.
    InstructorName2Id(dict): maps instructor names to instructor ids.
    InstructorId2Name(list): maps instructor ids to instructor names.
    Instructor2Courses(dict): stores the course(s) that an instructor teaches.
    CourseInfo(list): CourseInfo[courseId] is a Course class that stores course information we read from CourseInfo and CourseThisQuarter.
    TotalCourseNum(int): Total number of courses, including regular sessions and TA sessions.
    ]

    Format for courseInstructor file:
    ###
    200        McGarrity      MWF 14:30 15:20
    233        Evans          MWF  -    15:20  
    ###

    or 
    ###
    200     	McGarrity           	MWF  	14:30   	15:20   	50   	-  	-  
    233     	Evans               	MWF  	14:30   	15:20   	50   	-  	y  
    ###
    '''

    CourseName2Id = {}
    CourseId2Name = []
    InstructorName2Id = {}
    InstructorId2Name = []

    # Course: courseId, courseName, instructorId, mustOnDays, mustStartSlot, mustEndSlot, lengPerSession, sessionsPerWeek, largeClass, exempted, isTASession, slotNum
    CourseInfo = [Course(-1, -1, -1, [], -1, -1, -1, -1, -1, -1, -1, -1) for _ in range(100)]
    Instructor2Courses = defaultdict(list)
    TotalCourseNum = 0
    line_number = 0

    information = []

    if file_name.endswith('.csv'):
        with open(file_name, 'r', newline='') as csvfile:
                csv_reader = csv.reader(csvfile)

                # Skip the header line
                header = next(csv_reader, None)
                line_number += 1
                
                # Iterate through the remaining lines 
                for values in csv_reader:
                    line_number += 1

                    # Skip empty lines or line starting with '#'
                    if not any(values):
                        continue

                    course_name, course_name_before_slash, instructor_name, must_on_days, must_start_time, must_end_time, TotalCourseNum = readCTQline(values, TotalCourseNum, line_number)
                    instructor_id, course_id = defineID(instructor_name, course_name_before_slash, InstructorName2Id, InstructorId2Name, CourseName2Id, CourseId2Name)
    
                    information.append([instructor_id, course_id, course_name, must_on_days, must_start_time, must_end_time, line_number])
                     
    else:
        # Read the CourseInstructor file line by line
        with open(file_name, "r") as file:
            for line in file:
                line_number += 1

                #Ignore empty lines and lines starting with "#"
                if not line.strip() or line.startswith("#"):
                    continue

                # Split each line into its components
                values = line.strip().split()

                course_name, course_name_before_slash, instructor_name, must_on_days, must_start_time, must_end_time, TotalCourseNum = readCTQline(values, TotalCourseNum, line_number)
                instructor_id, course_id = defineID(instructor_name, course_name_before_slash, InstructorName2Id, InstructorId2Name, CourseName2Id, CourseId2Name)
                information.append([instructor_id, course_id, course_name, must_on_days, must_start_time, must_end_time, line_number])
                
    CourseInfoFromCTQ(information, Instructor2Courses, CourseInfo, config)
    course_instructor = [CourseName2Id, CourseId2Name, InstructorName2Id, InstructorId2Name, Instructor2Courses, CourseInfo, TotalCourseNum]

    return course_instructor

#################################################################################
def CourseInfoFromCI(information, config, CourseInfo, CourseName2Id):
    '''
    Usage: Update course information read from CourseInfo file.

    Input: 
    information(list): a list that contains all the information read from CI file
    config(dict)
    CourseInfo(list)
    CourseName2Id(dict)

    Output:
    NonExemptedC(list): a list of non-exempted course's course id
    TotalNonExemptedHours(float): total number of non-ExemptedHours
    '''

    TotalC = []
    TotalNonExemptedHours = 0
    NonExemptedC = []

    for course_name, course_name_before_slash, length_per_session, num_sessions_per_week, large_class, ten_percent_rule_exempted,\
        is_a_TA_session, mustOnDays, mustStartTime, mustEndTime, line_number in information:

        if (CourseName2Id[course_name_before_slash.lower()] in TotalC):
            print(f'Warning: {course_name} appears multiple times in courseInfo', file=sys.stderr)
            continue
        
        TotalC.append(CourseName2Id[course_name_before_slash.lower()])
        cur_course = CourseInfo[CourseName2Id[course_name_before_slash.lower()]]
        start_time = time_transfer(config['InstructDayStartsAt'], "config", -1)

        cur_course.lengPerSession = length_per_session
        cur_course.sessionsPerWeek = num_sessions_per_week
        cur_course.largeClass = large_class
        cur_course.exempted = ten_percent_rule_exempted
        cur_course.isTASession = is_a_TA_session
        cur_course.slotNum = math.ceil(length_per_session / 30)
    
        if (ten_percent_rule_exempted == 0 and CourseName2Id[course_name_before_slash.lower()] not in NonExemptedC): # if a course is not exempted
            NonExemptedC.append(CourseName2Id[course_name_before_slash.lower()])
            TotalNonExemptedHours += cur_course.slotNum * num_sessions_per_week / 2

        # For mustOnDays,  mustStartTime, mustEndTime, do the intersection
        if (mustOnDays != '-'):
            mustOnDays_intersection = set(cur_course.mustOnDays) & set(days2listint(mustOnDays, "courseInfo", line_number))
            cur_course.mustOnDays = list(mustOnDays_intersection)
            if len(cur_course.mustOnDays) < num_sessions_per_week:
                sys.exit(f"MustDays for {cur_course.courseName} should not be less than session per week.\
                        Please check courseInfo and courseThisQuarter files")

        if (mustStartTime != '-'):
            mstart = time_transfer(mustStartTime, "courseInfo", line_number)
            mstartslot = math.floor(timeSlotName2Id(start_time, mstart))
            cur_course.mustStartSlot = max(cur_course.mustStartSlot, mstartslot) 
        
        if (mustEndTime != '-'):
            mend = time_transfer(mustEndTime, "courseInfo", line_number)
            mendslot = math.floor(timeSlotName2Id(start_time, mend - timedelta(hours=0, minutes=1)))
            # If both files have an end time, take the earlier one
            if (cur_course.mustEndSlot != -1):
                cur_course.mustEndSlot = min(cur_course.mustEndSlot, mendslot) 
            # If only courseInfo file have an end time, take it
            else:
                cur_course.mustEndSlot = mendslot

        # If end time is not specified in any file. By default, class will end by config['Class-default-end-time'])
        elif (cur_course.mustEndSlot == -1 and mustEndTime == '-'):
            mend = time_transfer(config['Class-default-end-time'], "config", -1)
            cur_course.mustEndSlot = math.floor(timeSlotName2Id(start_time, mend - timedelta(hours=0, minutes=1)))
        
        duration = cur_course.mustEndSlot - cur_course.mustStartSlot + 1
        if (duration < cur_course.slotNum):
            pdb.set_trace()
            sys.exit(f"End time minus start time for LING {cur_course.courseName} should be larger than course length.\
                    Please check courseInfo and courseThisQuarter files.")
    
    NonExemptedC.sort()

    return NonExemptedC, TotalNonExemptedHours

#################################################################################
def readCIline(values, course_instructor, line_number):
    '''
    Usage: read lines in courseInfo file.
    '''

    if (len(values) != 9):
        sys.exit(f"Warning: Incorrect CoursesInfo format for line {line_number}. Each row should have 9 columns.")

    course_name = values[0]
    course_name_before_slash = course_name.split('/')[0]
    
    #If the course is not taught this quarter, skip the line.
    if (course_name_before_slash.lower() not in course_instructor[0]):
        return -1, -1, -1, -1, -1, -1, -1, -1, -1, -1

    length_per_session = int(values[1])
    num_sessions_per_week = int(values[2])
    large_class = int(values[3])
    ten_percent_rule_exempted = int(values[4])
    is_a_TA_session = int(values[5])
    mustOnDays = values[6].lower()
    mustStartTime = values[7]
    mustEndTime = values[8]

    return course_name, course_name_before_slash, length_per_session, num_sessions_per_week, large_class, ten_percent_rule_exempted,\
        is_a_TA_session, mustOnDays, mustStartTime, mustEndTime

#################################################################################
def read_courseInfo(file_name, course_instructor, config):
    '''
    Usage: Read the courseInfo file and store all the parameters. 

    Input:
    file_name(string): courseInfo file's file name. e.g., './courseInfo'
    course_instructor(list): a list that stores all the information read from courseInstructor file

    Output:
    NonExemptedC(list): a list of course ids of non-exempted courses
    TotalNonExemptedHours(float): total number of non-exempted hours

    Format for courseInfo file:
    ###
    200       50 3   1 0   0 
    200AA     50 2   0 0   1
    ###
    '''

    CourseName2Id = course_instructor[0]
    CourseInfo = course_instructor[5]
    information = []

    # Read the CourseInfo file
    line_number = 0
    if file_name.endswith('.csv'):
        with open(file_name, 'r', newline='') as csvfile:
                csv_reader = csv.reader(csvfile)

                # Skip the header line
                header = next(csv_reader, None)
                line_number += 1
                
                # Iterate through the remaining lines
                for values in csv_reader:
                    line_number += 1

                    # Skip empty lines or line starting with '#'
                    if not any(values) or values[0].startswith('#'):
                        continue

                    course_name, course_name_before_slash, length_per_session, num_sessions_per_week, large_class, ten_percent_rule_exempted,\
                        is_a_TA_session, mustOnDays, mustStartTime, mustEndTime\
                        = readCIline(values, course_instructor, line_number)
                    
                    if (course_name != -1):
                        information.append([course_name, course_name_before_slash, length_per_session, num_sessions_per_week, large_class, ten_percent_rule_exempted,\
                            is_a_TA_session, mustOnDays, mustStartTime, mustEndTime, line_number])

    else:
        with open(file_name, "r") as file:
            for line in file:
                line_number += 1

                # Ignore empty lines and lines starting with "#"
                if not line.strip() or line.startswith("#"):
                    continue

                # Split the line into values and create a CourseInfo object
                values = line.strip().split('#')[0].split()

                course_name, course_name_before_slash, length_per_session, num_sessions_per_week, large_class, ten_percent_rule_exempted,\
                    is_a_TA_session, mustOnDays, mustStartTime, mustEndTime\
                    = readCIline(values, course_instructor, line_number)

                if (course_name != -1):
                    information.append([course_name, course_name_before_slash, length_per_session, num_sessions_per_week, large_class, ten_percent_rule_exempted,\
                        is_a_TA_session, mustOnDays, mustStartTime, mustEndTime, line_number])

    CourseInfoFromCI(information, config, CourseInfo, CourseName2Id)

    NonExemptedC, TotalNonExemptedHours = CourseInfoFromCI(information, config, CourseInfo, CourseName2Id)

    return NonExemptedC, TotalNonExemptedHours

#################################################################################
def read_conflict(file_name, course_instructor):
    '''
    Usage: Read the conflict file and store all the parameters. 

    Input:
    file_name(string): conflict file's file name. e.g., './ConflictCourses'
    course_instructor(list): a list that stores all the information read from courseInstructor file

    Output:
    conflict_course_pairs(set): a set of conflicted course pair, e.g., {(13, 14), (13, 17)}

    Format for conflict file:
    ###
    566 567 570 571 572 573 574 575-guest1 575-guest2 575-guest3 575-Xia 575-Ben 575-Levow 575-Ste
    450/550 566 570 571 
    ###
    '''

    CourseName2Id = course_instructor[0]
    Instructor2Courses = course_instructor[4]
    conflict_course_pairs = set()

    with open(file_name, "r") as file:
        for line in file:
            # Ignore empty lines and lines starting with "#"
            if not line.strip() or line.startswith("#"):
                continue
            courses = line.split('#')[0].strip().split()
            
            # Adding conflicted pairs from conflicted files
            course_ids = [CourseName2Id[course.split('/')[0].lower()] for course in courses if course.split('/')[0].lower() in CourseName2Id]
            for i in range(len(course_ids)-1):
                #print out the course name for i
                for j in range(i + 1, len(course_ids)):
                    #print out the course name for j
                    conflict_course_pairs.add((min(course_ids[i], course_ids[j]), max(course_ids[i], course_ids[j])))

    # Adding conflicted pairs from same instructors 
    for key in Instructor2Courses.keys():
        # We don't assume '-' is the same instructor, so we only care about instructor whose id is not -1 and have multiple courses
        if (key != -1 and len(Instructor2Courses[key]) > 1): 
            course_ids = Instructor2Courses[key]
            for i in range(len(course_ids)-1):
                for j in range(i + 1, len(course_ids)):
                    conflict_course_pairs.add((min(course_ids[i], course_ids[j]), max(course_ids[i], course_ids[j])))

    return conflict_course_pairs

#################################################################################
def print_conflictPairs(conflict_course_pairs, course_instructor):
    '''
    Usage: Print our conflicted course pairs in stderr file

    Input:
    conflict_course_pairs(list): a list of conflicted course pair generated from read_conflit() function
    course_instructor(list): a list that stores all the information read from courseInstructor file generated from read_courseInstructor() function
    '''

    #print conflicted course pairs that are taught in this quarter in stderr
    InstructorId2Name = course_instructor[3]
    CourseInfo = course_instructor[5]
    print(f'', file=sys.stderr)
    for (c1,c2) in conflict_course_pairs:
        if (CourseInfo[c1].instructorId != CourseInfo[c2].instructorId):
            print(f'{CourseInfo[c1].courseName}, {CourseInfo[c2].courseName} are conflicted', file=sys.stderr)

    print(f'', file=sys.stderr)
    for (c1,c2) in conflict_course_pairs:
        if (CourseInfo[c1].instructorId == CourseInfo[c2].instructorId):
            print(f'{CourseInfo[c1].courseName}, {CourseInfo[c2].courseName} are conflicted because they are taught by {InstructorId2Name[CourseInfo[c1].instructorId]}', file=sys.stderr)
    print(f'', file=sys.stderr)

    return

#################################################################################
def setDefaultInsPref(prefStartTime, prefEndTime, prefDays, config, line_number):
    '''
    Usage: if a instructor does not have preference, set default value for him/her

    Input: 
    prefStartTime(string): prefered starting time for an instructor, could be '-' or a specific time, e.g., "9:30"
    prefStartTime(string): prefered ending time for an instructor, could be '-' or a specific time, e.g., "14:30"
    prefDays(string): prefered days for an instructor, e.g., 'TR'
    config(dict): a dictionary that store all the information from config file.

    Output:
    prefStartSlot(int): prefered starting time's slotId, e.g., 0
    prefEndSlot(int): prefered ending time's slotId, e.g., 19
    prefDayList(list): prefered days' list, e.g., [1,3,4] which means M, W, and R are prefered.
    '''

    #Set default value
    start_time = time_transfer(config['InstructDayStartsAt'], "config", -1)
    if (prefStartTime == '-'):
        prefStartSlot = 0
    else:
        pstart = time_transfer(prefStartTime, "insPref", line_number)
        prefStartSlot = math.floor(timeSlotName2Id(start_time, pstart))
    if (prefEndTime == '-'):
        prefEndSlot = config['SlotNumPerday'] - 1
    else:
        pend = time_transfer(prefEndTime, "insPref", line_number)
        prefEndSlot = math.floor(timeSlotName2Id(start_time, pend - timedelta(hours=0, minutes=1)))
    if (prefDays == '-'):
        prefDayList = [0,1,2,3,4]
    else:
        prefDayList = days2listint(prefDays, "InsPref", line_number)

    return prefStartSlot, prefEndSlot, prefDayList

#################################################################################
def readInsPrefline(values, line_number):
    '''
    Usage: Read lines in inspref file

    Input:
    values(list): e,g., ['Bender', 'TRF', '-', '-', '1']
    line_number(int): the line number in txt file or csv file

    Output:
    instructor_name(string): e.g., 'bender'
    prefDays(string): e.g., 'trf'
    prefStartTime(string): e.g., '-'
    prefEndTime(string): e.g., '-'
    sameDay(string): e.g., '1'
    '''

    if (len(values) != 5):
        sys.exit(f"Incorrect InstructorPref format for line {line_number}. Each row should have 5 columns.")
    instructor_name = values[0]
    prefDays = values[1].lower()
    prefStartTime = values[2]
    prefEndTime = values[3]
    sameDay = values[4]

    return instructor_name, prefDays, prefStartTime, prefEndTime, sameDay

#################################################################################
def processInsPref(information, InstructorName2Id, Instructor2Courses, config, CourseInfo, IW, line_number):
    '''
    Usage: processing insPref file, adding sameDay pairs, setting up IW matrix.
    '''

    instructor_in_insPref = [] 
    SameDayPairs = set()
    for instructor_name, prefDays, prefStartTime, prefEndTime, sameDay in information:
        InstructorID = InstructorName2Id[instructor_name.lower()]

        instructor_in_insPref.append(InstructorID)
        course_ids = Instructor2Courses[InstructorID]

        if (config["Assume-same-day-if-not-specified"] == 0\
            and sameDay == '1' and len(course_ids) > 1):
            for i in range(len(course_ids)-1):
                for j in range(i + 1, len(course_ids)):
                    if (CourseInfo[course_ids[i]].sessionsPerWeek <= CourseInfo[course_ids[j]].sessionsPerWeek):
                        SameDayPairs.add((course_ids[i], course_ids[j]))
                    else:
                        SameDayPairs.add((course_ids[j], course_ids[i]))  

        prefStartSlot, prefEndSlot, prefDayList = setDefaultInsPref(prefStartTime, prefEndTime, prefDays, config, line_number)

        for c in course_ids:
            for d in prefDayList:
                for t in range(prefStartSlot, prefEndSlot - math.ceil(CourseInfo[c].lengPerSession/30) + 1):
                    try:
                        IW[c][d][t] = 1 / CourseInfo[c].sessionsPerWeek
                    except:
                        sys.exit(f"CourseInfo for {CourseInfo[c].courseName} fail to find")
                    if (1 / CourseInfo[c].sessionsPerWeek < 0):
                        sys.exit(f"CourseInfo for {CourseInfo[c].courseName} fail to find")

    return instructor_in_insPref, SameDayPairs, IW

#################################################################################
def read_instructorPref(file_name, course_instructor, config):
    '''
    Usage: Read the instructor preference file and create matrix IW(instructor pref weight). 

    Input:
    file_name(string): instructor preference file's file name. e.g., './InstructorPref'.
    course_instructor(list): a list that stores all the information read from courseInstructor file.
    config(dict): a dictionary that store all the information read from config file. 

    Output:
    IW(list): Instructor preference weight matrix. IW[c][d][s] = 1/CourseInfo[c].sessionsPerWeek if the slot is prefered and = 0 otherwise; where c is courseId, d is day, s is slotId. 
    SameDayPairs:  a set of course pairs that insrtuctors want them to be on the same day, e.g., {(16, 14), (8, 9), (4, 1), (5, 6)}.
    instructor_in_insPref(list): a list of instructor id who appears in insturctorPref file. e.g., [7, 8, 5, 1, 3, 10, 2, 13]

    Format for instructorPref file:
    ###
    Ferjan-Ramirez   -     -     14:30   1
    Xia              TR   10:30   -      1
    ###
    '''

    InstructorName2Id = course_instructor[2]
    InstructorId2Name = course_instructor[3]
    Instructor2Courses = course_instructor[4]
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    IW = [[[0 for _ in range(config['SlotNumPerday'])] for _ in range(5)] for _ in range(TotalCourseNum)]
    line_number = 0
    information = []

    if file_name.endswith('.csv'):
        with open(file_name, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)

            # Skip the header line
            header = next(csv_reader, None)
            line_number += 1

            # Iterate through the remaining lines
            for values in csv_reader:
                line_number += 1

                # Skip empty lines or line starting with '#'
                if not any(values) or values[0].startswith('#'):
                    continue

                instructor_name, prefDays, prefStartTime, prefEndTime, sameDay = readInsPrefline(values, line_number)
                if (instructor_name.lower() not in InstructorName2Id):
                    continue
                information.append([instructor_name, prefDays, prefStartTime, prefEndTime, sameDay])

    else:
        with open(file_name, "r") as file:
            for line in file:
                line_number += 1
                # Ignore empty lines and lines starting with "#"
                if not line.strip() or line.startswith("#"):
                    continue

                values = line.strip().split()
                instructor_name, prefDays, prefStartTime, prefEndTime, sameDay = readInsPrefline(values, line_number)
                if (instructor_name.lower() not in InstructorName2Id):
                    continue
                information.append([instructor_name, prefDays, prefStartTime, prefEndTime, sameDay])

    instructor_in_insPref, SameDayPairs, IW = processInsPref(information, InstructorName2Id, Instructor2Courses, config, CourseInfo, IW, line_number)
               
    insNotInPref(TotalCourseNum, CourseInfo, instructor_in_insPref, InstructorId2Name)   
    if (config["Assume-same-day-if-not-specified"] == 1):
        addSameDayPairs(Instructor2Courses, SameDayPairs, CourseInfo)

    return IW, SameDayPairs, instructor_in_insPref

#################################################################################
def addSameDayPairs(Instructor2Courses, SameDayPairs, CourseInfo):
    '''
    Usage: If Assume-same-day-if-not-specified is 1, we add all the courses taught by the same instructor
            to same day pairs

    Input:
    Instructor2Courses(defaultdict)
    SameDayPairs(set)
    CourseInfo(list)
    '''

    for instructor_id, course_ids in Instructor2Courses.items():
        if len(course_ids) > 1:
            for i in range(len(course_ids)-1):
                for j in range(i + 1, len(course_ids)):
                        if (CourseInfo[course_ids[i]].sessionsPerWeek <= CourseInfo[course_ids[j]].sessionsPerWeek):
                            SameDayPairs.add((course_ids[i], course_ids[j]))
                        else:
                            SameDayPairs.add((course_ids[j], course_ids[i]))  

    return

#################################################################################
def insNotInPref(TotalCourseNum, CourseInfo, instructor_in_insPref, InstructorId2Name):
    '''
    Usage: For TA sessions or guest lecturer's sessions that we can't find insturctors' pref, we print a warning

    Input:
    TotalCourseNum(int): total number of course.
    CourseInfo(list): CourseInfo[courseId] is a Course class that stores course information we read from CourseInfo and CourseThisQuarter.
    instructor_in_insPref(list): instructor id for those who appear in instructor pref file.
    InstructorId2Name(list): maps from Instructor id to Instructor name.
    '''

    instructor_notIn_insPref = set()
    for c in range(TotalCourseNum):
        if (CourseInfo[c].sessionsPerWeek < 0):
            print(f"{CourseInfo[c].courseName} has incorrect session num. Please check CourseInfo file")
            sys.exit("incorrect session Num")
        if (CourseInfo[c].instructorId not in instructor_in_insPref):
            instructor_notIn_insPref.add(InstructorId2Name[CourseInfo[c].instructorId])
    for i in instructor_notIn_insPref:
        print(f"Warning: {i} doesn't appear in the instructor preference file", file=sys.stderr)
    
    return

#################################################################################
def createCW(course_instructor, config):
    '''
    Usage: Create matrix CW (UW policy's weight)

    Input:
    course_instructor(list): a list that stores all the information we read from courseInstructor file.
    config(dict): a dictionary that stores all the information we read from config file.

    output:
    CW(list): UW policy weight matrix. CW[c][d][s] where c is courseId, d is day, s is slotId. 
    '''

    # Create matrix CW (UW policy's weight)
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    BlockingSlot = list(range(config['BlockSchedulingStartsAtid'], config['BlockSchedulingEndsAtid'] + 1))
    CW = [[[0 for _ in range(config['SlotNumPerday'])] for _ in range(5)] for _ in range(TotalCourseNum)]
    
    penalty = config['Penalty-for-violating-block-policy']
    for c in range(TotalCourseNum):
        match CourseInfo[c].lengPerSession:
            case 50:
                for d in range(5):
                    for t in BlockingSlot:
                        CW[CourseInfo[c].courseId][d][t] = penalty / CourseInfo[c].sessionsPerWeek
                    for t in config['50-min-class-start-time']:
                        CW[CourseInfo[c].courseId][d][t] = 1 / CourseInfo[c].sessionsPerWeek
            case 80:
                for d in range(5):
                    for t in BlockingSlot:
                        CW[CourseInfo[c].courseId][d][t] = penalty / CourseInfo[c].sessionsPerWeek
                    for t in config['80-min-class-start-time']:
                        CW[CourseInfo[c].courseId][d][t] = 1 / CourseInfo[c].sessionsPerWeek
            case 110:
                for d in range(5):
                    for t in BlockingSlot:
                        CW[CourseInfo[c].courseId][d][t] = penalty / CourseInfo[c].sessionsPerWeek
                    for t in config['110-min-class-start-time']:
                        CW[CourseInfo[c].courseId][d][t] = 1 / CourseInfo[c].sessionsPerWeek 
            case 170:
                for d in range(5):
                    for t in BlockingSlot:
                        CW[CourseInfo[c].courseId][d][t] = penalty / CourseInfo[c].sessionsPerWeek
                    for t in config['170-min-class-start-time']:
                        CW[CourseInfo[c].courseId][d][t] = 1 / CourseInfo[c].sessionsPerWeek  

    return CW

#################################################################################
def addConstraints(problem, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs, X, Y):
    '''
    Usage: adding constraints for ILP 

    Input:
    problem(pulp): ILP problem we defined using pulp
    course_instructor(list)
    config(dict)
    conflict_course_pairs(set)
    NonExemptedC(list): e.g., [0, 1, 2, 3, 4, 5]
    TotalNonExemptedHours(float): 
    SameDayPairs(set)
    X(list): variable X for our ILP problem. X[c][d][s] = 1 means course c start at slot s on day d.
    Y(list): variable Y for our ILP problem. Y[c][d][s] = 1 means course c durates at slot s on day d.
    '''

    TotalCourseNum = course_instructor[6]
    CourseInfo = course_instructor[5]
    totalSlot = config['SlotNumPerday']
    addMatrixYC(problem, TotalCourseNum, CourseInfo, totalSlot, X, Y)
    addSessionC(problem, TotalCourseNum, CourseInfo, totalSlot, X, config)
    addTwiceAWeekC(problem, TotalCourseNum, CourseInfo, totalSlot, X)
    addThreeTimesAWeekC(problem, TotalCourseNum, CourseInfo, totalSlot, X)
    addConflictedC(problem, conflict_course_pairs, totalSlot, Y)
    add10PercentC(problem, config,TotalNonExemptedHours, NonExemptedC, Y)
    addSamedayC(problem, config, SameDayPairs, CourseInfo, totalSlot, X)
    addLatestStartC(problem, TotalCourseNum, totalSlot, CourseInfo, config, X)
    addMustTimeC(problem, TotalCourseNum, totalSlot, CourseInfo, X)
    addBlockC(problem, TotalCourseNum, CourseInfo, config, X)

    return

#################################################################################
def addMatrixYC(problem, TotalCourseNum, CourseInfo, totalSlot, X, Y):
    '''
    Usage: adding Constraint 1: Matrix Y must be consistent with Matrix X

    Input:
    problem(pulp)
    TotalCourseNum(int)
    CourseInfo(list)
    totalSlot(int)
    X(list)
    Y(list)
    '''

    for c in range(TotalCourseNum):
        slotNum = CourseInfo[c].slotNum
        for d in range(5):
            problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) * slotNum == pulp.lpSum(Y[c][d][t] for t in range(totalSlot))
            for t in range(totalSlot):
                for j in range(t, min(t + slotNum, totalSlot)):
                    problem += Y[c][d][j] >= X[c][d][t]
    
    return

#################################################################################
def addSessionC(problem, TotalCourseNum, CourseInfo, totalSlot, X, config):
    '''
    Usage: adding Constraint 2: Each course must meet the correct number of times per week

    Input:
    problem(pulp)
    TotalCourseNum(int)
    CourseInfo(list)
    totalSlot(int)
    X(list)
    '''

    for c in range(TotalCourseNum):
        sessionsPerWeek = CourseInfo[c].sessionsPerWeek
        #If CoursesThisQuarter includes a course that is not in CourseInfo, exit.
        if (sessionsPerWeek < 1):
            sys.exit(f"course {CourseInfo[c].courseName} is not found in CourseInfo.\
                     Please either add the course to CourseInfo or remove it from '{config['CourseInstructor']}'")
            
        #Total sessions taught in a week equal to sessionsPerWeek
        problem += pulp.lpSum(X[c][d][t] for d in range(5) for t in range(totalSlot)) == sessionsPerWeek

        #Each course meet at most once per day
        for d in range(5):
            problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) <= 1
    
    return

#################################################################################
def addTwiceAWeekC(problem, TotalCourseNum, CourseInfo, totalSlot, X):
    '''
    Usage: adding Constraint 3: Each course that meets twice per week must be taught on MW or TR
           (This should be for regular courses, but by coincident, it also works for TA session.)

    Input:
    problem(pulp)
    TotalCourseNum(int)
    CourseInfo(list)
    totalSlot(int)
    X(list)
    '''

    for c in range(TotalCourseNum):
        if CourseInfo[c].sessionsPerWeek == 2: 
            for t in range(totalSlot):
                problem += X[c][1][t] == X[c][3][t]   # T and R have the same schedule
                problem += X[c][0][t] == X[c][2][t]   # M and W have the same schedule
            # not meet on Friday
            problem += pulp.lpSum(X[c][4][t] for t in range(totalSlot)) == 0

            if CourseInfo[c].largeClass == 1:
                # must meet on T and R
                problem += pulp.lpSum(X[c][1][t] for t in range(totalSlot)) == 1
                problem += pulp.lpSum(X[c][3][t] for t in range(totalSlot)) == 1

    return

#################################################################################
def addThreeTimesAWeekC(problem, TotalCourseNum, CourseInfo, totalSlot, X):
    '''
    Usage: adding Constraint 4: Courses that meet three times per week must be taught on MWF

    Input:
    problem(pulp)
    TotalCourseNum(int)
    CourseInfo(list)
    totalSlot(int)
    X(list)
    '''

    for c in range(TotalCourseNum):
        if CourseInfo[c].sessionsPerWeek == 3: 
            # must meet on M, W, F
            problem += pulp.lpSum(X[c][0][t] for t in range(totalSlot)) == 1
            problem += pulp.lpSum(X[c][2][t] for t in range(totalSlot)) == 1
            problem += pulp.lpSum(X[c][4][t] for t in range(totalSlot)) == 1
            # M, W, and F have the same schedule
            for t in range(totalSlot):
                problem += X[c][0][t] == X[c][2][t]   
                problem += X[c][0][t] == X[c][4][t] 

    return  

#################################################################################
def addConflictedC(problem, conflict_course_pairs, totalSlot, Y):
    '''
    Usage: adding Constraint 5: Conflicted courses should not overlap in time

    Input:
    problem(pulp)
    conflict_course_pairs(set)
    totalSlot(int)
    Y(list)
    '''

    for (c1, c2) in conflict_course_pairs:
        for d in range(5):
            for t in range(totalSlot):
                problem += Y[c1][d][t] + Y[c2][d][t] <= 1
    
    return

#################################################################################
def add10PercentC(problem, config, TotalNonExemptedHours, NonExemptedC, Y):
    '''
    Usage: adding Constraint 5: Meet the 10%-rule requirement

    Input:
    problem(pulp)
    config(dict)
    TotalNonExemptedHour(float)
    Y(list)
    '''
    target = math.ceil(config['RulePercentage'] * TotalNonExemptedHours)
    for t in range(config['10PercRuleStartsAtid'], config['10PercRuleEndsAtid'] + 1, 2):
        t1 = pulp.lpSum(Y[c][d][t] for c in NonExemptedC for d in range(5))
        t2 = pulp.lpSum(Y[c][d][t + 1] for c in NonExemptedC for d in range(5))
        problem += t1 + t2 <= 2 * target

#################################################################################
def addSamedayC(problem, config, SameDayPairs, CourseInfo, totalSlot, X):
    '''
    Usage: adding Constraint 7: Whether SameDay preferences are treated as hard constraint is specified in config file

    Input:
    problem(pulp)
    config(dict)
    SameDayPairs(set)
    CourseInfo(list)
    totalSlot(int): total number of slot in a day
    X(list)
    '''

    sameday = config['Treat-same-day-preference-as-hard-constraint']
    if (sameday == 1):
        for (c1, c2) in SameDayPairs:
            assert (CourseInfo[c1].sessionsPerWeek <= CourseInfo[c2].sessionsPerWeek)
            for d in range(5):
                problem += pulp.lpSum(X[c1][d][t] for t in range(totalSlot)) <= pulp.lpSum(X[c2][d][t] for t in range(totalSlot))
    
    return

#################################################################################
def addLatestStartC(problem, TotalCourseNum, totalSlot, CourseInfo, config, X):
    '''
    Usage: adding Constraint 8: X's time later than InstructDayEndsAt - course length should be set to 0

    Input:
    problem(pulp)
    TotalCourseNum(int)
    totalSlot(int): total number of slot in a day
    CourseInfo(list)
    config(dict)
    X(list)
    '''
    
    for c in range(TotalCourseNum):
        for d in range(5):
            for t in range(totalSlot - CourseInfo[c].slotNum + 1, config['SlotNumPerday']):
                problem += X[c][d][t] == 0
    
    return

#################################################################################
def addMustTimeC(problem, TotalCourseNum, totalSlot, CourseInfo, X):
    '''
    Usage: adding Constraint 9: mustOnDays, mustStartSlot and mustEndSlot

    Input:
    problem(pulp)
    TotalCourseNum(int)
    totalSlot(int): total number of slot in a day
    CourseInfo(list)
    X(list)
    '''

    for c in range(TotalCourseNum):
        if (CourseInfo[c].mustOnDays != []):
            # Course must be on specific days
            d1 = CourseInfo[c].mustOnDays
            for d in [0,1,2,3,4]:
                if (d in d1):
                    problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) == 1
                else:
                    problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) == 0

        if (CourseInfo[c].mustStartSlot != -1):
            for d in range(5):
                for t in range(0, CourseInfo[c].mustStartSlot):
                    problem += X[c][d][t] == 0

        if (CourseInfo[c].mustEndSlot != -1):
            for d in range(5):
                for t in range(CourseInfo[c].mustEndSlot - CourseInfo[c].slotNum + 2, totalSlot):
                    problem += X[c][d][t] == 0
    
    return

#################################################################################
def addBlockC(problem, TotalCourseNum, CourseInfo, config, X):
    '''
    Usage: adding Constraint 10: If must-follow-block-policy is 1, we set corresponding X value

    Input:
    problem(pulp)
    TotalCourseNum(int)
    CourseInfo(list)
    config(list)
    X(list)
    '''

    BlockingSlot = list(range(config['BlockSchedulingStartsAtid'], config['BlockSchedulingEndsAtid'] + 1))
    if (config['Must-follow-block-policy'] == 1):
        for c in range(TotalCourseNum):
            match CourseInfo[c].lengPerSession:
                case 50:
                    for d in range(5):
                        for t in BlockingSlot:
                            if (t not in config['50-min-class-start-time']):
                                problem += X[c][d][t] == 0
                case 80:
                    for d in range(5):
                        for t in BlockingSlot:
                            if (t not in config['80-min-class-start-time']):
                                problem += X[c][d][t] == 0
                case 110:
                    for d in range(5):
                        for t in BlockingSlot:
                            if (t not in config['110-min-class-start-time']):
                                problem += X[c][d][t] == 0
                case 170:
                    for d in range(5):
                        for t in BlockingSlot:
                            if (t not in config['170-min-class-start-time']):
                                problem += X[c][d][t] == 0

    return

#################################################################################
def defineXY(X, Y, TotalCourseNum, totalSlot, type):
    '''
    Usage: Define variable X and Y. Their types can be either binary or continous depending on it is a ILP problem or LP problem.
    
    Input:
    X(list): an empty list
    Y(list): an empty list
    TotalCourseNum(int)
    totalSlot(int)
    type(string): either "binary" or "continous"
    '''

    for c in range(TotalCourseNum):
        X_c = []
        Y_c = []
        for d in range(5):
            X_d = []
            Y_d = []
            for t in range(totalSlot):
                if (type == 'binary'):
                    X_d.append(pulp.LpVariable(f"X_{c}_{d}_{t}", 0, 1, cat=pulp.LpBinary))
                    Y_d.append(pulp.LpVariable(f"Y_{c}_{d}_{t}", 0, 1, cat=pulp.LpBinary))
                else:
                    X_d.append(pulp.LpVariable(f"X_{c}_{d}_{t}", 0, 1, cat='Continuous'))
                    Y_d.append(pulp.LpVariable(f"Y_{c}_{d}_{t}", 0, 1, cat='Continuous'))

            X_c.append(X_d)
            Y_c.append(Y_d)
        X.append(X_c)
        Y.append(Y_c)
    
    return

#################################################################################
def readParameterForProblem(course_instructor, config):
    '''
    Usage: read parameters for ILP/LP problem

    Input:
    course_instructor(list)
    config(dict)

    Output:
    TotalCourseNum(int)
    totalSlot(int)
    l1(float): weight for CW matrix
    l2(float): weight for IW matrix
    '''

    TotalCourseNum = course_instructor[6]
    totalSlot = config['SlotNumPerday']
    l1 = config['UWPolicyWeight']
    l2 = config['InstructorPrefWeight']

    return TotalCourseNum, totalSlot, l1, l2

#################################################################################
def solveProblem(problem):
    '''
    Usage: this function will set time limit for ILP/LP, call a solver, and then solve it.

    Input: problem(pulp)
    '''
    pulp.LpSolverDefault.timeLimit = 15 #Set the time limit for pulp solver
    solver = pulp.getSolver('COIN_CMD', timeLimit=15)
    problem.solve(solver)

    return

#################################################################################
def ILP(IW, CW, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs):
    '''
    Usage: Define an ILP problem then solve it.

    Input:
    IW(list): instructor preference weight matrix
    CW(list): UW policy weight matrix
    course_instructor(list)
    conflict_course_pairs(set)
    NonExemptedC(list)
    TotalNonExemptedHours(float)
    SameDayPairs(list)
    output_dir(string): the directory where output will be generated

    Output:
    X(list)
    Y(list)
    problem(pulp)
    '''

    # Read parameters for ILP problem
    TotalCourseNum, totalSlot, l1, l2 = readParameterForProblem(course_instructor, config)

    # Create the ILP problem
    problem = pulp.LpProblem("ILP_Maximization_Problem", pulp.LpMaximize)
    
    # Initialize variable X and Y (three dimensional array)
    X = []
    Y = []
    defineXY(X, Y, TotalCourseNum, totalSlot, "binary")

    # objective function
    problem +=  pulp.lpSum((l1 * CW[c][d][t] + l2 * IW[c][d][t]) * X[c][d][t] for c in range(TotalCourseNum) for d in range(5) for t in range(totalSlot))
    
    #adding constraints
    addConstraints(problem, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs, X, Y)

    #solve problem
    solveProblem(problem)

    if (pulp.LpStatus[problem.status] != 'Optimal'):
        sys.exit("Pulp fail to find an optimal solution.") 

    return X, Y, problem

#################################################################################
def LP(IW, CW, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs):
    '''
    Usage: Define an LP problem then solve it. Only differences with ILP() is we set the varaible to be continuous instead of binary

    Output: 
    upper_bound(float): the optimal value of the LP problem, which is the upper bound for the ILP problem.
    '''

    # Read parameters for LP problem
    TotalCourseNum, totalSlot, l1, l2 = readParameterForProblem(course_instructor, config)

    # Create the LP problem
    problem = pulp.LpProblem("LP_Maximization_Problem", pulp.LpMaximize)
    
    # Initialize variable X and Y (three dimensional array)
    X = []
    Y = []
    defineXY(X, Y, TotalCourseNum, totalSlot, "continuous")

    # objective function
    problem +=  pulp.lpSum((l1 * CW[c][d][t] + l2 * IW[c][d][t]) * X[c][d][t] for c in range(TotalCourseNum) for d in range(5) for t in range(totalSlot))
    
    #adding constraints
    addConstraints(problem, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs, X, Y)

    #solve problem
    solveProblem(problem)

    if (pulp.LpStatus[problem.status] != 'Optimal'):
        sys.exit("Pulp fail to find an optimal solution for LP.")  
    upper_bound =pulp.value(problem.objective)

    return upper_bound

#################################################################################
def computeCWIWPoint(course_instructor, config, X, IW, CW):
    '''
    Usage: Compute IW and CW points earned from objective function

    Input:
    course_instructor(list)
    config(dict)
    X(list)
    IW(list)
    CW(list)

    Output: 
    IW_point(float): IW points earned from objective function
    CW_point(float): CW points earned from objective function
    '''

    TotalCourseNum = course_instructor[6]
    totalSlot = config['SlotNumPerday']
    CW_point = 0
    IW_point = 0
    for c in range(TotalCourseNum):
        for d in range(5):
            for t in range(totalSlot):
                CW_point += CW[c][d][t] *  X[c][d][t].varValue
                IW_point += IW[c][d][t] *  X[c][d][t].varValue

    return IW_point, CW_point

#################################################################################
def generate_output(X, output_dir, course_instructor, config, IW, instructor_in_insPref):
    '''
    Usage: generate schedule.txt based on X.varValue we get from ILP problem

    Input:
    X(list)
    output_dir(string)
    course_instructor(list)
    config(dict)
    IW(list)
    instructor_in_insPref(list): instructor id for those who appear in instrutcor pref file

    Output:
    NumCNoPref(int): total number of courses that don't have an instructor preference (could be regular course or TA session)
    InsNotMet(defaultdict): instructor who has a preference that are not met. 
        key is the instructor id and value is a set of course names that didn't meet preference. e.g., {8: {'520'}})
    BPNotMet(set): a set of course names that didn't meet block policy. e.g., {'234', '233AH'}

    Format for schedule.txt file:
    ###
    200     	McGarrity           	MWF  	14:30   	15:20   	50   	-  	-  
    233     	Evans               	MWF  	08:30   	09:20   	50   	y  	y  
    ###
    '''

    InstructorId2Name = course_instructor[3]
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    start_time = time_transfer(config['InstructDayStartsAt'], "config", -1)
    totalSlot = config['SlotNumPerday']
    BlockingSlot = list(range(config['BlockSchedulingStartsAtid'], config['BlockSchedulingEndsAtid'] + 1))
    NumCNoPref = 0
    InsNotMet = defaultdict(set)
    BPNotMet = set()

    with open(output_dir+"schedule.txt", "w") as file:
        for c in range(TotalCourseNum):
            course_name = CourseInfo[c].courseName
            if (CourseInfo[c].instructorId != -1):
                instructor_name = InstructorId2Name[CourseInfo[c].instructorId]
            else:
                instructor_name = '-'  
            meetIP = 'y'
            days = []
            slots = set()
            
            for d in range(5):
                for t in range(totalSlot):
                    if (X[c][d][t].varValue >= 1):
                        if (IW[c][d][t] == 0):
                            meetIP = 'n'
                            if (CourseInfo[c].instructorId in instructor_in_insPref):
                                InsNotMet[CourseInfo[c].instructorId].add(course_name)
                        days.append(d)
                        slots.add(t)
            # If an instructor does not appear in the insPref file, we use '-'
            if (CourseInfo[c].instructorId not in instructor_in_insPref):
                meetIP = '-'
                NumCNoPref += 1

            slots = list(slots)
            if (len(slots) > 1):
                # print('more than one session in a day')
                sys.exit('more than one session in a day')  
            else:
                course_start = timeSlotId2ISlot(start_time, slots[0])

            teaching_days = ''.join(intlist2days(days))
            session_length = CourseInfo[c].lengPerSession
            course_end = (time_transfer(course_start, "config", -1) + timedelta(minutes=session_length)).strftime('%H:%M')
            
            meetBP = checkMeetBP(config, slots, session_length, BPNotMet, BlockingSlot, course_name)

            formatted_output = "{:<8}\t{:<20}\t{:<5}\t{:<8}\t{:<8}\t{:<5}\t{:<3}\t{:<3}\n"\
                .format(course_name, instructor_name, teaching_days, course_start, course_end, session_length, meetBP, meetIP)
            file.write(formatted_output)
    
    return NumCNoPref, InsNotMet, BPNotMet

#################################################################################
def checkMeetBP(config, slots, session_length, BPNotMet, BlockingSlot, course_name):
    '''
    Usage: check whether a course meet Block Policy or not

    Input: 
    config(dict)
    slots(dict): currently we only have one element in slots, which is slot id for a course
    session_length(int): session length for a course 
    BPNotMet(set): an set that contain course id that doesn't meet block policy
    BlockingSlot(list): slot id that are between block starting time and block ending time
    course_name(string): e.g., '200'

    Output: 
    meetBP(string): 'n' or 'y' or '-'. '-' means its before block starting time or after block ending time. 
    '''

    meetBP = 'y'          
    #if course begin after 14:30, meetBP = '-'
    if (slots[0] > config['BlockSchedulingEndsAtid'] or slots[0] < config['BlockSchedulingStartsAtid']):
        meetBP = '-'
    #if course begin before 14:30 and violates block policy, meetBP = 'n'
    else:
        match session_length:
            case 50:
                for s in slots:
                    if (s in BlockingSlot and s not in config['50-min-class-start-time']):
                        meetBP = 'n'
                        BPNotMet.add(course_name)
            case 80:
                for s in slots:
                    if (s in BlockingSlot and s not in config['80-min-class-start-time']):
                        meetBP = 'n'
                        BPNotMet.add(course_name)
            case 110:
                for s in slots:
                    if (s in BlockingSlot and s not in config['110-min-class-start-time']):
                        meetBP = 'n'
                        BPNotMet.add(course_name)
            case 170:
                for s in slots:
                    if (s in BlockingSlot and s not in config['170-min-class-start-time']):
                        meetBP = 'n'
                        BPNotMet.add(course_name)

    return meetBP

#################################################################################
def generateHeatMap(Y, output_dir, config, NonExemptedC, TotalNonExemptedHours):
    '''
    Usage: generate heatmap.txt based on Y.varValue we get from ILP problem

    Input:
    Y(list)
    output_dir(string)
    config(dict)
    NonExemptedC(list): a list of non-exempted course's course id
    TotalNonExemptedHours(float)

    Format for headtmap.txt file:
    ###
        M	T	W	R	F	Hourly total	Hourly Target
    08:30	2.0	2.0	2.0	3.0	1.0	10.0    	10  
    ###
    '''

    start_slot = config['10PercRuleStartsAtid']
    start_time = time_transfer(config['10PercRuleStartsAt'], "config", -1)
    end_slot = config['10PercRuleEndsAtid']
    target_value = math.ceil(TotalNonExemptedHours * config['RulePercentage'])
    with open(output_dir+"heatMap.txt", "w") as file:
        file.write(f"\tM\tT\tW\tR\tF\tHourly total\tHourly Target\n")
        for i in range(start_slot, end_slot + 1, 2):
            time = timeSlotId2ISlot(start_time, i)
            weekly_sum = []
            for d in range(5):
                total_sum = 0
                for c in NonExemptedC:                    
                    total_sum += (Y[c][d][i].varValue / 2)
                    total_sum += (Y[c][d][i+1].varValue / 2)
                weekly_sum.append(total_sum)
            formatted_output = "{:<5}\t{:<3}\t{:<3}\t{:<3}\t{:<3}\t{:<3}\t{:<8}\t{:<8}\n".format(time, weekly_sum[0], weekly_sum[1], weekly_sum[2], weekly_sum[3], weekly_sum[4], sum(weekly_sum), target_value)
            file.write(formatted_output)

    return

#################################################################################
def printStandardOutput(config, course_instructor, NonExemptedC, TotalNonExemptedHours, IW_point, CW_point, NumCNoPref, InsNotMet, BPNotMet, problem, upper_bound):
    '''
    Usage: print out some useful information in stderr file

    Input:
    config(dict): parameters read from config file
    course_instructor(list): information read from course instructor(courseThisQuarter) file
    NonExemptedC(list): a list of non-exempted course's course id
    TotalNonExemptedHours(float): total number of non exempted hours
    IW_point(float): points earned from instructor preference weight
    CW_point(float): points earned from UW policy weight
    NumCNoPref(int): number of course that doesn't have an instructor preference
    InsNotMet(defaultdict): instructor who has a preference that are not met. 
        key is the instructor id and value is a set of course names that didn't meet preference. e.g., {8: {'520'}})
    BPNotMet(set): a set of course names that didn't meet block policy. e.g., {'234', '233AH'}
    problem(pulp): ILP problem we defined using pulp
    upper_bound(float): optimal value calculated from LP problem
    '''

    InstructorId2Name = course_instructor[3]
    print(f"10%-rule-percentage={config['RulePercentage']}", file=sys.stderr)
    print(f"Must-follow-block-policy={config['Must-follow-block-policy']}\n", file=sys.stderr)
    print(f"Result: {pulp.LpStatus[problem.status]}", file=sys.stderr)
    print(f"Objective value: {pulp.value(problem.objective)}", file=sys.stderr)
    print(f"Upper bound: {upper_bound}", file=sys.stderr) # Upper bound is the optimal value for LP problem
    print(f"IW points earned: {IW_point}", file=sys.stderr)
    print(f"CW points earned: {CW_point}", file=sys.stderr)
    courseID2Name = course_instructor[1]
    NonExemptedCName = [courseID2Name[course_id] for course_id in NonExemptedC]
    TotalC = list(range(course_instructor[6]))
    ExemptedC = [c for c in TotalC if c not in NonExemptedC]
    ExemptedCName = [courseID2Name[course_id] for course_id in ExemptedC]
    print(f"Total Number of Course: {course_instructor[6]}", file=sys.stderr)
    print(f"Exempted Courses List: {ExemptedCName}", file=sys.stderr)
    print(f"Total Number of Non-Exempted Courses: {len(NonExemptedCName)}", file=sys.stderr)
    print(f"Total Number of Non-Exempted Hours: {TotalNonExemptedHours}\n", file=sys.stderr)
    print(f"The number of courses for which the instructors are not listed in the instructorpref file: {NumCNoPref}", file=sys.stderr)
    print(f"The number of courses for which the instructors' preference are not met: {int(course_instructor[6] - IW_point - NumCNoPref)}", file=sys.stderr)
    if (len(InsNotMet) > 0):
        print(f"Instructors whose preference are not met: ", file=sys.stderr)
        for i in InsNotMet.keys():
            print(f"Instructor's name: {InstructorId2Name[i]}\tCourses that violate preference{InsNotMet[i]}", file=sys.stderr)
    print(f"\nThe number of courses that violate Block Policy: {len(BPNotMet)}", file=sys.stderr)
    if (len(BPNotMet) > 0):
        print(f"Courses that violate Block Policy: {BPNotMet}", file=sys.stderr)       

    return        

#################################################################################
def createCSVrow(CourseInfo, c, config, InstructorId2Name, totalSlot, X, start_time, BPNotMet, InsNotMet, instructor_in_insPref):
    '''
    Usage: generate one row in schedule.txt file

    Input:
    CourseInfo(list)
    c(int): a course id
    config(dict)
    InstructorId2Name(list): e.g., ['McGarrity', 'Evans', 'Wassink', ...]
    totalSlot(int)
    X(list)
    start_time(datetime)
    BPNotMet(set)
    InsNotMet(defaultdict)
    instructor_in_insPref(list): instructor id for those appears in instructor preference file
    '''

    course_name = CourseInfo[c].courseName
    if (CourseInfo[c].instructorId != -1):
        instructor_name = InstructorId2Name[CourseInfo[c].instructorId]
    else:
        instructor_name = '-'  
    days = []
    slots = set()     
    for d in range(5):
        for t in range(totalSlot):
            if (X[c][d][t].varValue >= 1):
                days.append(d)
                slots.add(t)
    slots = list(slots)
    if (len(slots) > 1):
        sys.exit('more than one session in a day')
    else:
        course_start = timeSlotId2ISlot(start_time, slots[0])
    session_length = CourseInfo[c].lengPerSession
    course_end = (time_transfer(course_start, "config", -1) + timedelta(minutes=session_length)).strftime('%H:%M')
    teaching_days = ' '.join(intlist2days(days))

    if (slots[0]> config['BlockSchedulingEndsAtid'] or slots[0] < config['BlockSchedulingStartsAtid']):
        meetBP = '-'
    elif (c in BPNotMet):
        meetBP = 'n'
    else:
        meetBP = 'y'

    meetIP = 'y'
    if (CourseInfo[c].instructorId in InsNotMet and course_name in InsNotMet[CourseInfo[c].instructorId]):
        meetIP = 'n'
    if (CourseInfo[c].instructorId not in instructor_in_insPref):
        meetIP = '-'

    return course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start, course_end

#################################################################################
def generateNonExCSV(output_dir, X, course_instructor, config, NonExemptedC, InsNotMet, BPNotMet, instructor_in_insPref):
    '''
    Usage: generate schedule-nonEx.csv. Only include non-exempt courses.

    Input:
    output_dir(string)
    X(list)
    course_instructor(list)
    config(dict)
    NonExemptedC(list)
    InsNotMe(defaultdict)
    BPNotMet(set)
    instructor_in_insPref(list)

    Format for scedule-NonEx.csv file:
    ###
    Course,Instructor,Length,Meet-block-policy,Meet-Instructor-Preference,Days,Start,End,Notes,
    LING 200,McGarrity,50,-,-,M W F,1430,1520,,
    ###
    '''

    InstructorId2Name = course_instructor[3]
    CourseInfo = course_instructor[5]
    start_time = time_transfer(config['InstructDayStartsAt'], "config", -1)
    totalSlot = config['SlotNumPerday']
    fields = ['Course', 'Instructor', 'Length', 'Meet-block-policy','Meet-Instructor-Preference','Days','Start','End','Notes','']
    rows = []
    for c in NonExemptedC:
        course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start, course_end = createCSVrow(CourseInfo, c, config, InstructorId2Name, totalSlot, X, start_time, BPNotMet, InsNotMet, instructor_in_insPref)
        rows.append(['LING '+course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start.replace(':',''), course_end.replace(':',''), '', ''])

    with open(output_dir+"schedule-nonEx.csv", 'w') as csvfile:  
        # creating a csv writer object  
        csvwriter = csv.writer(csvfile)  
        csvwriter.writerow('') 
        csvwriter.writerow(fields)                
        csvwriter.writerows(rows) 
    
    return

#################################################################################
def generateCSV(output_dir, X, course_instructor, config, NonExemptedC, InsNotMet, BPNotMet, instructor_in_insPref):
    '''
    Usage: generate schedule.csv. Include all the courses. The order is non-exempted courses, exempted courses, TA sessions.

    Input:
    output_dir(string)
    X(list)
    course_instructor(list)
    config(dict)
    NonExemptedC(list)
    InsNotMe(defaultdict)
    BPNotMet(set)
    instructor_in_insPref(list)

    Format for scedule.csv file:
    ###
    Course,Instructor,Length,Meet-block-policy,Meet-Instructor-Preference,Days,Start,Exempted,Notes,
    LING 200,McGarrity,50,-,-,M W F,1430,1520,0,
    ###
    '''

    InstructorId2Name = course_instructor[3]
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    start_time = time_transfer(config['InstructDayStartsAt'], "config", -1)
    totalSlot = config['SlotNumPerday']
    fields = ['Course', 'Instructor', 'Length', 'Meet-block-policy','Meet-Instructor-Preference','Days','Start','Exempted','Notes','']
    rows = []

    #First NonExempted Course
    for c in NonExemptedC:
        if (CourseInfo[c].isTASession == 0):
            course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start, course_end = createCSVrow(CourseInfo, c, config, InstructorId2Name, totalSlot, X, start_time, BPNotMet, InsNotMet, instructor_in_insPref)
            rows.append(['LING '+course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start.replace(':',''), course_end.replace(':',''), '0', ''])
    rows.append(['']*10)

    # Then Exempted Course
    for c in range(TotalCourseNum):
        if (c not in NonExemptedC and CourseInfo[c].isTASession == 0):
            course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start, course_end = createCSVrow(CourseInfo, c, config, InstructorId2Name, totalSlot, X, start_time, BPNotMet, InsNotMet, instructor_in_insPref)
            rows.append(['LING '+course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start.replace(':',''), course_end.replace(':',''), '1', ''])
    rows.append(['']*10)

    # Finally TA sessions
    for c in range(TotalCourseNum):
        if (CourseInfo[c].isTASession == 1):
            course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start, course_end = createCSVrow(CourseInfo, c, config, InstructorId2Name, totalSlot, X, start_time, BPNotMet, InsNotMet, instructor_in_insPref)
            rows.append(['LING '+course_name, instructor_name, session_length, meetBP, meetIP, teaching_days, course_start.replace(':',''), course_end.replace(':',''), CourseInfo[c].exempted, ''])

    with open(output_dir+"schedule.csv", 'w') as csvfile:  
        # creating a csv writer object  
        csvwriter = csv.writer(csvfile)  
        csvwriter.writerow('') 
        csvwriter.writerow(fields)                
        csvwriter.writerows(rows) 

    return

#################################################################################
def printPath(config_file, courseInstructor_file, courseInfo_file, conflict_file, instructorPref_file, output_dir):
    '''
    Usage: print paths for input files and output directory. 

    Input: 
    config_file(string)
    courseInstructor_file(string)
    courseInfo_file(string)
    conflict_file(string)
    instructorPref_file(string)
    output_dir(string)
    '''

    print(f"config file={config_file}", file=sys.stderr)
    print(f"courseInstructor file={courseInstructor_file}", file=sys.stderr)
    print(f"courseInfo file={courseInfo_file}", file=sys.stderr)
    print(f"conflict file={conflict_file}", file=sys.stderr)
    print(f"instructorPref file={instructorPref_file}", file=sys.stderr)
    print(f"output dir={output_dir}", file=sys.stderr)

    return

#################################################################################
def main():
    #Step 1: read config file, print related information.
    current_time = datetime.now()
    print(f"Log file generate at {current_time}", file=sys.stderr)
    print(f"python version: {sys.version}",  file=sys.stderr)
    print(f"pulp version: {pulp.__version__}",  file=sys.stderr)
    config_file = sys.argv[1]
    config = read_config(config_file)
    courseInfo_file = config['CourseInfo']
    courseInstructor_file = config['CourseInstructor']
    conflict_file = config['ConflictCourse']
    instructorPref_file = config['InstructorPref']
    output_dir = config['OutputDir']
    printPath(config_file, courseInstructor_file, courseInfo_file, conflict_file, instructorPref_file, output_dir)

    #Step 2: read all the other files.
    course_instructor = read_courseInstructor(courseInstructor_file, config)
    NonExemptedC, TotalNonExemptedHours = read_courseInfo(courseInfo_file, course_instructor, config)
    conflict_course_pairs = read_conflict(conflict_file, course_instructor)
    print_conflictPairs(conflict_course_pairs, course_instructor)
    IW, SameDayPairs, instructor_in_insPref = read_instructorPref(instructorPref_file, course_instructor, config)

    #Step 3: set up the ILP problem and slove it.
    CW = createCW(course_instructor, config)
    upper_bound = LP(IW, CW, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs)
    X, Y, problem = ILP(IW, CW, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs)

    #Step 4: generate outputs.
    isExist = os.path.exists(output_dir)     # Create a new directory if it does not exist
    if not isExist:
        os.makedirs(output_dir)
    NumCNoPref, InsNotMet, BPNotMet = generate_output(X, output_dir, course_instructor, config, IW, instructor_in_insPref)
    generateHeatMap(Y, output_dir, config, NonExemptedC, TotalNonExemptedHours)
    IW_point, CW_point = computeCWIWPoint(course_instructor, config, X, IW, CW)
    printStandardOutput(config, course_instructor, NonExemptedC, TotalNonExemptedHours, IW_point, CW_point, NumCNoPref, InsNotMet, BPNotMet, problem, upper_bound)
    generateNonExCSV(output_dir, X, course_instructor, config, NonExemptedC, InsNotMet, BPNotMet, instructor_in_insPref)
    generateCSV(output_dir, X, course_instructor, config, NonExemptedC, InsNotMet, BPNotMet, instructor_in_insPref)

#################################################################################
if __name__ == "__main__":
    main()


