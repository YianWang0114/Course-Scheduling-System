import pdb
import sys
import math
from datetime import datetime, timedelta
from collections import defaultdict
import pulp

class Course:
    #def __init__(self, instructorId=None, mustOnDays=None, mustStartSlot=None, mustEndSlot=None, lengPerSession=None, sessionsPerWeek=None, largeClass=None, exempted=None, isTASession=None, mustBeOnSameDay=None, mustOnWhichDay=None, slotNum=None):
    def __init__(self, courseId, courseName, instructorId, mustOnDays, mustStartSlot, mustEndSlot, lengPerSession, sessionsPerWeek, largeClass, exempted, isTASession, slotNum):
        self.courseId = courseId
        self.courseName = courseName
        self.instructorId = instructorId
        self.mustOnDays = mustOnDays
        self.mustStartSlot = mustStartSlot
        self.mustEndSlot = mustEndSlot
        self.lengPerSession = lengPerSession
        self.sessionsPerWeek = sessionsPerWeek
        self.largeClass = largeClass
        self.exempted = exempted 
        self.isTASession = isTASession
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
    day_mapping = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4}
    return [day_mapping[day] for day in days if day in day_mapping]

def intlist2days(intlist):
    day_mapping = {0: 'M', 1: 'T', 2: 'W', 3: 'R', 4: 'F'}
    return [day_mapping[day] for day in intlist if day in day_mapping]

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
    SlotNumPerday = math.ceil(total_day_time.total_seconds()/60/30) #A slot is 30 min

    # Define keys that should be treated as floats, integers, or list
    float_keys = ["RulePercentage"]
    int_keys = ["penalty-for-violating-block-policy", "UWPolicyWeight", "InstructorPrefWeight"]
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
    config['BlockSchedulingEndsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['BlockSchedulingEndsAt']) - timedelta(hours=0, minutes=1)))
    config['10PercRuleStartsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['10PercRuleStartsAt'])))
    config['10PercRuleEndsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['10PercRuleEndsAt'])))
    config['SlotNumPerday'] = SlotNumPerday
    return config

def read_courseInstructor(filename, config):
    CourseName2Id = {}
    CourseId2Name = []
    InstructorName2Id = {}
    InstructorId2Name = []
    CourseInfo = [Course(-1, -1, -1, [], -1, -1, -1, -1, -1, -1, -1, -1) for _ in range(100)]
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
            course_name_before_slash = course_name.split('/')[0]
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

            if (course_name_before_slash not in CourseName2Id):
                course_id = len(CourseName2Id)
                CourseName2Id[course_name_before_slash] = course_id
                CourseId2Name.append(course_name_before_slash)
                assert(len(CourseName2Id) == len(CourseId2Name)) # Make sure they are of equal length
            else:
                course_id = CourseName2Id[course_name_before_slash]

            Instructor2Courses[instructor_id].append(course_id)
            cur_course = CourseInfo[course_id]
            cur_course.courseId = course_id
            cur_course.courseName = course_name
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
            course_name_before_slash = course_name.split('/')[0]
            #If the course is not taught this quarter, skip the line.
            if (course_name_before_slash not in course_instructor[0]):
                continue
            length_per_session = int(values[1])
            num_sessions_per_week = int(values[2])
            large_class = int(values[3])
            ten_percent_rule_exempted = int(values[4])
            is_a_TA_session = int(values[5])

            cur_course = CourseInfo[CourseName2Id[course_name_before_slash]]
            cur_course.lengPerSession = length_per_session
            cur_course.sessionsPerWeek = num_sessions_per_week
            cur_course.largeClass = large_class
            cur_course.exempted = ten_percent_rule_exempted
            cur_course.isTASession = is_a_TA_session
            cur_course.slotNum = math.ceil(length_per_session/30)

            if (ten_percent_rule_exempted == 0): # if a course is not exempted
                NonExemptedC.append(CourseName2Id[course_name_before_slash])
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
            course_ids = [CourseName2Id[course.split('/')[0]] for course in courses if course.split('/')[0] in CourseName2Id]
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

def read_instructorPref(file_name, course_instructor, config):
    SameDayPairs = set()
    InstructorName2Id = course_instructor[2]
    Instructor2Courses = course_instructor[4]
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    start_time = time_transfer(config['InstructDayStartsAt'])
    IW = [[[0 for _ in range(config['SlotNumPerday'])] for _ in range(5)] for _ in range(TotalCourseNum)]
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
            '''
            Should we just skip it or should we set all the slots pref slots?
            '''
            # if (prefDays == '-' and prefStartTime == '-' and prefEndTime == '-'):
            #     continue

            #Set default value
            if (prefStartTime == '-'):
                prefStartSlot = 0
            else:
                prefStartSlot = math.floor(timeSlotName2Id(start_time, time_transfer(prefStartTime)))
            if (prefEndTime == '-'):
                prefEndSlot = config['SlotNumPerday'] - 1
            else:
                prefEndSlot = math.floor(timeSlotName2Id(start_time, time_transfer(prefEndTime)-timedelta(hours=0, minutes=1)))
            if (prefDays == '-'):
                prefDayList = [0,1,2,3,4]
            else:
                prefDayList = days2listint(prefDays)

            for c in course_ids:
                for d in prefDayList:
                    for t in range(prefStartSlot, prefEndSlot - math.ceil(CourseInfo[c].lengPerSession/30) + 1):
                        IW[c][d][t] = 1 / CourseInfo[c].sessionsPerWeek
                        if (1 / CourseInfo[c].sessionsPerWeek < 0):
                            print('CourseInfo fail to find')
                            pdb.set_trace()
    
    return IW, SameDayPairs

def createCW(course_instructor, config):
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    totalSlot = config['SlotNumPerday']
    BlockingSlot = list(range(config['BlockSchedulingStartsAtid'], config['BlockSchedulingEndsAtid'] + 1))
    CW = [[[0 for _ in range(config['SlotNumPerday'])] for _ in range(5)] for _ in range(TotalCourseNum)]
    
    for c in CourseInfo:
        if (c.lengPerSession == 50):
            for d in range(5):
                for t in BlockingSlot:
                    CW[c.courseId][d][t] = config['penalty-for-violating-block-policy']
                for t in config['50-min-class-start-time']:
                    CW[c.courseId][d][t] = 1
        elif (c.lengPerSession == 80):
            for d in range(5):
                for t in BlockingSlot:
                    CW[c.courseId][d][t] = config['penalty-for-violating-block-policy']
                for t in config['80-min-class-start-time']:
                    CW[c.courseId][d][t] = 1
        elif (c.lengPerSession == 110):
            for d in range(5):
                for t in BlockingSlot:
                    CW[c.courseId][d][t] = config['penalty-for-violating-block-policy']
                for t in config['110-min-class-start-time']:
                    CW[c.courseId][d][t] = 1 
        elif (c.lengPerSession == 170):
            for d in range(5):
                for t in BlockingSlot:
                    CW[c.courseId][d][t] = config['penalty-for-violating-block-policy']
                for t in config['170-min-class-start-time']:
                    CW[c.courseId][d][t] = 1  
                    
    return CW

def createDecisionvariable(TotalCourseNum, totalSlot, var):
    var = {}
    for c in range(TotalCourseNum):
        var[c] = {}
        for d in range(5):
            var[c][d] = {}
            for t in range(totalSlot):
                var[c][d][t] = pulp.LpVariable(f"{var}_{c}_{d}_{t}", 0, 1, pulp.LpBinary)
    return var

def ILP(IW, CW, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs):
    CourseId2Name = course_instructor[1]
    TotalCourseNum = course_instructor[6]
    CourseInfo = course_instructor[5]
    totalSlot = config['SlotNumPerday']
    l1 = config['UWPolicyWeight']
    l2 = config['InstructorPrefWeight']
    # Create the ILP problem
    problem = pulp.LpProblem("ILP_Maximization_Problem", pulp.LpMaximize)

    # Initialize variable X and Y (three dimensional array)
    X = [[[pulp.LpVariable(f"X_{c}_{d}_{t}", 0, 1, cat=pulp.LpBinary) for t in range(totalSlot)] for d in range(5)] for c in range(TotalCourseNum)]
    Y = [[[pulp.LpVariable(f"Y_{c}_{d}_{t}", 0, 1, cat=pulp.LpBinary) for t in range(totalSlot)] for d in range(5)] for c in range(TotalCourseNum)]

    # objective function
    problem +=  pulp.lpSum((l1 * CW[c][d][t] + l2 * IW[c][d][t]) * X[c][d][t] for c in range(TotalCourseNum) for d in range(5) for t in range(totalSlot))
    
    # Constraint 1: Matrix Y must be consistent with Matrix X
    for c in range(TotalCourseNum):
        slotNum = CourseInfo[c].slotNum
        for d in range(5):
            problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) * slotNum == pulp.lpSum(Y[c][d][t] for t in range(totalSlot))
            for t in range(totalSlot):
                for j in range(t, min(t + slotNum, totalSlot)):
                    problem += Y[c][d][j] >= X[c][d][t]

    # Constraint 2: Each course must meet the correct number of times per week
    for c in range(TotalCourseNum):
        sessionsPerWeek = CourseInfo[c].sessionsPerWeek
        #Total sessions taught in a week equal to sessionsPerWeek
        if (sessionsPerWeek != 3 and sessionsPerWeek != 1 and sessionsPerWeek != 2):
            print('incorrect session number')
            pdb.set_trace()
        problem += pulp.lpSum(X[c][d][t] for d in range(5) for t in range(totalSlot)) == sessionsPerWeek

        #Each course meet at most once per day
        for d in range(5):
            problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) <= 1

    #Constraint 3: Non-TA courses that meet twice per week
    for c in range(TotalCourseNum):
        if CourseInfo[c].sessionsPerWeek == 2:
            for t in range(totalSlot):
                problem += X[c][1][t] == X[c][3][t]   # T and R have the same schedule
                problem += X[c][0][t] == X[c][2][t]   # M and W have the same schedule
            # not meet on Friday
            problem += pulp.lpSum(X[c][4][t] for t in range(totalSlot)) == 0
            '''
            We don't have large courses that have two sessions per week
            '''
            if CourseInfo[c].largeClass == 1:
                # must meet on T and R
                problem += pulp.lpSum(X[c][1][t] for t in range(totalSlot)) >= 1
                problem += pulp.lpSum(X[c][3][t] for t in range(totalSlot)) >= 1
    
    # Constraint 4: Non-TA courses that meet three times per week
    for c in range(TotalCourseNum):
        if CourseInfo[c].sessionsPerWeek == 3:
            # must meet on M, W, F
            problem += pulp.lpSum(X[c][0][t] for t in range(totalSlot)) >= 1
            problem += pulp.lpSum(X[c][2][t] for t in range(totalSlot)) >= 1
            problem += pulp.lpSum(X[c][4][t] for t in range(totalSlot)) >= 1
            # M, W, and F have the same schedule
            for t in range(totalSlot):
                problem += X[c][0][t] == X[c][2][t]   
                problem += X[c][0][t] == X[c][4][t]   

    # Constraint 5: Conflicting courses should not overlap in time
    for (c1, c2) in conflict_course_pairs:
        for d in range(5):
            for t in range(totalSlot):
                problem += Y[c1][d][t] + Y[c2][d][t] <= 1

    # Constraint 6: Meet the 10%-rule requirement
    target = config['RulePercentage'] * TotalNonExemptedHours
    for t in range(config['10PercRuleStartsAtid'], config['10PercRuleEndsAtid'] + 1, 2):
        t1 = pulp.lpSum(Y[c][d][t] for c in NonExemptedC for d in range(5))
        t2 = pulp.lpSum(Y[c][d][t + 1] for c in NonExemptedC for d in range(5))
        problem += (t1 + t2) / 2 <= target

    # Constraint 7: The SameDay preferences are treated as hard constraints
    for (c1, c2) in SameDayPairs:
        # CourseInfo[c1].SessionsPerWeek <=  CourseInfo[c2].sessionsPerWeek 
        assert (CourseInfo[c1].sessionsPerWeek <= CourseInfo[c2].sessionsPerWeek)
        for d in range(5):
            problem += pulp.lpSum(X[c1][d][t] for t in range(totalSlot)) <= pulp.lpSum(X[c2][d][t] for t in range(totalSlot))
    
    # Constraint 8: X's time later than InstructDayEndsAt - course length should be set to 0
    for c in range(TotalCourseNum):
        for d in range(5):
            for t in range(totalSlot - CourseInfo[c].slotNum + 1, config['SlotNumPerday']):
                problem += X[c][d][t] <= 0
    
    # Constraint 9: mustOnDays, mustStartSlot and mustEndSlot
    for c in range(TotalCourseNum):
        if (CourseInfo[c].mustOnDays != []):
            # Course must be on specific days
            d1 = CourseInfo[c].mustOnDays
            for d in [0,1,2,3,4]:
                if (d in d1):
                    problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) >= 1
                else:
                    problem += pulp.lpSum(X[c][d][t] for t in range(totalSlot)) == 0
        '''
        Make it must start at or after mustStartSlot
        '''
        if (CourseInfo[c].mustStartSlot != -1):
            for d in range(5):
                for t in range(0, CourseInfo[c].mustStartSlot):
                    #if (t != CourseInfo[c].mustStartSlot):
                    problem += X[c][d][t] == 0
        if (CourseInfo[c].mustEndSlot != -1):
            for d in range(5):
                for t in range(CourseInfo[c].mustEndSlot - CourseInfo[c].slotNum + 2, totalSlot):
                    problem += X[c][d][t] == 0

    # Constraint 10: If must-follow-block-policy is 1, we set corresponding X value
    BlockingSlot = list(range(config['BlockSchedulingStartsAtid'], config['BlockSchedulingEndsAtid'] + 1))
    if (config['must-follow-block-policy'] == '1'):
        for c in range(TotalCourseNum):
            if (CourseInfo[c].lengPerSession == 50):
                for d in range(5):
                    for t in BlockingSlot:
                        if (t not in config['50-min-class-start-time']):
                            problem += X[c][d][t] <= 0
            elif (CourseInfo[c].lengPerSession == 80):
                for d in range(5):
                    for t in BlockingSlot:
                        if (t not in config['80-min-class-start-time']):
                            problem += X[c][d][t] <= 0
            elif (CourseInfo[c].lengPerSession == 110):
                for d in range(5):
                    for t in BlockingSlot:
                        if (t not in config['110-min-class-start-time']):
                            problem += X[c][d][t] <= 0
            elif (CourseInfo[c].lengPerSession == 170):
                for d in range(5):
                    for t in BlockingSlot:
                        if (t not in config['170-min-class-start-time']):
                            problem += X[c][d][t] <= 0
    pulp.LpSolverDefault.timeLimit = 15
    problem.solve()

    print(pulp.LpStatus[problem.status])
    print(pulp.value(problem.objective))
    return X, Y

