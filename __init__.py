import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from aqt.main import AnkiQt
from anki.hooks import wrap, addHook
from anki.utils import intTime
try:
    from anki.consts import QUEUE_TYPE_NEW, QUEUE_TYPE_LRN, QUEUE_TYPE_DAY_LEARN_RELEARN, QUEUE_TYPE_REV
except:
    QUEUE_TYPE_NEW = 0
    QUEUE_TYPE_LRN = 1
    QUEUE_TYPE_REV = 2
    QUEUE_TYPE_DAY_LEARN_RELEARN = 3

from aqt import mw
from aqt.utils import tooltip, showText
from aqt.deckbrowser import DeckBrowser

ADDON_NAME = __name__
DIR_PATH = Path(__file__).parents[0] / "user_files"
DATA_PATH = DIR_PATH / "data.json"
BACKUP_PATH = DIR_PATH / "backups"

NEW_MOD = 2 * 1.05
REV_MOD = 1.05

DONE_THRESHHOLD = 0.99


config = mw.addonManager.getConfig(__name__)

def create_missing_dir():
    if not DIR_PATH.is_dir():
        DIR_PATH.mkdir()

    if not DATA_PATH.is_file():
        DATA_PATH.write_text("{}")

    if not BACKUP_PATH.is_dir():
        BACKUP_PATH.mkdir()


def delete_today_backup():
    tday_str = datetime.now().strftime("%Y_%m_%d_")
    for fname in BACKUP_PATH.iterdir():
        fn = fname.name
        if fn.startswith(tday_str) and fname.is_file():
            fpth = BACKUP_PATH / fn
            fpth.unlink()


def create_backup(data):
    # one backup for each day
    delete_today_backup()
    timestr = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    fname = timestr + ".json"
    path = BACKUP_PATH / fname
    path.write_text(data)
        


def get_data():
    """ format: dictionary in string. Parsed in web/main.js
    "{
        #year
        2020: {
            #month 0-12
            0: {
                #date 1 - 31
                1: 0.9 #percentage done
                2: 1
                ...
            }
        }
    }"
    """
    create_missing_dir()
    datastr = DATA_PATH.read_text()
    return datastr


def write_data(datastr):
    create_missing_dir()
    create_backup(datastr)
    DATA_PATH.write_text(datastr)

def get_date(delta = 0):
    now = datetime.now() - timedelta(delta)
    year = str(now.year)
    month = str(now.month - 1)
    date = str(now.day)
    return (year, month, date)

def get_stats_from_data(data):
    done_days = 0
    day_cnt = 0
    tot_perc = 0
    for year in data:
        yearlydata = data[year]
        for month in yearlydata:
            monthlydata = yearlydata[month]
            for date in monthlydata:
                day_cnt += 1
                tot_perc += monthlydata[date]
                if monthlydata[date] > DONE_THRESHHOLD:
                    done_days += 1

    if day_cnt  == 0:
        #avoid division by 0
        day_cnt = 1
    done_perc = round(done_days / day_cnt * 100)

    avg_perc = round(tot_perc / day_cnt * 100)
    
    streak = True
    streak_d = 0
    while(streak):
        year, month, date = get_date(streak_d)
        try:
            if(data[year][month][date] > DONE_THRESHHOLD):
                streak_d += 1
            else:
                streak = False
        except:
            streak = False
    
    return (avg_perc, done_perc, streak_d)
    

def heatmap_html():
    datastr = get_data()
    data = json.loads(datastr)
    stats = get_stats_from_data(data)
    return """
<link rel="stylesheet" href="/_addons/{0}/web/calendar-heatmap.css"></script>
<script src="/_addons/{0}/web/d3.min.js"></script>
<script src="/_addons/{0}/web/moment.js"></script>
<script src="/_addons/{0}/web/calendar-heatmap.js"></script>
<script>window.ADDON_percjsonstr = `{1}`; window.ADDON_percyear = "{2}"; window.ADDON_perccolors={3};</script>
<div id="percHeatmap"></div>
<div id="percHeatmapFoot">
    <span class="percFoot">Daily Average: {4} %</span>
    <span class="percFoot">Completed Days: {5}%</span>
    <span class="percFoot">Current Streak: {6} days</span>
</div>
<script src="/_addons/{0}/web/main.js"></script>
    """.format(ADDON_NAME, datastr, config["year"], config["colors"], stats[0], stats[1], stats[2])


def get_today_perc_stat():
    # from aqt.deckbrowser.DeckBrowser._renderStats
    done_cards = mw.col.db.scalar(
        """
select count() from revlog
where id > ?""",
        (mw.col.sched.dayCutoff - 86400) * 1000,
    )
    due_cards = 0
    nameMap = mw.col.decks.nameMap()
    dueTree = mw.col.sched.deckDueTree()
    for node in dueTree:
        name, did, due, lrn, new, children = node
        if "::" in mw.col.decks.get(did):
            continue
        due_cards += (due + lrn) * REV_MOD + new * NEW_MOD

    return (done_cards, due_cards)


def save_perc(*args, **kwargs):
    donecnt, duecnt = get_today_perc_stat()
    if donecnt + duecnt == 0:
        perc = 1
    else:
        perc = donecnt / (donecnt+duecnt)
        perc = round(perc, 2)

    percdict = json.loads(get_data())
    year, month, date = get_date()
    if year not in percdict:
        percdict[year] = {}
    yeardict = percdict[year]
    
    if month not in yeardict:
        yeardict[month] = {}
    monthdict = yeardict[month]

    monthdict[date] = perc

    jsonstr = json.dumps(percdict)
    write_data(jsonstr)
    
    _old = kwargs.pop("_old", lambda: None)
    return _old(*args, **kwargs)


def on_state_change(new, *args, **kwargs):
    if new == "deckBrowser":
        save_perc()


def custom_render_stats(*args, **kwargs):
    _old = kwargs.pop("_old", lambda: None)
    ret = _old(*args, **kwargs)
    return ret + heatmap_html()


addHook("beforeStateChange", on_state_change)
AnkiQt.closeEvent = wrap(AnkiQt.closeEvent, save_perc, "around")
DeckBrowser._renderStats = wrap(
    DeckBrowser._renderStats, custom_render_stats, "around")
mw.addonManager.setWebExports(__name__, r"web(\/|\\).*\.(css|js)")
