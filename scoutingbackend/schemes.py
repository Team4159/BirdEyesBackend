def format_event(season: int, event_id: str):
    return f"frc{season}{event_id}"

PIT_SCHEME = {
    '2023': {
        "What is your experience with FIRST so far? How did this build season go for you?" : "experienceBuildseason",
        "How has your robot been doing in this competition? What are some strengths of your robot? What are some of its shortcomings?" : "strengthsWeaknesses",
        "Does your robot usually score in the Low, Mid, or High row?" : "scoreRow",
        "During matches can your robot go up the Charge Station?" : "canCharge",
        "What are your robot's preferred starting locations? What are its auto options?" : "autoStart",
        "How do you usually intake? Is your intake specific to any one game piece?" : "howIntake",
        "How would you rate your Drive Team's level of experience/performance in this competition?" : "driveTeamExperience",
        "Any questions/additional comments for CardinalBotics? Anything we should know about your robot/team? " : "comments"
    },
    '2022': {"What role do you think the FIRST community has in the world, how has that role changed since its establishment?": "test"}
}

MATCH_SCHEME = {
    '2023': {
        "auto": {
            "ConeAttempts": "counter",
            "ConeLow": "counter",
            "ConeMid" : "counter",
            "ConeHigh": "counter",
            "CubeAttempts": "counter",
            "CubeLow" : "counter",
            "CubeMid" : "counter",
            "CubeHigh" : "counter",
            "Mobility" : "toggle",
            "Docked" : "toggle",
            "Engaged" : "toggle"
        },
        "teleop": {
            "ConeAttempts": "counter",
            "ConeLow": "counter",
            "ConeMid" : "counter",
            "ConeHigh": "counter",
            "CubeAttempts": "counter",
            "CubeLow" : "counter",
            "CubeMid" : "counter",
            "CubeHigh" : "counter",
            "IntakesSingle": "toggle",
            "IntakesDouble": "toggle"
        },
        "endgame": {
            "Parked" : "toggle",
            "Docked" : "toggle",
            "Engaged" : "toggle",
        },
        "comments": {
            "Defensive": "toggle",
            "DriverRating": "slider",
            "Fouls": "counter",
            "DriverComments": "text",
            "RobotComments": "text"
        }
    },
    '2022': {
        "test": {
            "counter": "counter",
            "slider": "slider",
            "toggle": "toggle",
            "text": "text"
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
    name TEXT NOT NULL,\n"""+(",\n".join([f"    {v} TEXT" for v in PIT_SCHEME[season].values()]))+"\n);"