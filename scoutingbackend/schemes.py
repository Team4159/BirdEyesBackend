import typing

def flatten(scheme: dict[str, dict[str, str]]) -> dict[str, str]:
    out = {}
    for k, v in scheme.items():
        for k1, v1 in v.items():
            out[k+k1.capitalize()] = MATCH_SCHEME_DATATYPES[v1]
    return out

def generate_table_schemas(season: str, event: str) -> tuple[str, str]:
        table_name = f"frc{season}{event}"
        flattened_scheme = flatten(MATCH_SCHEME[season])
        eschema_middle = ", ".join(f"{name} {type_}" for name, type_ in flattened_scheme.items())
        pschema_middle = ", ".join(f"{question_name} TEXT" for question_name in PIT_SCHEME[season].values())
        eschema = f"""CREATE TABLE IF NOT EXISTS {table_name}_match (match TEXT NOT NULL, teamNumber INTEGER NOT NULL, scouter TEXT NOT NULL, {eschema_middle}, PRIMARY KEY (match, teamNumber));"""
        pschema = f"""CREATE TABLE IF NOT EXISTS {table_name}_pit (teamNumber INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, {pschema_middle});"""
        
        return (eschema, pschema)

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
    '2022': {
        "What role do you think the FIRST community has in the world, how has that role changed since its establishment?": "test"
    }
}

MATCH_SCHEME = {
    '2023': {
        "auto": {
            "ConeAttempted": "counter",
            "ConeLow": "counter",
            "ConeMid" : "counter",
            "ConeHigh": "counter",
            "CubeAttempted": "counter",
            "CubeLow" : "counter",
            "CubeMid" : "counter",
            "CubeHigh" : "counter",
            "mobility" : "toggle",
            "docked" : "toggle",
            "engaged" : "toggle"
        },
        "teleop": {
            "coneAttempted": "counter",
            "coneLow": "counter",
            "coneMid" : "counter",
            "coneHigh": "counter",
            "cubeAttempted": "counter",
            "cubeLow" : "counter",
            "cubeMid" : "counter",
            "cubeHigh" : "counter",
        },
        "endgame": {
            "parked" : "toggle",
            "docked" : "toggle",
            "engaged" : "toggle",
        },
        "comments": {
            "driverRating" : "slider",
            "fouls" : "counter",
            "driverComments": "text",
            "robotComments": "text"
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