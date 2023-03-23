invert_alliance = {"red": "blue", "blue": "red"}

PIT_SCHEME = {
    '2023': {
        "experienceBuildseason": "What is your experience with FIRST so far? How did this build season go for you?",
        "strengthsWeaknesses": "How has your robot been doing in this competition? What are some strengths of your robot? What are some of its shortcomings?",
        "autoStart": "What are your robot's preferred starting locations? What are its auto options?",
        "canCharge": "During matches can your robot go up the Charge Station?",
        "howIntake": "How do you usually intake? Is your intake specific to any one game piece?",
        "scoreRow": "Does your robot usually score in the Low, Mid, or High row?",
        "driveTeamExperience": "How would you rate your Drive Team's level of experience/performance in this competition?",
        "comments": "Any questions/additional comments for CardinalBotics? Anything we should know about your robot/team?"
    },
    '2022': {"What role do you think the FIRST community has in the world, how has that role changed since its establishment?": "test"}
}

MATCH_SCHEME = {
    '2023': {
        "auto": {
            "ConeHigh": "counter",
            "CubeHigh": "counter",
            "ConeMid": "counter",
            "CubeMid": "counter",
            "ConeLow": "counter",
            "CubeLow": "counter",
            "ConeMisses": "counter",
            "CubeMisses": "counter",
            "Docked": "toggle",
            "Engaged": "toggle",
            "Mobility": "toggle",
        },
        "teleop": {
            "ConeHigh": "counter",
            "CubeHigh": "counter",
            "ConeMid": "counter",
            "CubeMid": "counter",
            "ConeLow": "counter",
            "CubeLow": "counter",
            "ConeMisses": "counter",
            "CubeMisses": "counter",
            "IntakesSingle": "toggle",
            "IntakesDouble": "toggle"
        },
        "endgame": {
            "Parked": "toggle",
            "Docked": "toggle",
            "Engaged": "toggle",
        },
        "comments": {
            "Defensive": "toggle",
            "DriverRating": "slider",
            "Fouls": "counter",
            "Disabled": "toggle",
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