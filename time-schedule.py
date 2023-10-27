import pdb
import sys
import math
from datetime import datetime, timedelta
from collections import defaultdict

class Course:
    #def __init__(self, instructorId=None, mustOnDays=None, mustStartSlot=None, mustEndSlot=None, lengPerSession=None, sessionsPerWeek=None, largeClass=None, exempted=None, isTASession=None, mustBeOnSameDay=None, mustOnWhichDay=None, slotNum=None):
    def __init__(self, instructorId, mustOnDays, mustStartSlot, mustEndSlot, lengPerSession, sessionsPerWeek, largeClass, exempted, isTASession, mustBeOnSameDay, mustOnWhichDay, slotNum):
        self.instructorId = instructorId
        self.mustOnDays = mustOnDays
        self.mustStartSlot = mustStartSlot
        self.mustEndSlot = mustEndSlot
        self.lengPerSession = lengPerSession
        self.sessionsPerWeek = sessionsPerWeek
        self.largeClass = largeClass
        self.exempted = exempted
        self.isTASession = isTASession
        self.mustBeOnSameDay = mustBeOnSameDay
        self.mustOnWhichDay = mustOnWhichDay
        self.slotNum = slotNum

def time_transfer(time_string):
    #This function transfer time from string to datetime object
    time = datetime.strptime(time_string, '%H:%M')
    return time 

def timeSlotName2Id(start, timeSlotName):
    id = (timeSlotName - start).total_seconds() / 60 / 30
    return id

def timeSlotId2ISlot(start, timeSlotId):
    name = start + timedelta(minutes=timeSlotId * 30)
    return name.strftime('%H:%M')

def days2listint(days):
    day_mapping = {'M': 1, 'T': 2, 'W': 3, 'R': 4, 'F': 5}
    return [day_mapping[day] for day in days if day in day_mapping]

