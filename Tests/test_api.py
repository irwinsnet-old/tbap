import json
import re
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET

import pytest
import pandas

import tbap.api as api
import tbap.server as server
import auth


class CheckResults(object):

    @staticmethod
    def frame(frame, test_data, mod_time=None):
        CheckResults.attr(frame.attr)
        assert isinstance(frame, pandas.DataFrame)
        assert frame.attr["args"] == test_data["args"]
        assert frame.shape == test_data["shape"]
        idx, col, value = test_data["spotcheck"]
        assert frame.loc[idx, col] == value
        assert server.httpdate_to_datetime(frame.attr["Last-Modified"])
        json.loads(frame.attr["text"])  # Verify that "text" is valid JSON text.

    @staticmethod
    def dict(dictionary, test_data):
        CheckResults.attr(dictionary)
        assert isinstance(dictionary, dict)
        assert dictionary["frame_type"] == test_data["frame_type"]
        if dictionary["text_format"] == "json":
            return json.loads(dictionary["text"])  # Verify "text" valid JSON.
        elif dictionary["text_format"] == "xml":
            return ET.fromstring(dictionary["text"])  # Verify "text valid XML.
        else:
            pytest.fail("dict['text_format'] invalid. Should be 'xml' or "
                        "'json'. Instead contains " + dictionary["text_format"])

    @staticmethod
    def attr(attr, mod_time=None):
        assert attr["code"] == 200
        if "Last-Modified" in attr.keys():
            assert server.httpdate_to_datetime(attr["Last-Modified"])
        assert server.httpdate_to_datetime(attr["Date"])
        assert re.match("https://www.thebluealliance.com/api/v3/",
                        attr["url"]) is not None
        assert isinstance(attr["args"], list)
        assert attr["X-TBA-Version"] == "3"

    @staticmethod
    def empty(result, mod_time):
        assert isinstance(result, dict)
        assert "text" not in result
        assert result["code"] == 304
        assert server.httpdate_to_datetime(result["If-Modified-Since"])
        assert result["If-Modified-Since"] == mod_time


class TestStatus(object):

    def test_status(self):
        sn = api.Session(auth.username, auth.key)
        status = api.get_status(sn)
        tdata = {"shape": (10, 1), "args": ["status"],
                 "spotcheck": ("max_season", "value", 2018)}
        CheckResults.frame(status, tdata)

    def test_badkey(self):
        sn = api.Session(auth.username, "bad_key")
        with pytest.warns(UserWarning):
            status = api.get_status(sn)
        assert status["code"] == 401
        assert status["error_message"] == "HTTPError, Code 401: Unauthorized"


class TestDistricts(object):

    def test_districts(self):
        sn = api.Session(auth.username, auth.key)
        dist = api.get_districts(sn, 2017)
        tdata = {"shape": (10, 4), "args": ["districts", 2017],
                 "spotcheck": (9, "key", "2017pnw")}
        CheckResults.frame(dist, tdata)

        lm = dist.attr["Last-Modified"]
        dist2 = api.get_districts(sn, 2017, mod_since=lm)
        CheckResults.empty(dist2, lm)


class TestTeams(object):

    def test_full(self):
        sn = api.Session(auth.username, auth.key)
        teams = api.get_teams(sn, page=1)
        tdata = {"shape": (378, 19), "args": ["teams", 1],
                 "spotcheck": (1, "nickname", "The PowerKnights")}
        CheckResults.frame(teams, tdata)

        lm = teams.attr["Last-Modified"]
        teams = api.get_teams(sn, page=1, mod_since=lm)
        CheckResults.empty(teams, lm)

    def test_simple(self):
        sn = api.Session(auth.username, auth.key)
        teams = api.get_teams(sn, page=1, response="simple")
        tdata = {"shape": (378, 7), "args": ["teams", 1, "simple"],
                 "spotcheck": (3, "state_prov", "Michigan")}
        CheckResults.frame(teams, tdata)

    def test_keys(self):
        sn = api.Session(auth.username, auth.key)
        teams = api.get_teams(sn, page=1, response="keys")
        tdata = {"shape": (378, 1), "args": ["teams", 1, "keys"],
                 "spotcheck": (370, "team", "frc990")}
        CheckResults.frame(teams, tdata)


class TestTeam(object):

    def test_full(self):
        sn = api.Session(auth.username, auth.key)
        team = api.get_team(sn, "frc1318")
        tdata = {"shape": (1, 19), "args": ["team", "frc1318"],
                 "spotcheck": (0, "motto", "Robots Don't Quit!")}
        CheckResults.frame(team, tdata)

    def test_simple(self):
        sn = api.Session(auth.username, auth.key)
        team = api.get_team(sn, "frc1318", response="simple")
        tdata = {"shape": (1, 7), "args": ["team", "frc1318", "simple"],
                 "spotcheck": (0, "team_number", 1318)}
        CheckResults.frame(team, tdata)

    def test_years(self):
        sn = api.Session(auth.username, auth.key)
        team = api.get_team(sn, "frc1318", response="years_participated")
        tdata = {"shape": (15, 1),
                 "args": ["team", "frc1318", "years_participated"],
                 "spotcheck": (0, "year", 2004)}
        CheckResults.frame(team, tdata)

    def test_robots(self):
        sn = api.Session(auth.username, auth.key)
        team = api.get_team(sn, "frc1318", response="robots")
        tdata = {"shape": (4, 4), "args": ["team", "frc1318", "robots"],
                 "spotcheck": (2, "robot_name", "Cerberus")}
        CheckResults.frame(team, tdata)


