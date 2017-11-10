import json
import re
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET

import pytest

import tbap.api as api
import tbap.server as server
import auth


class CheckResults(object):

    @staticmethod
    def frame(frame, test_data, mod_time=None):
        CheckResults.attr(frame.attr, mod_time)
        assert isinstance(frame, server.Dframe)
        assert frame.attr["frame_type"] == test_data["frame_type"]
        assert frame.shape == test_data["shape"]
        assert frame.index.min() == 0
        assert frame.index.max() == (test_data["shape"][0] - 1)
        assert frame.index.is_monotonic_increasing
        col, row, value = test_data["spotcheck"]
        assert frame[col][row] == value
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
        assert re.match("'https://www.thebluealliance.com/api/v3/",
                        attr["url"]) is not None
        assert isinstance(attr["args"], list)
        assert attr["X-TBA-Version"] == "3"
        # else:
        #     assert attr["args"] in ["status"]
        # assert server.httpdate_to_datetime(attr["time_downloaded"], False)
        # if mod_time is None:
        #     assert attr["mod_since"] is None
        #     assert attr["only_mod_since"] is None
        # else:
        #     assert ((attr["mod_since"] is None) or
        #             (attr["only_mod_since"] is None))
        #     assert ((attr["mod_since"] == mod_time) or
        #             (attr["only_mod_since"] == mod_time))
        # assert re.match("https://frc-api.firstinspires.org/v2.0",
        #                 attr["url"]) is not None
        # CheckResults.local(attr)


    @staticmethod
    def empty(result, mod_time):
        if isinstance(result, server.Dframe):
            attr = result.attr
        else:
            attr = result

        assert attr["text"] is None
        assert attr["code"] == 304
        if attr["mod_since"] is not None:
            frame_col_name = "If-Modified-Since"
            assert attr["mod_since"] == mod_time
            assert attr["only_mod_since"] is None
        elif attr["only_mod_since"] is not None:
            frame_col_name = "FMS-OnlyModifiedSince"
            assert attr["only_mod_since"] == mod_time
            assert attr["mod_since"] is None
        else:
            # Test should fail if both "mod_since" and "only_mod_since" are None
            assert attr["mod_since"] is not None
            assert attr["only_mod_since"] is not None
            frame_col_name = ""
        if isinstance(result, server.Dframe):
            assert result[frame_col_name][0] == mod_time


class TestStatus(object):

    def test_status(self):
        sn = api.Session(key)
        status = api.get_status(sn)
        print()
        print(status)


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


class TestDistricts(object):

    def test_df(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        districts = api.get_districts(sn)
        tdata = {"frame_type": "districts", "shape": (10, 3),
                 "spotcheck": ("code", 0, "IN")}
        CheckResults.frame(districts, tdata)

        # Test no data and 304 code returned when mod_since used.
        lmod = server.httpdate_addsec(districts.attr["Last-Modified"], True)
        dist2 = api.get_districts(sn, mod_since=lmod)
        CheckResults.empty(dist2, lmod)

        # Test no data and 304 code returned when only_mod_since used.
        dist3 = api.get_districts(sn, only_mod_since=lmod)
        CheckResults.empty(dist3, lmod)


class TestEvents(object):

    def test_df(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        events = api.get_events(sn, district="PNW")
        tdata = {"frame_type": "events", "shape": (10, 15),
                 "spotcheck": ("code", 0, "ORLAK")}
        CheckResults.frame(events, tdata)

        # Test no data and 304 code returned when mod_since used.
        lmod = server.httpdate_addsec(events.attr["Last-Modified"], True)
        events2 = api.get_events(sn, district="PNW", mod_since=lmod)
        CheckResults.empty(events2, lmod)

        # Test no data and 304 code returned when only_mod_since used.
        events3 = api.get_events(sn, district="PNW", only_mod_since=lmod)
        CheckResults.empty(events3, lmod)


class TestTeams(object):

    def test_df(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        teams = api.get_teams(sn, district="PNW")
        tdata = {"frame_type": "teams", "shape": (155, 16),
                 "spotcheck": ("teamNumber", 13, 1318)}
        CheckResults.frame(teams, tdata)

        lmod = server.httpdate_addsec(teams.attr["Last-Modified"], True)
        teams2 = api.get_teams(sn, district="PNW", mod_since=lmod)
        CheckResults.empty(teams2, lmod)

    def test_page(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        teams = api.get_teams(sn, district="PNW", page="2")
        tdata = {"frame_type": "teams", "shape": (65, 16),
                 "spotcheck": ("nameShort", 64, "Aluminati")}
        CheckResults.frame(teams, tdata)

        lmod = server.httpdate_addsec(teams.attr["Last-Modified"], True)
        teams2 = api.get_teams(sn, district="PNW", page="2",
                               only_mod_since=lmod)
        CheckResults.empty(teams2, lmod)


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


class TestMatches(object):

    def test_matches(self):
        sn = api.Session(auth.username, auth.key, season='2017')
        matches = api.get_matches(sn, event="TURING")
        tdata = {"frame_type": "matches", "shape": (672, 14),
                 "spotcheck": ("teamNumber", 39, 1318)}
        CheckResults.frame(matches, tdata)


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

