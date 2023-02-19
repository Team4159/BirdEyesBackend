import os

def format_event(season: int, event_id: str):
    return f"frc{season}{event_id}"

PIT_SCHEME = {
    '2023': {
        "Which drivetrain do you use?": "drivetrain",
        "What is your experience with FIRST so far? How did this build season go for you?": "experience",
        "How has your robot been doing in this competition? What are some the strengths of your robot? What are some of its shortcomings?": "strengthsWeaknesses",
        "Describe your auto": "auto",
        "Where can you score?": "scoreZone",
        "Can you dock in teleop?": "teleopDock",
        "Where can you pick up pieces?": "substationZone",
        "Which pieces can you pick up?": "scoreType",
        "How many years have your drivers been driving the robot? How would you rate your drive team's experience/performance in this competition?": "driver",
    },
    '2022': {"What role do you think the FIRST community has in the world, how has that role changed since its establishment?": "test"}
}

MATCH_SCHEME = {
    '2023': {
        "auto": {
            "coneAttempted": "counter",
            "coneLow": "counter",
            "coneMid": "counter",
            "coneHig": "counter",
            "mobility":"toggle"
        },
        "teleop": {
            "coneAttempted": "counter",
            "coneLow": "counter",
            "coneMid": "counter",
            "coneHig": "counter"
        },
        "endgame": {
            "docked": "toggle",
            "engaged":"toggle"
        },
        "driver": {
            "rating": "slider",
            "fouls": "counter"
        }
    },
    '2022': {
        "test": {
            "counter": "counter",
            "slider": "slider",
            "toggle": "toggle"
        }
    }
}

MATCH_SCHEME_DATATYPES = {
    "counter": "INTEGER", "toggle": "BOOLEAN", "slider": "INTEGER", "text": "TEXT"
}

DB_SCHEME = {}
for season in MATCH_SCHEME:
    s = ""
    for k, v in MATCH_SCHEME[season].items():
        for k1, v1 in v.items():
            s += f"    {k+k1[0].upper()+k1[1:]} {MATCH_SCHEME_DATATYPES[v1]},\n"
    if (season not in DB_SCHEME):
        DB_SCHEME[season] = ""
    DB_SCHEME[season] += f"""
CREATE TABLE IF NOT EXISTS {{event}}_match (
    match TEXT NOT NULL,
    teamNumber INTEGER NOT NULL,
    name TEXT NOT NULL,

{s}
    PRIMARY KEY (match, teamNumber)
);"""
for season in PIT_SCHEME:
    if (season not in DB_SCHEME):
        DB_SCHEME[season] = ""
    DB_SCHEME[season] += """
CREATE TABLE IF NOT EXISTS {event}_pit (
    teamNumber INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,\n"""+("\n".join([f"    {v} TEXT," for v in PIT_SCHEME[season].values()]))+"\n);"