def read_config(file_name):
    # Initialize a dictionary to store course information
    config = {}
    with open(file_name, "r") as file:
        for line in file:
            #Ignore lines starting with "#"
            if line.startswith("#"):
                continue
            # Split each line into key and value
            key, value = line.strip().split("=")
            key = key.strip()
            value = value.strip().strip('"')
            # Store the values in the dictionary
            config[key] = value

    start_time = time_transfer(config['InstructDayStartsAt'])
    total_day_time = time_transfer(config['InstructDayEndsAt']) - start_time
    SlotNumPerday = math.ceil(total_day_time.total_seconds()/60/20) #A slot is 30 min

    # Define keys that should be treated as floats, integers, or list
    float_keys = ["RulePercentage"]
    int_keys = ["penalty-for-violating-block-policy"]
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
                slotId = math.floor(timeSlotName2Id(start_time, time_transfer(timeName)))
                new_list.append(slotId)
            config[key] = new_list

    config['BlockSchedulingStartsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['BlockSchedulingStartsAt'])))
    config['BlockSchedulingEndsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['BlockSchedulingEndsAt'])))
    config['10PercRuleStartsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['10PercRuleStartsAt'])))
    config['10PercRuleEndsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['10PercRuleEndsAt'])))
    return config

def read_courseInstructor(filename, config):
    CourseName2Id = {}
    CourseId2Name = []
    InstructorName2Id = {}
    InstructorId2Name = []
    CourseInfo = [Course(-1,[], -1, -1, -1, -1, -1, -1, -1, -1, -1, -1) for _ in range(100)]
    Instructor2Courses = defaultdict(list)
    TotalCourseNum = 0
    # Read the CourseInstructor file line by line
    with open(filename, "r") as file:
        for line in file:
            #Ignore lines starting with "#"
            if not line.strip() or line.startswith("#"):
                continue
            # Split each line into its components
            values = line.strip().split()
            # Extract course name and instructor name
            course_name = values[0]
            instructor_name = values[1]
            must_on_days = values[2]
            must_start_time = values[3]
            must_end_time = values[4]
            TotalCourseNum += 1
            # Generate course and instructor IDs
            
            if (instructor_name == '-'):
                instructor_id = -1  # Default to -1 if no instructor specified
            else:
                if (instructor_name not in InstructorName2Id):
                    instructor_id = len(InstructorName2Id)
                    InstructorName2Id[instructor_name] = instructor_id
                    InstructorId2Name.append(instructor_name)
                    assert(len(InstructorName2Id) == len(InstructorId2Name)) # Make sure they are of equal length
                else:
                    instructor_id = InstructorName2Id[instructor_name]

            if (course_name not in CourseName2Id):
                course_id = len(CourseName2Id)
                CourseName2Id[course_name] = course_id
                CourseId2Name.append(course_name)
                assert(len(CourseName2Id) == len(CourseId2Name)) # Make sure they are of equal length
            else:
                course_id = CourseName2Id[course_name]

            Instructor2Courses[instructor_id].append(course_id)
            cur_course = CourseInfo[course_id]
            cur_course.instructorId = instructor_id
            start_time = time_transfer(config['InstructDayStartsAt'])
            if (must_on_days != '-'):
                cur_course.mustOnDays = days2listint(must_on_days) 
            if (must_start_time != '-'):
                cur_course.mustStartSlot = math.floor(timeSlotName2Id(start_time, time_transfer(must_start_time)))
            if (must_end_time != '-'):
                cur_course.mustEndSlot = math.floor(timeSlotName2Id(start_time, time_transfer(must_end_time)))
    course_instructor = [CourseName2Id, CourseId2Name, InstructorName2Id, InstructorId2Name, Instructor2Courses, CourseInfo, TotalCourseNum]

    return course_instructor


def read_courseInfo(file_name, course_instructor):
    TotalNonExemptedHours = 0
    NonExemptedC = []
    CourseName2Id = course_instructor[0]
    CourseInfo = course_instructor[5]
    # Read the CourseInfo file
    with open(file_name, "r") as file:
        for line in file:
            # Ignore lines starting with "#"
            if not line.strip() or line.startswith("#"):
                continue
            # Split the line into values and create a CourseInfo object
            values = line.strip().split()
            course_name = values[0]
            #If the course is not taught this quarter, skip the line.
            if (course_name not in course_instructor[0]):
                continue
            length_per_session = int(values[1])
            num_sessions_per_week = int(values[2])
            large_class = int(values[3])
            ten_percent_rule_exempted = int(values[4])
            is_a_TA_session = int(values[5])
            # all_sessions_must_be_on_same_day = int(values[6])
            # must_on_day = values[7] 

            cur_course = CourseInfo[CourseName2Id[course_name]]
            cur_course.lengPerSession = length_per_session
            cur_course.sessionsPerWeek = num_sessions_per_week
            cur_course.largeClass = large_class
            cur_course.exempted = ten_percent_rule_exempted
            cur_course.isTASession = is_a_TA_session
            # cur_course.mustBeOnSameDay = all_sessions_must_be_on_same_day
            # cur_course.mustOnWhichDay = must_on_day
            cur_course.slotNum = math.ceil(length_per_session/30)

            if (ten_percent_rule_exempted == 0): # if a course is not exempted
                NonExemptedC.append(CourseName2Id[course_name])
                TotalNonExemptedHours += cur_course.slotNum * num_sessions_per_week / 2

    return CourseInfo, NonExemptedC, TotalNonExemptedHours

def read_conflict(file_name, course_instructor):
    CourseName2Id = course_instructor[0]
    Instructor2Courses = course_instructor[4]
    conflict_course_pairs = []
    with open(file_name, "r") as file:
        for line in file:
            # Ignore lines starting with "#"
            if not line.strip() or line.startswith("#"):
                continue
            courses = line.split('#')[0].strip().split()
            course_ids = [CourseName2Id[course] for course in courses if course in CourseName2Id]
            for i in range(len(course_ids)-1):
                for j in range(i + 1, len(course_ids)):
                    conflict_course_pairs.append((min(course_ids[i], course_ids[j]), max(course_ids[i], course_ids[j])))

    for key in Instructor2Courses.keys():
        if (key != -1 and len(Instructor2Courses[key]) > 1):
            course_ids = Instructor2Courses[key]
            for i in range(len(course_ids)-1):
                for j in range(i + 1, len(course_ids)):
                    conflict_course_pairs.append((min(course_ids[i], course_ids[j]), max(course_ids[i], course_ids[j])))
    return conflict_course_pairs

def read_instructorPref(file_name, course_instructor):
    SameDayPairs = set()
    InstructorName2Id = course_instructor[2]
    Instructor2Courses = course_instructor[4]
    CourseInfo = course_instructor[5]
    with open(file_name, "r") as file:
        for line in file:
            # Ignore lines starting with "#"
            if not line.strip() or line.startswith("#"):
                continue
            instructor_name, prefDays, prefStartTime, prefEndTime, sameDay = line.strip().split()
            #If the instructor is not teaching that quarter, skip the line
            '''
            We might also want to consider if the instructor is an TA
            '''
            if (instructor_name not in InstructorName2Id):
                continue
            InstructorID = InstructorName2Id[instructor_name]
            if (InstructorID not in Instructor2Courses):
                continue          
            course_ids = Instructor2Courses[InstructorID]
            if (sameDay == '1' and len(course_ids) > 1):
                for i in range(len(course_ids)-1):
                    for j in range(i + 1, len(course_ids)):
                        if (CourseInfo[course_ids[i]].sessionsPerWeek <= CourseInfo[course_ids[j]].sessionsPerWeek):
                            SameDayPairs.add((course_ids[i], course_ids[j]))
                        else:
                            SameDayPairs.add((course_ids[j], course_ids[i]))                
    pdb.set_trace()
            

def main():
    config_file = sys.argv[1]
    config = read_config(config_file)
    courseInstructor_file = config['CourseInstructor']
    course_instructor = read_courseInstructor(courseInstructor_file, config)
    courseInfo_file = config['CourseInfo']
    CourseInfo, NonExemptedC, TotalNonExemptedHours = read_courseInfo(courseInfo_file, course_instructor)
    conflict_file = config['ConflictCourse']
    conflict_course_pairs = read_conflict(conflict_file, course_instructor)
    instructorPref_file = config['InstructorPref']
    read_instructorPref(instructorPref_file, course_instructor)
if __name__ == "__main__":
    main()


