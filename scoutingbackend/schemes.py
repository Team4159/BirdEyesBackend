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
    }
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
    }
}

DB_SCHEME = {
    "2023": f"""CREATE TABLE IF NOT EXISTS {{event}}_match (
        qual TEXT NOT NULL,
        teamNumber INTEGER NOT NULL,

        autoConeAttempt INTEGER,
        autoConeLow INTEGER,
        autoConeMid INTEGER,
        autoConeHigh INTEGER,
        autoMobility INTEGER,
        teleopConeAttempt INTEGER,
        teleopConeLow INTEGER,
        teleopConeMid INTEGER,
        teleopCodeHigh INTEGER,
        endgameDock INTEGER,
        endgameEngage INTEGER,
        driverRating INTEGER,
        driverFouls INTEGER,

        PRIMARY KEY (qual, teamNumber)
    );
    CREATE TABLE IF NOT EXISTS {{event}}_pit (
        teamNumber INTEGER PRIMARY KEY NOT NULL,
        {" TEXT,".join(PIT_SCHEME['2023'].values())+" TEXT"}
    );
    """
}