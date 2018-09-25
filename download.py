from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import requests
import json

TIME_SCHEDULE_FILE = "time_schedule.csv"
CLASSROOM_FILE = "classrooms.json"

def valid_day(string):
    return re.match(r"^(M|T|(Th)|W|F|Sat\.)+$",string)

def to_minutes(time):
    if (len(time) == 3 and re.match(r"^[1-7]",time)) or time.endswith("P"): # ex: 1:30
        return 12 * 60 + int(time[0]) * 60 + int(time[1:3])
    elif len(time) == 3: # ex: 8:30
        return int(time[0]) * 60 + int(time[1:3])
    else: # ex: 11:30
        return int(time[0:2]) * 60 + int(time[2:4])

def append_table(table, df):
    if len(table.parent) > 4:
        time = table.parent.contents[2].split(None)
        day = time[2]
        if valid_day(day):
            hours = time[3].split("-")
            start_minutes = to_minutes(hours[0])
            end_minutes = to_minutes(hours[1])
            building = table.parent.contents[3].string
            room = table.parent.contents[4].split(None, 1)[0]
            entry = pd.Series(np.array([day, start_minutes, end_minutes, time[3], building, room]),
                index=["day", "start", "end", "original_time", "building", "room"])
            return df.append(entry, ignore_index=True)
    return df

# deprecated - the classrooms here are only a subset of available rooms
def load_classroom_list():
    page = requests.get("https://www.washington.edu/classroom/?active=1&capacity=0").content
    soup = BeautifulSoup(page, "html5lib")
    results = soup.find_all("a", href=re.compile(r"[A-Z]+\+[A-Z\d]{3,4}"))
    classrooms = {}
    for each in results:
        building_and_room = each.string.split(None)
        building = building_and_room[0]
        room = building_and_room[1]
        if building not in classrooms:
            classrooms[building] = set()
        classrooms[building].add(room)
    return classrooms

def load_classroom_list2(df):
    classrooms = {}
    for index, row in df.iterrows():
        building = row["building"]
        room = row["room"]
        if building not in classrooms:
            classrooms[building] = set()
        classrooms[building].add(room)
    return classrooms  

def load_departments(df):
    page = requests.get("https://www.washington.edu/students/timeschd/AUT2018/").content
    soup = BeautifulSoup(page, "lxml")
    departments = soup.find_all("a", href=re.compile(r"^[a-z]&*[a-z]+\.html"))
    processed_departments = set()
    for each in departments:
        link = "https://www.washington.edu/students/timeschd/AUT2018/" + each["href"]
        if link not in processed_departments:
            print(f"now loading {link}")
            df = load_department(df, link)
            processed_departments.add(link)
    return df

def load_department(df, dept_link):
    page = requests.get(dept_link).content
    soup = BeautifulSoup(page, "html5lib")

    tables = soup.find_all("a", href=re.compile("timeschd/uwnetid/sln"))

    for table in tables:
        df = append_table(table, df)

    df[["start", "end"]] = df[["start", "end"]].apply(pd.to_numeric)
    # print(find_available(df, "EEB", to_minutes("1200")))
    return df

def export(df, classrooms):
    print(f"Exporting to {TIME_SCHEDULE_FILE}")
    df.to_csv(TIME_SCHEDULE_FILE)
    print(f"{TIME_SCHEDULE_FILE} successfully exported")     
    print(f"Exporting to {CLASSROOM_FILE}")
    with open(CLASSROOM_FILE, "w") as f:
        serializable_classrooms = {}
        for classroom in classrooms:
            serializable_classrooms[classroom] = list(classrooms[classroom])
        f.write(json.dumps(serializable_classrooms))
    print(f"{CLASSROOM_FILE} successfully exported")

def main():
    print("Downloading time schedule data from https://www.washington.edu/students/timeschd/AUT2018/")
    df = pd.DataFrame()
    df = load_departments(df)
    classrooms = load_classroom_list2(df)
    export(df, classrooms)

if __name__ == "__main__":
    main()