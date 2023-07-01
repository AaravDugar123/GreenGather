from datetime import datetime
def convertTime(time):
    d = datetime.strptime(time, "%H:%M")
    return d.strftime("%I:%M" "%p")