def generate_output(X, output_dir, course_instructor, config, IW):
    CourseId2Name = course_instructor[1]
    InstructorId2Name = course_instructor[3]
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    start_time = time_transfer(config['InstructDayStartsAt'])
    totalSlot = config['SlotNumPerday']
    BlockingSlot = list(range(config['BlockSchedulingStartsAtid'], config['BlockSchedulingEndsAtid'] + 1))
    with open("raw_output.txt", "w") as file:
        for c in range(TotalCourseNum):
            for d in range(5):
                for t in range(totalSlot):
                    x_value = X[c][d][t].varValue
                    file.write(f"X_{c}_{d}_{t} = {x_value}\n")
    with open(output_dir+"output.txt", "w") as file:
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
                        days.append(d)
                        slots.add(t)
            if (CourseInfo[c].isTASession == 1):
                meetIP = '-'
            slots = list(slots)
            if (len(slots) > 1):
                print('more than one session in a day')
                pdb.set_trace()
            else:
                course_start = timeSlotId2ISlot(start_time, slots[0])
            teaching_days = ''.join(intlist2days(days))
            session_length = CourseInfo[c].lengPerSession
            course_end = (time_transfer(course_start) + timedelta(minutes=session_length)).strftime('%H:%M')
            meetBP = 'y'
            #irrelevent to Blocking Rule
            if (slots[0] > config['BlockSchedulingEndsAtid'] or slots[0] < config['BlockSchedulingStartsAtid']):
                meetBP = '-'
            else:
                if (session_length == 50):
                    for s in slots:
                        if (s in BlockingSlot and s not in config['50-min-class-start-time']):
                            meetBP = 'n'
                elif (session_length == 80):
                    for s in slots:
                        if (s in BlockingSlot and s not in config['80-min-class-start-time']):
                            meetBP = 'n'
                elif (session_length == 110):
                    for s in slots:
                        if (s in BlockingSlot and s not in config['110-min-class-start-time']):
                            meetBP = 'n'
                elif (session_length == 170):
                    for s in slots:
                        if (s in BlockingSlot and s not in config['170-min-class-start-time']):
                            meetBP = 'n'
            formatted_output = "{:<8}\t{:<20}\t{:<5}\t{:<8}\t{:<8}\t{:<5}\t{:<3}\t{:<3}\n".format(course_name, instructor_name, teaching_days, course_start, course_end, session_length, meetBP, meetIP)
            file.write(formatted_output)
    return

