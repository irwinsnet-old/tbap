import os
import pickle

import auth
import tbap.api as api


def store_local_data():
    sn_json = api.Session(auth.username, auth.key, season=2017,
                          data_format="json")
    sn_xml = api.Session(auth.username, auth.key, season=2017,
                         data_format="xml")

    os.chdir("C:/Users/stacy/OneDrive/Projects/FIRST_API/tbap/data")

    season_json = api.get_season(sn_json)
    with open("season_json.pickle", "wb") as f:
        pickle.dump(season_json, f, pickle.HIGHEST_PROTOCOL)

    season_xml = api.get_season(sn_xml)
    with open("season_xml.pickle", "wb") as f:
        pickle.dump(season_xml, f, pickle.HIGHEST_PROTOCOL)

    status_json = api.get_status(sn_json)
    with open("status_json.pickle", "wb") as f:
        pickle.dump(status_json, f, pickle.HIGHEST_PROTOCOL)

    status_xml = api.get_status(sn_xml)
    with open("status_xml.pickle", "wb") as f:
        pickle.dump(status_xml, f, pickle.HIGHEST_PROTOCOL)

    districts_json = api.get_districts(sn_json)
    with open("districts_json.pickle", "wb") as f:
        pickle.dump(districts_json, f, pickle.HIGHEST_PROTOCOL)

    districts_xml = api.get_districts(sn_xml)
    with open("districts_xml.pickle", "wb") as f:
        pickle.dump(districts_xml, f, pickle.HIGHEST_PROTOCOL)

    events_json = api.get_events(sn_json, district ="PNW")
    with open("events_json.pickle", "wb") as f:
        pickle.dump(events_json, f, pickle.HIGHEST_PROTOCOL)

    events_xml = api.get_events(sn_xml, district ="PNW")
    with open("events_jxml.pickle", "wb") as f:
        pickle.dump(events_xml, f, pickle.HIGHEST_PROTOCOL)

    teams_json = api.get_teams(sn_json, district ="PNW")
    with open("teams_json.pickle", "wb") as f:
        pickle.dump(teams_json, f, pickle.HIGHEST_PROTOCOL)

    teams_xml = api.get_teams(sn_xml, district ="PNW")
    with open("teams_xml.pickle", "wb") as f:
        pickle.dump(teams_xml, f, pickle.HIGHEST_PROTOCOL)