import pytest
import os
import datetime
import pickle

import tbap.server as server
import tbap.api as api


class TestSession(object):

    def test_creation(self):
        session = api.Session("username", "key")

        assert session.username == "username"
        assert session.key == "key"
        assert session.season == int(
            datetime.date.today().strftime("%Y"))
        assert session.data_format == "dataframe"
        assert session.source == "production"

    def test_season(self):
        session = api.Session("username", "key", season='2017')
        assert session.season == 2017

    def test_errors(self):
        with pytest.raises(ValueError):
            api.Session("username", "key", season=2014)

        with pytest.raises(ValueError):
            future_year = int(datetime.date.today().strftime("%Y")) + 2
            api.Session("username", "key", season=future_year)

        with pytest.raises(TypeError):
            session = api.Session("username", "key")
            session.data_format = True

        with pytest.raises(ValueError):
            session = api.Session("username", "key")
            session.data_format = "yaml"

        with pytest.raises(TypeError):
            api.Session(42, "key")

        with pytest.raises(TypeError):
            api.Session("username", True)


class TestInternalFunctions(object):

    def test_build_url(self):
        sn = api.Session("username", "key", source="staging")
        args = {"eventCode": None, "teamNumber": "1318",
                "excludeDistrict": False}
        url = server.build_first_url(sn, "districts", args)
        assert url == ("https://frc-staging-api.firstinspires.org" +
                       "/v2.0/2017/districts" +
                       "?teamNumber=1318&excludeDistrict=false")


class TestHttpDate(object):

    def test_http_date(self):
        date_str1= "Wed, 30 Aug 2017 06:49:32 GMT"
        date_dt1 = server.httpdate_to_datetime(date_str1, True)
        assert date_dt1.tzname() == "GMT"
        assert date_dt1.hour == 6
        assert date_dt1.month == 8

        date_str2 = server.datetime_to_httpdate(date_dt1, True)
        assert date_str1 == date_str2

        date_str3 = server.httpdate_addsec(date_str1, True)
        assert date_str3 == "Wed, 30 Aug 2017 06:49:33 GMT"


class TestLocalData(object):

    def test_season_json(self):
        os.chdir(
            "C:/Users/stacy/OneDrive/Projects/FIRST_API/tbap/data")
        with open("season_json.pickle", 'rb') as f:
            local_data = pickle.load(f)
            print(type(local_data))
            print(local_data.keys())
            print(local_data["text"])


class TestNormJSON(object):

    def test_json(self):
        os.chdir("C:/Users/stacy/OneDrive/Projects/FIRST_API/tbap/JSON")
        with open("schedule.json") as file:
            json_txt = file.read()
