import json
import re

import pytest
import pandas

import tbap.api as api
import tbap.server as server

key = "6Sx6a2gOyNWwNNTAd9UYBOpWp7MxaNrZgO4CqConwJwwDooKQV3DbZXvnk8TBL7A"
pandas.set_option('expand_frame_repr', False)

class TestTBA(object):

    def test_status(self):
        sn = api.Session("None", key, source="tba")

        url = server.build_tba_url(sn, "status")
        response = server.send_tba_request(sn, url, "status")
        print(response)

    def test_frame(self):
        sn = api.Session("None", key, source="tba")
        teams = api.send_request(sn, ["teams", 1])
        return(teams)
        # print(server.build_frame(teams))

    def test_teams(self):
        sn = api.Session(key)
        teams = api.get_teams(sn, page=1)
        print(teams.columns)

    def test_teams_year(self):
        sn = api.Session(key)
        teams = api.get_teams(sn, page=1, year=2016)
        print(teams.columns)

    def test_teams_district(self):
        sn = api.Session(key)
        sn.data_format="json"
        teams = api.get_teams(sn, district="pnw")
        print(teams.columns)

    def test_team(self):
        sn = api.Session(key)
        team = api.get_team(sn, team="frc1318", response="simple")
        print(team.columns)

    def test_event(self):
        sn = api.Session(key)
        team = api.get_events(sn, year=2016)
        print(team.columns)

    def test_matches(self):
        sn = api.Session(key)
        matches = api.get_matches(sn, "2017tur")
        print(list(matches.columns))

    def test_matches_simple(self):
        sn = api.Session(key)
        matches = api.send_request(sn,
                                   ["event", "2017tur", "matches", "simple"])

    def test_alliances(self):
        sn = api.Session(key)
        alliances = api.get_alliances(sn, "2017pncmp")
        print(alliances.columns)

    def test_insights(self):
        sn = api.Session(key)
        insights = api.get_insights(sn, "2017pncmp")
        # print(insights.columns)

    def test_predictions(self):
        sn = api.Session(key)
        insights = api.get_predictions(sn, "2017pncmp")
        print(insights["teams"])

    def test_event_rankings(self):
        sn = api.Session(key)
        ranks = api.get_event_rankings(sn, "2017pncmp")
        print()
        print(ranks)

    def test_district_points(self):
        sn = api.Session(key)
        points = api.get_district_points(sn, "2017pncmp")

    def test_status(self):
        sn = api.Session(key)
        status = api.get_status(sn)
        print()
        print(status)

    def test_event_team_status(self):
        sn = api.Session(key)
        team_rank = api.get_event_team_status(sn, "2017tur", team="frc1318")
        print()
        print(team_rank)

    def test_media(self):
        sn = api.Session(key)
        media = api.get_media(sn, "frc1318", "2017")
        print()
        print(media)

    def test_social_media(self):
        sn = api.Session(key)
        media = api.get_social_media(sn, "frc1318")
        print()
        print(media)