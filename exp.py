from pathlib import Path
import json

DIR_PATH = Path(__file__).parents[0] / "user_files"
DATA_PATH = DIR_PATH / "data.json"

datastr = DATA_PATH.read_text()

year = 2020
month = 1
date = 20
perc = 0.0

percdict = json.loads(datastr)
    
if year not in percdict:
    percdict[year] = {}
yeardict = percdict[year]

if month not in yeardict:
    yeardict[month] = {}
monthdict = yeardict[month]

monthdict[date] = perc

jsonstr = json.dumps(percdict)

print(jsonstr)