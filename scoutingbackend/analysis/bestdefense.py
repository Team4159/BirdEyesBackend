from schemes import invert_alliance

from ..database import db

def get(season: int, event: str) -> dict[str, int]:
    c = db.cursor()
    table = f"frc{season}{event}_match"
    teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
    def k(team: str) -> int:
        netscore = 0
        for match in c.execute(f"select * from {table} where teamNumber={team}").fetchall():
            matchinfo = getmatchinfo()
            alliance = [a for a in matchinfo["alliances"] if "frc"+match["teamNumber"] in a["team_keys"]]
            if len(alliance) != 1:
                raise Exception(f"[Analysis] Invalid Alliance. Team: {match['teamNumber']} @ Match: {match['match']}")
            alliance = alliance[0]
            driverskill = matchinfo["commentsDriverrating"]/((matchinfo["commentsFouls"]+1)*(0.7 if matchinfo["commentsDefensive"] == 1 else 1))
            defensescore= matchinfo["score_breakdown"][alliance]["foulPoints"]-matchinfo["score_breakdown"][invert_alliance[alliance]]["teleopPoints"]
            netscore += 2*driverskill*defensescore
        return netscore
    return dict(sorted(teams.items(), key=lambda item: item[1]))
def getmatchinfo():
    return {
        "actual_time":
        1676731568,
        "alliances": {
            "blue": {
                "dq_team_keys": [],
                "score": 75,
                "surrogate_team_keys": [],
                "team_keys": ["frc3467", "frc2423", "frc8724"]
            },
            "red": {
                "dq_team_keys": [],
                "score": 42,
                "surrogate_team_keys": [],
                "team_keys": ["frc238", "frc1721", "frc1512"]
            }
        },
        "comp_level":
        "qm",
        "event_key":
        "2023week0",
        "key":
        "2023week0_qm5",
        "match_number":
        5,
        "post_result_time":
        1676731793,
        "predicted_time":
        1676748000,
        "score_breakdown": {
            "blue": {
                "activationBonusAchieved": True,
                "adjustPoints": 0,
                "autoBridgeState": "Level",
                "autoChargeStationPoints": 12,
                "autoChargeStationRobot1": "Docked",
                "autoChargeStationRobot2": "None",
                "autoChargeStationRobot3": "None",
                "autoCommunity": {
                    "B": [
                        "None", "None", "None", "None", "None", "None", "None",
                        "None", "Cone"
                    ],
                    "M": [
                        "None", "None", "None", "None", "None", "None", "None",
                        "None", "None"
                    ],
                    "T": [
                        "None", "None", "None", "None", "None", "Cone", "None",
                        "None", "None"
                    ]
                },
                "autoDocked": True,
                "autoGamePieceCount": 2,
                "autoGamePiecePoints": 9,
                "autoMobilityPoints": 9,
                "autoPoints": 30,
                "coopGamePieceCount": 2,
                "coopertitionCriteriaMet": False,
                "endGameBridgeState": "Level",
                "endGameChargeStationPoints": 20,
                "endGameChargeStationRobot1": "Docked",
                "endGameChargeStationRobot2": "None",
                "endGameChargeStationRobot3": "Docked",
                "endGameParkPoints": 0,
                "foulCount": 3,
                "foulPoints": 0,
                "linkPoints": 5,
                "links": [{
                    "nodes": [4, 5, 6],
                    "row": "Top"
                }],
                "mobilityRobot1": "Yes",
                "mobilityRobot2": "Yes",
                "mobilityRobot3": "Yes",
                "rp": 3,
                "sustainabilityBonusAchieved": False,
                "techFoulCount": 0,
                "teleopCommunity": {
                    "B": [
                        "None", "None", "None", "None", "None", "None", "None",
                        "None", "Cone"
                    ],
                    "M": [
                        "None", "None", "None", "None", "None", "None", "None",
                        "None", "None"
                    ],
                    "T": [
                        "None", "Cube", "None", "None", "Cube", "Cone", "Cone",
                        "None", "Cone"
                    ]
                },
                "teleopGamePieceCount": 6,
                "teleopGamePiecePoints": 20,
                "teleopPoints": 40,
                "totalChargeStationPoints": 32,
                "totalPoints": 75
            },
            "red": {
                "activationBonusAchieved": False,
                "adjustPoints": 0,
                "autoBridgeState": "Level",
                "autoChargeStationPoints": 0,
                "autoChargeStationRobot1": "None",
                "autoChargeStationRobot2": "None",
                "autoChargeStationRobot3": "None",
                "autoCommunity": {
                    "B": [
                        "None", "None", "None", "None", "None", "None", "None",
                        "None", "None"
                    ],
                    "M": [
                        "None", "None", "None", "None", "None", "None", "None",
                        "None", "None"
                    ],
                    "T": [
                        "None", "None", "None", "None", "None", "None", "None",
                        "None", "None"
                    ]
                },
                "autoDocked": False,
                "autoGamePieceCount": 0,
                "autoGamePiecePoints": 0,
                "autoMobilityPoints": 3,
                "autoPoints": 3,
                "coopGamePieceCount": 2,
                "coopertitionCriteriaMet": False,
                "endGameBridgeState": "NotLevel",
                "endGameChargeStationPoints": 6,
                "endGameChargeStationRobot1": "Docked",
                "endGameChargeStationRobot2": "None",
                "endGameChargeStationRobot3": "None",
                "endGameParkPoints": 0,
                "foulCount": 0,
                "foulPoints": 15,
                "linkPoints": 0,
                "links": [],
                "mobilityRobot1": "Yes",
                "mobilityRobot2": "No",
                "mobilityRobot3": "No",
                "rp": 0,
                "sustainabilityBonusAchieved": False,
                "techFoulCount": 0,
                "teleopCommunity": {
                    "B": [
                        "None", "None", "Cube", "None", "None", "None", "None",
                        "None", "Cone"
                    ],
                    "M": [
                        "None", "Cube", "None", "Cone", "Cube", "None", "None",
                        "None", "None"
                    ],
                    "T": [
                        "None", "Cube", "None", "None", "None", "None", "None",
                        "None", "None"
                    ]
                },
                "teleopGamePieceCount": 6,
                "teleopGamePiecePoints": 18,
                "teleopPoints": 24,
                "totalChargeStationPoints": 6,
                "totalPoints": 42
            }
        },
        "set_number":
        1,
        "time":
        1676729520,
        "videos": [{
            "key": "InJGPng5MO8",
            "type": "youtube"
        }, {
            "key": "yoiE3y7uAgw",
            "type": "youtube"
        }],
        "winning_alliance":
        "blue"
    },
