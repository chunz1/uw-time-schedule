import re
import pandas as pd
import datetime as dt
import json
import copy

TIME_SCHEDULE_FILE = "time_schedule.csv"
CLASSROOM_FILE = "classrooms.json"
WEEKDAY_LETTERS = ["M", "T", "W", "Th", "F", "S"]

def to_minutes(time):
    if (len(time) == 3 and re.match(r"^[1-7]",time)) or time.endswith("P"): # ex: 1:30
        return 12 * 60 + int(time[0]) * 60 + int(time[1:3])
    elif len(time) == 3: # ex: 8:30
        return int(time[0]) * 60 + int(time[1:3])
    else: # ex: 11:30
        return int(time[0:2]) * 60 + int(time[2:4])

def current_time():
    now = dt.datetime.now()
    minute = str(now.minute)
    hour = str(now.hour % 12)
    return hour + (minute if len(minute) == 2 else "0" + minute)

# time in minutes (e.g. 9:30 am = 9 * 60 + 30 minutes)
def find_available(df, building, day, time, classrooms):
    building_condition = df["building"] == building
    before_start = time >= df["start"]
    after_end = time <= df["end"]
    on_day = df["day"].str.contains(day)
    occupied = df[building_condition & on_day & (before_start & after_end)] 
    return classrooms.difference(set(occupied["room"]))

def find_available_any(df, day, time, classrooms):
    before_start = time >= df["start"]
    after_end = time <= df["end"]
    on_day = df["day"].str.contains(day)
    occupied = df[on_day & (before_start & after_end)][["building", "room"]]
    map_occupied = load_classroom_list2(occupied)
    available = copy.deepcopy(classrooms)
    for building in map_occupied:
        for room in map_occupied[building]:
            available[building].remove(room)
    available = {building:available[building] for building in available if len(available[building]) > 0}
    return available  

def load_classroom_list2(df):
    classrooms = {}
    for index, row in df.iterrows():
        building = row["building"]
        room = row["room"]
        if building not in classrooms:
            classrooms[building] = set()
        classrooms[building].add(room)
    return classrooms  

def from_file():
    print(f"Now loading classroom data from {CLASSROOM_FILE}")
    with open(CLASSROOM_FILE, "r") as classroom_json:
        classrooms = json.loads(classroom_json.read())
        for classroom in classrooms:
            classrooms[classroom] = set(classrooms[classroom])
    print(f"Now loading time schedule data from {TIME_SCHEDULE_FILE}")
    df = pd.read_csv(TIME_SCHEDULE_FILE)
    print("Importing data finished")    
    return df, classrooms

def valid_time(time):
    return re.match(r"^([1-9]|1[0-2])[0-5][0-9]$", time)

def prompt_time():
    while True:
        day = input(f"Specify the day to check available {WEEKDAY_LETTERS} ")
        if day in WEEKDAY_LETTERS:
            break
        print("Input not one of the options. Please specify one of the given days.")
    while True:
        time = input("Specify the time to check available for in the format of HMM."
            + "\n Examples: 130, 1230, 1155"
            + "\n Note: specifying hours 8 to 11 will be taken to be AM ")
        if valid_time(time):
            break
    return day, time

def search_action(df, classrooms):
    while True:
        building = input("Specify a building's 3-letter abbreviation to search in: "
            + "\n ('list') to list all the classroom abbreviations"
            + "\n (enter) to search all buildings ")
        if building == 'list':
            print_buildings(df)
        elif building in classrooms or not building:
            break         
        else:
            print("Usage: Invalid building name specified.")
    use_current_time = input("Use the current time to check for availability? ('y' for yes, anything else for no) ")
    if (use_current_time == 'y'):
        day = WEEKDAY_LETTERS[dt.datetime.now().weekday()]
        time = current_time()
    else:
        day, time = prompt_time()
    if not building:
        print(find_available_any(df, day, to_minutes(time), classrooms))
    else:
        print(find_available(df, building, day, to_minutes(time), classrooms[building]))

def print_buildings(df):
    buildings = list(set(df["building"]))
    buildings.sort()
    print(buildings)

def schedule_action(df, classrooms):
    while True:
        building = input("Specify a building's 3-letter abbreviation to use: "
            + "\n ('list') to list all the classroom abbreviations ")
        if building in classrooms:
            break
        elif building == 'list':
            print_buildings(df)
        else:
            print("Usage: Invalid building name specified.")
    # sort by room or time 
    return df[df["building"] == building].sort_values(["room", "day", "start"])

def main():
    df, classrooms = from_file()   
    while True:
        action = input("Input an action: "
            + "\n ('schedule') to find the classroom schedule for a building" 
            + "\n ('search') to search for available classrooms for a given time" 
            + "\n ('exit') to exit: ")
        if action == 'schedule': #schedule
            print(schedule_action(df, classrooms).to_string())
        elif action == 'search': #search
            search_action(df, classrooms)
        elif action != 'exit':
            print("Usage")
        else:
            break
    
if __name__ == "__main__":
    main()   
