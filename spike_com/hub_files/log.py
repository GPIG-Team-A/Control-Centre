"""
    A module to do logging on the Spike
"""
import time

LOG_FILE_NAME = "log.txt"

def log(text):
    year, month, mday, hour, minute, second, weekday, yearday = time.localtime()
    datetime = str(mday) + "/" + str(month) + "/" + str(year) + " " + str(hour) + ":" + str(minute) + ":" + str(second)
    text = "[" + datetime + "] " + str(text) + "\n"
    with open(LOG_FILE_NAME, "a") as f:
        f.write(text)
    print(text)

def reset():
    f = open(LOG_FILE_NAME, "w")
    f.write("")
    f.close()