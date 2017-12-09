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
        if "index_name" in test_data:
            assert frame.index.name == test_data["index_name"]
        if "spotcheck" in test_data:
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
        tdata = {"shape": (10, 3), "args": ["districts", 2017],
                 "index_name": "key",
                 "spotcheck": ("2017pnw", "display_name", "Pacific Northwest")}
        CheckResults.frame(dist, tdata)

        lm = dist.attr["Last-Modified"]
        dist2 = api.get_districts(sn, 2017, mod_since=lm)
        CheckResults.empty(dist2, lm)


class TestTeams(object):

    def test_full(self):
        sn = api.Session(auth.username, auth.key)
        teams = api.get_teams(sn, page=1)
        tdata = {"shape": (378, 18), "args": ["teams", 1],
                 "index_name": "key",
                 "spotcheck": ("frc501", "nickname", "The PowerKnights")}
        CheckResults.frame(teams, tdata)

        lm = teams.attr["Last-Modified"]
        teams = api.get_teams(sn, page=1, mod_since=lm)
        CheckResults.empty(teams, lm)

    def test_simple(self):
        sn = api.Session(auth.username, auth.key)
        teams = api.get_teams(sn, page=1, response="simple")
        tdata = {"shape": (378, 6), "args": ["teams", 1, "simple"],
                 "index_name": "key",
                 "spotcheck": ("frc503", "state_prov", "Michigan")}
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
        tdata = {"shape": (1, 18), "args": ["team", "frc1318"],
                 "index_name": "key",
                 "spotcheck": ("frc1318", "motto", "Robots Don't Quit!")}
        CheckResults.frame(team, tdata)

    def test_simple(self):
        sn = api.Session(auth.username, auth.key)
        team = api.get_team(sn, "frc1318", response="simple")
        tdata = {"shape": (1, 6), "args": ["team", "frc1318", "simple"],
                 "index_name": "key",
                 "spotcheck": ("frc1318", "team_number", 1318)}
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
        tdata = {"shape": (4, 3), "args": ["team", "frc1318", "robots"],
                 "index_name": "key",
                 "spotcheck": ("frc1318_2017", "robot_name", "Cerberus")}
        CheckResults.frame(team, tdata)


class TestEvents(object):

    def test_year_full(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, year=2016)
        tdata = {"shape": (203, 32), "args": ["events", 2016],
                 "index_name": "key",
                 "spotcheck": ("2016waamv", "city", "Auburn")}
        CheckResults.frame(events, tdata)

    def test_year_simple(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, year=2016, response="simple")
        tdata = {"shape": (203, 13), "args": ["events", 2016, "simple"],
                 "spotcheck": ("2016wasno", "city", "Snohomish")}
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
        tdata = {"shape": (10, 32), "args": ["district", "2017pnw", "events"],
                 "spotcheck": ("2017waamv", "postal_code", "98092")}
        CheckResults.frame(events, tdata)

    def test_team_simple(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, team="frc1318", year="2017")
        tdata = {"shape": (8, 32), "args": ["team", "frc1318", "events",
                                            "2017"],
                 "spotcheck": ("2017cmptx", "event_type_string",
                               "Championship Finals")}
        CheckResults.frame(events, tdata)

    def test_event_simple(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, event="2017tur", response="simple")
        tdata = {"shape": (1, 10), "args": ["event", "2017tur", "simple"],
                 "spotcheck": ("2017tur", "name", "Turing Division")}
        CheckResults.frame(events, tdata)


