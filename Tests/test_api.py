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

    @staticmethod
    def timestamp(ts, year, month, day, hour, minute, second, offset):
        assert ts.year == year
        assert ts.month == month
        assert ts.day == day
        assert ts.hour == hour
        assert ts.minute == minute
        assert ts.second == second
        assert ts.utcoffset().seconds == offset


class TestStatus(object):

    def test_status(self):
        sn = api.Session(auth.username, auth.key)
        status = api.get_status(sn)
        tdata = {"shape": (14, 1), "args": ["status"],
                 "spotcheck": ("max_season", "value", 2018)}
        CheckResults.frame(status, tdata)

    # This test only passes if it is the first test run. The Blue
    # Alliance will accept incorrect authorization keys if the
    # user has recently logged in with a valid key.
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
        tdata = {"shape": (8, 30), "args": ["team", "frc1318", "events",
                                            "2017"],
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
        sn = api.Session(auth.username, auth.key, time_zone="America/Chicago")
        matches = api.get_matches(sn, "2017tur", response="simple")
        tdata = {"shape": (770, 14),
                 "args": ["event", "2017tur", "matches", "simple"],
                 "spotcheck": (2, "score", 503)}
        CheckResults.frame(matches, tdata)
        CheckResults.timestamp(matches.time[0], 2017, 4, 22, 12, 0, 0, 68400)
        assert matches.attr["timezone"] == "America/Chicago"

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
        tdata = {"shape": (102, 14),
                 "args": ["team", "frc1318", "event", "2017tur", "matches",
                          "simple"],
                 "spotcheck": (55, "team_key", "frc2046")}
        CheckResults.frame(matches, tdata)

    def test_team_year_full(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, team="frc1318", year="2017")
        tdata = {"shape": (642, 49),
                 "args": ["team", "frc1318", "matches", "2017"],
                 "spotcheck": (641, "score", 259)}
        CheckResults.frame(matches, tdata)

    def test_match(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, match="2017wasno_qm79")
        tdata = {"shape": (6, 49),
                 "args": ["match", "2017wasno_qm79"],
                 "spotcheck": (3, "team_key", "frc3070")}
        CheckResults.frame(matches, tdata)
        CheckResults.timestamp(matches.actual_time[5],
                               2017, 3, 26, 11, 24, 20, 61200)


class TestDistrictRankings(object):

    def test_rankings(self):
        sn = api.Session(auth.username, auth.key)
        rankings = api.get_district_rankings(sn, "2017pnw")
        tdata = {"shape": (376, 11),
                 "args": ["district", "2017pnw", "rankings"],
                 "spotcheck": (0, "team_key", "frc3238")}
        CheckResults.frame(rankings, tdata)


class TestAwards(object):

    def test_team_year(self):
        sn = api.Session(auth.username, auth.key)
        awards = api.get_awards(sn, team="frc1318", year=2017)
        tdata = {"shape": (9, 6),
                 "args": ["team", "frc1318", "awards", 2017],
                 "spotcheck": (8, "name", "District Chairman's Award")}
        CheckResults.frame(awards, tdata)

    def test_team(self):
        sn = api.Session(auth.username, auth.key)
        awards = api.get_awards(sn, team="frc1318")
        tdata = {"shape": (57, 6),
                 "args": ["team", "frc1318", "awards"],
                 "spotcheck": (15, "event_key", "2014waahs")}
        CheckResults.frame(awards, tdata)

    def test_team_event(self):
        sn = api.Session(auth.username, auth.key)
        awards = api.get_awards(sn, team="frc1318", event="2017pncmp")
        tdata = {"shape": (3, 6),
                 "args": ["team", "frc1318", "event", "2017pncmp", "awards"],
                 "spotcheck": (0, "team_key", "frc3238")}
        CheckResults.frame(awards, tdata)

    def test_event(self):
        sn = api.Session(auth.username, auth.key)
        awards = api.get_awards(sn, event="2017tur")
        tdata = {"shape": (15, 6),
                 "args": ["event", "2017tur", "awards"],
                 "spotcheck": (3, "team_key", "frc2907")}
        CheckResults.frame(awards, tdata)
