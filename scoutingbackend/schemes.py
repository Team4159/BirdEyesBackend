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
        eschema = f"""CREATE TABLE IF NOT EXISTS {table_name}_match (match TEXT NOT NULL, teamNumber INTEGER NOT NULL, name TEXT NOT NULL, {eschema_middle}, PRIMARY KEY (match, teamNumber, name));"""
        pschema = f"""CREATE TABLE IF NOT EXISTS {table_name}_pit (teamNumber INTEGER NOT NULL, name TEXT NOT NULL, {pschema_middle});"""
        
        return (eschema, pschema)

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