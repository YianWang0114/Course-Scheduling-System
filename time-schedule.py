import pdb
import sys
import math
from datetime import datetime, timedelta

def time_transfer(time_string):
    #This function transfer time from string to datetime object
    time = datetime.strptime(time_string, '%H:%M')
    return time 

def timeSlotName2Id(start, timeSlotName):
    id = (timeSlotName - start).total_seconds() / 60/ 30
    return id

def timeSlotId2ISlot(start, timeSlotId):
    name = start + timedelta(minutes=timeSlotId * 30)
    return name.strftime('%H:%M')

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
            for timeName in value.split(' '):
                slotId = math.floor(timeSlotName2Id(start_time, time_transfer(timeName)))
                new_list.append(slotId)
            config[key] = new_list

    config['BlockSchedulingStartsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['BlockSchedulingStartsAt'])))
    config['BlockSchedulingEndsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['BlockSchedulingEndsAt'])))
    config['10PercRuleStartsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['10PercRuleStartsAt'])))
    config['10PercRuleEndsAtid'] = math.floor(timeSlotName2Id(start_time, time_transfer(config['10PercRuleEndsAt'])))
    return config

def read_courseInfo(file_name):
    # Initialize a dictionary to store course information
    course_info = {}
    # Read the CourseInfo file
    with open(file_name, "r") as file:
        for line in file:
            # Ignore lines starting with "#"
            if line.startswith("#"):
                continue
            # Split the line into values and create a CourseInfo object
            values = line.strip().split()
            course_name = values[0]
            length_per_session = int(values[1])
            num_sessions_per_week = int(values[2])
            large_class = int(values[3])
            ten_percent_rule_exempted = int(values[4])
            is_a_TA_session = int(values[5])
            all_sessions_must_be_on_same_day = int(values[6])
            must_on_day = values[7] 
            course_info[course_name] = [
            length_per_session,
            num_sessions_per_week,
            large_class,
            ten_percent_rule_exempted,
            is_a_TA_session,
            all_sessions_must_be_on_same_day,
            must_on_day]

    return course_info





def main():
    config_file = sys.argv[1]
    config = read_config(config_file)
    courseInfo_file = config['CourseInfo']
    course_info = read_courseInfo(courseInfo_file)
    pdb.set_trace()

if __name__ == "__main__":
    main()