class TestMatches(object):

    def test_event_full(self):
        sn = api.Session(auth.username, auth.key)
        sn.time_zone = "America/Chicago"
        matches = api.get_matches(sn, "2017tur")
        tdata = {"shape": (770, 47), "args": ["event", "2017tur", "matches"]}
        CheckResults.frame(matches, tdata)
        assert matches.loc["2017tur_f1m2"].at["frc1318", "score"] == 461

    def test_event_simple(self):
        sn = api.Session(auth.username, auth.key, time_zone="America/Chicago")
        matches = api.get_matches(sn, "2017tur", response="simple")
        tdata = {"shape": (770, 12),
                 "args": ["event", "2017tur", "matches", "simple"]}
        CheckResults.frame(matches, tdata)
        CheckResults.timestamp(matches.loc["2017tur_f1m2"].at["frc2046",
                                                              "time"],
                               2017, 4, 22, 12, 13, 0, 68400)
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
        tdata = {"shape": (102, 12),
                 "args": ["team", "frc1318", "event", "2017tur", "matches",
                          "simple"]}
        assert matches.loc["2017tur_qm52"].at["frc1318", "score"] == 253
        CheckResults.frame(matches, tdata)

    def test_team_year_full(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, team="frc1318", year="2017")
        tdata = {"shape": (642, 47),
                 "args": ["team", "frc1318", "matches", "2017"]}
        assert matches.loc["2017tur_f1m1"].at["frc2046",
                                              "teleopFuelPoints"] == 21
        CheckResults.frame(matches, tdata)

    def test_match(self):
        sn = api.Session(auth.username, auth.key)
        matches = api.get_matches(sn, match="2017wasno_qm79")
        tdata = {"shape": (6, 47),
                 "args": ["match", "2017wasno_qm79"]}
        CheckResults.frame(matches, tdata)
        act_time = matches.loc["2017wasno_qm79"].at["frc4077", "actual_time"]
        CheckResults.timestamp(act_time,
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


class TestAlliances(object):

    def test_event(self):
        sn = api.Session(auth.username, auth.key)
        alliances = api.get_alliances(sn, event="2017pncmp")
        tdata = {"shape": (25, 11),
                 "args": ["event", "2017pncmp", "alliances"]}
        CheckResults.frame(alliances, tdata)
        assert alliances.loc["Alliance 8", "frc2907"]["current_level_wins"] == 1


class TestEventData(object):

    def test_get_insights(self):
        sn = api.Session(auth.username, auth.key)
        insights = api.get_insights(sn, event="2017pncmp")
        tdata = {"shape": (64, 3), "args": ["event", "2017pncmp", "insights"]}
        CheckResults.frame(insights, tdata)
        assert (insights.loc["qual", "average_fuel_points"].
                at["value_0"] == pytest.approx(7.652344))

    def test_get_oprs(self):
        sn = api.Session(auth.username, auth.key)
        oprs = api.get_oprs(sn, event="2017pncmp")
        tdata = {"shape": (64, 3), "args": ["event", "2017pncmp", "oprs"]}
        CheckResults.frame(oprs, tdata)
        assert oprs.loc["frc1595"].at["oprs"] == pytest.approx(100.205323)

    def test_get_predictions(self):
        sn = api.Session(auth.username, auth.key)
        pred = api.get_predictions(sn, event="2017pncmp")
        # Check event_stats
        tdata = {"shape": (14, 1),
                 "args": ["event", "2017pncmp", "predictions"]}
        CheckResults.frame(pred["event_stats"], tdata)
        assert (pred["event_stats"].loc["playoff", "brier_scores_gears"].
                at["value"] == pytest.approx(0.075659, rel=1e-5))

        # Check predictions
        tdata = {"shape": (2628, 1),
                 "args": ["event", "2017pncmp", "predictions"]}
        CheckResults.frame(pred["predictions"], tdata)
        assert (pred["predictions"].
                loc["qual", "2017pncmp_qm1", "blue", "gears"].
                at["value"] == pytest.approx(5.12684, rel=1e-5))

        # Check team rankings
        tdata = {"shape": (64, 2),
                 "args": ["event", "2017pncmp", "predictions"]}
        CheckResults.frame(pred["team_rankings"], tdata)
        assert (pred["team_rankings"].
                loc["frc2046"].
                at["points"] == pytest.approx(24, rel=1e-2))

        # Check team stats
        tdata = {"shape": (768, 1),
                 "args": ["event", "2017pncmp", "predictions"]}
        CheckResults.frame(pred["team_stats"], tdata)
        assert (pred["team_stats"].
                loc["frc2907", "score", "mean", "playoff"].
                at["value"] == pytest.approx(108.635760, rel=1e-5))




class TestTS(object):

    def test_expand_col(self):
        sn = api.Session(auth.username, auth.key)
        events = api.get_events(sn, year=2016)
        print(events)