class TestEvents(object):

    def test_year_full(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, year=2016)
        tdata = {"shape": (203, 30), "args": ["events", 2016],
                 "spotcheck": (189, "city", "Auburn")}
        CheckResults.frame(events, tdata)

    def test_year_simple(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, year=2016, response="simple")
        tdata = {"shape": (203, 11), "args": ["events", 2016, "simple"],
                 "spotcheck": (196, "event_code", "wasno")}
        CheckResults.frame(events, tdata)

    def test_year_keys(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, year=2016, response="keys")
        tdata = {"shape": (203, 1), "args": ["events", 2016, "keys"],
                 "spotcheck": (196, "key", "2016wasno")}
        CheckResults.frame(events, tdata)

    def test_district_full(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, district="2017pnw")
        tdata = {"shape": (10, 33), "args": ["district", "2017pnw", "events"],
                 "spotcheck": (6, "short_name",
                               "Central Washington University")}
        CheckResults.frame(events, tdata)

    def test_team_simple(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, team="frc1318", year="2017")
        tdata = {"shape": (8, 30), "args": ["team", "frc1318", "events", "2017"],
                 "spotcheck": (0, "short_name", "Einstein (Houston)")}
        CheckResults.frame(events, tdata)

    def test_event_simple(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, event="2017tur")
        tdata = {"shape": (1, 30), "args": ["event", "2017tur"],
                 "spotcheck": (0, "postal_code", 77010)}
        CheckResults.frame(events, tdata)


class TestMatches(object):

    def test_event_full(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, "2017tur")
        tdata = {"shape": (770, 49), "args": ["event", "2017tur", "matches"],
                 "spotcheck": (765, "team_key", "frc1318")}
        CheckResults.frame(matches, tdata)

    def test_event_simple(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, "2017tur", response="simple")
        tdata = {"shape": (770, 13),
                 "args": ["event", "2017tur", "matches", "simple"],
                 "spotcheck": (2, "predicted_time", "2017-04-22 10:19:01")}
        CheckResults.frame(matches, tdata)

    def test_event_keys(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, "2017tur", response="keys")
        tdata = {"shape": (128, 1),
                 "args": ["event", "2017tur", "matches", "keys"],
                 "spotcheck": (60, "key", "2017tur_qm43")}
        CheckResults.frame(matches, tdata)

    def test_event_team_simple(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, "2017tur", team="frc1318",
                                  response="simple")
        tdata = {"shape": (102, 13),
                 "args": ["team", "frc1318", "event", "2017tur", "matches",
                          "simple"],
                 "spotcheck": (55, "team_key", "frc2046")}
        CheckResults.frame(matches, tdata)

    def test_team_year_full(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, team="frc1318", year="2017")
        assert True
        # tdata = {"shape": (102, 13),
        #          "args": ["team", "frc1318", "event", "2017tur", "matches",
        #                   "simple"],
        #          "spotcheck": (55, "team_key", "frc2046")}

# Old stuff after this line ====================================================


class TestSeason(object):

    def test_2017(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        season = api.get_season(sn)
        tdata = {"frame_type": "season", "shape": (2, 8),
                 "spotcheck": ("teamCount", 0, 3372)}
        CheckResults.frame(season, tdata)

    def test_2016(self):
        sn = api.Session(auth.username, auth.key, season='2016')
        season = api.get_season(sn)
        tdata = {"frame_type": "season", "shape": (1, 8),
                 "spotcheck": ("teamCount", 0, 3140)}
        CheckResults.frame(season, tdata)

    def test_xml(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        sn.data_format = "xml"
        season = api.get_season(sn)
        tdata = {"frame_type": "season"}
        CheckResults.dict(season, tdata)

    def test_local(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        sn.source = "local"
        season = api.get_season(sn)
        tdata = {"frame_type": "season", "shape": (2, 8),
                 "spotcheck": ("teamCount", 0, 3372)}
        CheckResults.frame(season, tdata)


class TestSchedule(object):

    def test_df(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        schedule = api.get_schedule(sn, event="TURING", team=1318)
        tdata = {"frame_type": "schedule", "shape": (60, 8),
                 "spotcheck": ("teamNumber", 3, 1318)}
        CheckResults.frame(schedule, tdata)


class TestHybrid(object):

    def test_hybrid(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        hybrid = api.get_hybrid(sn, event="TURING")
        tdata = {"frame_type": "hybrid", "shape": (672, 16),
                 "spotcheck": ("scoreBlueFinal", 670, 255)}
        CheckResults.frame(hybrid, tdata)

        lm = "Fri, 21 Apr 2017 13:43:00 GMT"
        hyb2 = api.get_hybrid(sn, event="TURING", only_mod_since=lm)
        tdata = {"frame_type": "hybrid", "shape": (348, 16),
                 "spotcheck": ("matchNumber", 0, 55)}
        CheckResults.frame(hyb2, tdata, lm)



class TestScores(object):

    def test_scores(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        scores = api.get_scores(sn, event="TURING", level="playoff")
        tdata = {"frame_type": "scores", "shape": (32, 36),
                 "spotcheck": ("autoPoints", 21, 89)}
        CheckResults.frame(scores, tdata)


class TestAlliances(object):

    def test_alliances(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        alliances = api.get_alliances(sn, event="TURING")
        tdata = {"frame_type": "alliances", "shape": (8, 9),
                 "spotcheck": ("captain", 2, 1318)}
        CheckResults.frame(alliances, tdata)


class TestRankings(object):

    def test_rankings(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        rankings = api.get_rankings(sn, event="TURING")
        tdata = {"frame_type": "rankings", "shape": (67, 14),
                 "spotcheck": ("teamNumber", 2, 1318)}