def generateHeatMap(Y, output_dir, course_instructor, config, NonExemptedC, TotalNonExemptedHours):
    CourseInfo = course_instructor[5]
    TotalCourseNum = course_instructor[6]
    start_slot = config['10PercRuleStartsAtid']
    start_time = time_transfer(config['10PercRuleStartsAt'])
    end_slot = config['10PercRuleEndsAtid']
    totalSlot = end_slot - start_slot + 1
    target_value = math.floor(TotalNonExemptedHours * config['RulePercentage'])
    with open(output_dir+"heatMap.txt", "w") as file:
        file.write(f"\t\tM\tT\tW\tR\tF\tHourly total\tHourly Target\n")
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
            #file.write(f"{time}\t{weekly_sum[0]}\t{weekly_sum[1]}\t{weekly_sum[2]}\t{weekly_sum[3]}\t{weekly_sum[4]}\t{sum(weekly_sum)}\t{target_value}\n")
    return

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
    IW, SameDayPairs = read_instructorPref(instructorPref_file, course_instructor, config)
    CW = createCW(course_instructor, config)
    X, Y = ILP(IW, CW, course_instructor, config, conflict_course_pairs, NonExemptedC, TotalNonExemptedHours, SameDayPairs)
    output_dir = config['outputDir']
    generate_output(X, output_dir, course_instructor, config, IW)
    generateHeatMap(Y, output_dir, course_instructor, config, NonExemptedC, TotalNonExemptedHours)

if __name__ == "__main__":
    main()


