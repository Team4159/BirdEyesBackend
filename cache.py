import json
import os
import sys

from requests import Session
from dotenv import load_dotenv
load_dotenv()

request_session = Session()
request_session.headers['X-TBA-Auth-Key'] = os.getenv('TBA_KEY')

season = sys.argv[1]
event = sys.argv[2]
resp = request_session.get(f"https://www.thebluealliance.com/api/v3/events/{season}/keys")
if not resp.ok: raise Exception(f"Error {resp.status_code} @ Season: {resp.content.decode()}")
if not season+event in resp.json(): raise Exception(f"Error @ Event: {season}{event} does not exist.")

resp = request_session.get(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/matches/simple")
if not resp.ok: raise Exception("Error @ Matches: "+resp.status_code)
respjson = resp.json()
matches = {e['key'].split("_")[-1]: e['key'] for e in respjson}

teams = {}
for match in respjson:
    o = {}
    for alliance, adata in match['alliances'].items():
        for teamCode in adata['team_keys']:
            o[teamCode[3:]] = alliance
    teams[match['key'].split("_")[-1]] = o

open(os.path.join('instance', 'cache.json'), "w+").write(json.dumps({
    "season": season,
    "event": event,
    "matches": matches,
    "teams": teams
}, indent=4))