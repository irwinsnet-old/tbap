"""

Output of tbap Functions
========================

The tbap package is designed to provide it's output as _Pandas_
dataframes, a powerful tabular format that supports basic sorting and
filtering, as well as many advanced data analysis techniques. By
default, fapy functions provide a `pandas.DataFrame` object. The
only difference
between the `'Pandas.Dataframe'` and `server.DFrame` classes is that
the DFrame has an _attr_ property that contains a python dictionary
with TBA Read API metadata, such as the time the data was downloaded from
the TBA Read API, and the URL used to obtain the data. Users can use the
_Pandas_ module to manipulate ``server.DFrame`` objects just as they
would ``Pandas.dataframe`` objects.

Fapy functions can also return Python dictionaries containing both
the requested data in either XML or JSON format and metadata. To
obtain XML or JSON data, set the `api.Session` objects data_format
property to either "xml" or "json". The XML or JSON text will be
available via the "text" key of the returned Python dictionary.

Common fapy Function Arguments
==============================

Fapy functions that send HTTP requests to the TBA Read API all require
many of the same arguments.

**session**
    An instance of ``fapy.classes.Session`` that contains a valid
    username and authorization key. Other useful properties of
    ``Session`` object include _season_ (2015, 2016, 2017, etc.)
    and _data/_format_ ("dataframe", "xml", or "json"). The
    _session_ argument is always required.

**event**
    A string containing a TBA Read API event code. Most fapy functions
    apply only to a single event, therefore we must specify the FRC
    event as an argument. For example, the event code for the Turing
    subdivision at the Houston FIRST World Champiionships is "TURING",
    and the event code for the district event in Mt. Vernon, WA is

Pandas Liense Text
==================

BSD 3-Clause License

Copyright (c) 2008-2012, AQR Capital Management, LLC, Lambda Foundry,
Inc. and PyData Development Team All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
import collections
import datetime
import json
import re
import numpy

import pandas.io.json
import pandas

import tbap.server as server


def send_request(session, http_args, mod_since=None, only_mod_since=None):
    """Routes data request to correct internal functions.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        cmd:
            A string that identifies the TBA Read API command.
        args:
            A Python dictionary.
        mod_since:
            A string containing an HTTP formatted date and time.
            Causes function to return None if no changes have been
            made to the requested data since the date and time provided.
            Optional.
        only_mod_since:
            A string containing an HTTP formatted date and
            time. Causes function to only return data that has
            changed since the date and time provided. Optional.

    Returns:
        Either a server.DFrame object (if session.data_format =
        "dataframe") or a Python dictionary.

    """
    response = server.send_http_request(session, http_args)
    if session.data_format == "dataframe":
        return server.build_frame(response)
    else:
        return response


def get_status(session):
    http_args = ["status"]
    data = server.send_http_request(session, http_args)
    if session.data_format != "dataframe":
        return data
    else:
        return server.build_single_column_frame(data["text"], data)


def get_teams(session,  # pylint: disable=too-many-arguments
              page=None, year=None, event=None, district=None,
              response="full",
              mod_since=None, only_mod_since=None):
    """Retrieves FRC teams from TBA Read API Server.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        team:
            FRC team number as a string. If listed, function will
            return data only for that team. Optional.
        event:
            A string containing the TBA Read API event code. If
            included, function will return only teams that are
            competing in that event. Use tbap.api.get_events to lookup
            event codes. Optional.
        district:
            A string containing the TBA Read API district code. If
            included, function will only return teams that are
            competing in that event. Optional.
        state:
            A string containing the name of the U.S. state, spelled
            out. If included, function will only return teams that are
            located in that state.
        page:
            A string containing the requested page number. The FIRST
            API splits long lists of teams into several pages and only
            returns one page at a time. For XML and JSON data, if page
            is omitted, the TBA Read API and this function will return
            only the first page of data. Users can retrieve subsequent
            pages of data by specifying a page number of '2' or higher.
            This argument is not needed if the dataframe data_format is
            requested becuase the function will request all pages of
            data and combine them into one dataframe. Optional.
        mod_since:
            A string containing an HTTP formatted date and time.
            Causes function to return None if no changes have been
            made to the requested data since the date and time provided.
            Optional.
        only_mod_since:
            A string containing an HTTP formatted date and
            time. Causes function to only return data that has
            changed since the date and time provided. Optional.

    Returns:
        If session.data_format == "json" or "xml", returns a Python
        dictionary object containing the response text and additional
        metadata. If session.data_format == "dataframe", returns an instances
        of tbap.server.Dframe, which is a Pandas dataframe with
        an additional `attr` property that contains a Python dictionary
        with additional metadata.
    """

    # Check for un-allowed combinations of arguments
    if ((page is not None) and (year is None) and (event is None) and
            (district is None)):
        # /teams/{page_num}
        http_args = ["teams", page]
    elif ((page is not None) and (year is not None) and (event is None) and
            (district is None)):
        http_args = ["teams", year, page]
    elif ((district is not None) and (year is None) and (event is None) and
              (page is None)):
        http_args = ["district", district, "teams"]
    elif ((event is not None) and (year is None) and (district is None) and
              (page is None)):
        http_args = ["event", event, "teams"]
    else:
        raise server.ArgumentError("Incorrect Arguments")
    if response.lower() in ["simple", "keys"]:
        http_args.append(response.lower())
    return send_request(session, http_args, mod_since, only_mod_since)


def get_team(session, team, response = "full", mod_since=None,
             only_mod_since=None):
    http_args = ["team", team]
    if response.lower() in ["simple", "years_participated", "robots"]:
        http_args.append(response.lower())
    return send_request(session, http_args, mod_since, only_mod_since)


def get_events(session,  # pylint: disable=too-many-arguments
               year=None, district=None, team=None, event=None, response="full",
               mod_since=None, only_mod_since=None):
    """Retrieves information on one or more FRC competitions.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        event:
            A string containing a FIRST event code.
        team:
            The four digit FRC team number as an integer.
        district:
            A string containing the FIRST district code, such as
            "PNW" for the Pacific Northwest district. Results will be
            filtered to the events occurring in that district. Use
            `districts()` to retrieve all district codes.
        exclude_district:
            A Boolean value. If True, filters results to
            events that are not affiliated with a district.
        mod_since:
            A string containing an HTTP formatted date and time.
            Causes function to return None if no changes have been
            made to the requested data since the date and time provided.
            Optional.
        only_mod_since:
            A string containing an HTTP formatted date and
            time. Causes function to only return data that has
            changed since the date and time provided. Optional.

    Returns:
        If session.data_format == "json" or "xml", returns a Python
        dictionary object containing the response text and additional
        metadata. If session.data_format == "dataframe", returns an instances
        of tbap.server.Dframe, which is a Pandas dataframe with
        an additional `attr` property that contains a Python dictionary
        with additional metadata.

    Raises:
        tbap.Classes.ArgumentError:
            If the `event` argument is specified and any other
            argument is specified in addition to `event` (i.e.,
            if `event` is specified, no other arguments should be
            used).
            If both the `district` and `exclude_district` arguments
            are specified (i.e., use one or the other but not both).
    """

    # Check for un-allowed combinations of arguments
    if year is not None and district is None and team is None and event is None:
        http_args = ["events", year]
    elif (district is not None and year is None and team is None and
            event is None):
        http_args = ["district", district, "events"]
    elif (team is not None and year is None and district is None and
            event is None):
        http_args = ["team", team, "events"]
    elif (team is not None and year is not None and district is None and
            event is None):
        http_args = ["team", team, "events", year]
    elif (event is not None and team is None and year is None and
            district is None and response != "keys"):
        http_args = ["event", event]
    else:
        raise server.ArgumentError("Incorrect Arguments")
    if response.lower() in ["simple", "keys"]:
        http_args.append(response.lower())
    return send_request(session, http_args, mod_since, only_mod_since)


def get_rankings(session, district, mod_since=None, only_mod_since=None):
    """Retrieves the team rankings based on the qualification rounds.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        event:
            A string containing the TBA Read API event code.
        team:
            FRC team number as a string. If listed, function will
            return data only for that team. Optional.
        top:
            The number of top-ranked teams to return in the result.
            Optional. Default is to return all teams at the event.
        mod_since:
            A string containing an HTTP formatted date and time.
            Causes function to return None if no changes have been
            made to the requested data since the date and time provided.
            Optional.
        only_mod_since:
            A string containing an HTTP formatted date and
            time. Causes function to only return data that has
            changed since the date and time provided. Optional.

    Returns:

    """
    http_args = ["district", district, "rankings"]
    return send_request(session, http_args, mod_since, only_mod_since)


def get_matches(session, event=None, team=None, year=None, match=None,
                response="full", mod_since=None, only_mod_since=None):
    if event is not None and team is None and year is None and match is None:
        http_args = ["event", event, "matches"]
    elif (team is not None and event is not None and year is None and
            match is None):
        http_args = ["team", team, "event", event, "matches"]
    elif (team is not None and year is not None and event is None and
            match is None):
        http_args = ["team", team, "matches", year]
    elif (match is not None and event is None and team is None and
            year is None and response in ["full", "simple"]):
        http_args = ["match", match]
    else:
        raise server.ArgumentError("Incorrect Arguments")
    if response.lower() in ["simple", "keys"]:
        http_args.append(response.lower())
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    if response.lower() == "keys":
        return server.build_frame(data)

    # Convert nested JSON text into a flat dataframe
    jdata = json.loads(data["text"])
    if not isinstance(jdata, list):
        jdata = [jdata]  # TBA returns single match when match arg used
    flat_match = {}
    for col in jdata[0].keys():
        if (not isinstance(jdata[0][col], list) and
                not isinstance(jdata[0][col], dict)):
            flat_match[col] = []
    flat_match["_alliance"] = []
    flat_match["_team_key"] = []
    flat_match["_surrogate"] = []
    flat_match["_score"] = []
    if "videos" in jdata[0]:
        flat_match["_videos"] = []

    if "score_breakdown" in jdata[0]:
        for col in jdata[0]["score_breakdown"]["blue"].keys():
            flat_match["*" + col] = []

    def append_match_data(mtch, team, alliance, surrogate):
        for key in flat_match.keys():
            if key[0:1] not in ["_", "*"]:
                flat_match[key].append(mtch[key])
            elif key[0:1] == "*":
                flat_match[key].append(
                    mtch["score_breakdown"][alliance][key[1:]])
        flat_match["_team_key"].append(team)
        flat_match["_alliance"].append(alliance)
        flat_match["_surrogate"].append(surrogate)
        if "_videos" in flat_match:
            flat_match["_videos"].append(str(mtch["videos"]))
        flat_match["_score"].append(mtch["alliances"][alliance]["score"])

    for mtch in jdata:
        for team in mtch["alliances"]["blue"]["team_keys"]:
            append_match_data(mtch, team, "blue", False)
        for team in mtch["alliances"]["blue"]["surrogate_team_keys"]:
            append_match_data(mtch, team, "blue", True)
        for team in mtch["alliances"]["red"]["team_keys"]:
            append_match_data(mtch, team, "red", False)
        for team in mtch["alliances"]["red"]["surrogate_team_keys"]:
            append_match_data(mtch, team, "red", True)

    # Convert Unix timestamps to human readable time strings
    def to_time(timestamp):
        if isinstance(timestamp, int):
            return datetime.datetime.fromtimestamp(timestamp).isoformat(" ")
        else:
            return numpy.nan
    for col in [tcl for tcl in flat_match.keys() if tcl[-4:] == "time"]:
        iso_time = list(map(to_time, flat_match[col]))
        flat_match[col] = iso_time

    df = pandas.DataFrame(flat_match)
    df.columns=map(lambda x: re.sub(r"^[*|_]", "", x), df.columns)

    order = ["key", "comp_level", "set_number", "match_number",
             "predicted_time", "team_key", "surrogate", "alliance",
             "winning_alliance", "score", "time", "actual_time", "event_key"]
    if response == "full":
        order = (order + ["videos", "post_result_time"] +
                 list(jdata[0]["score_breakdown"]["blue"].keys()))
    return df[order]


def get_districts(session, team=None, year=None, mod_since=None,
                  only_mod_since=None):
    """
    Retrieves information on FIRST districts.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        mod_since:
            A string containing an HTTP formatted date and time.
            Causes function to return None if no changes have been
            made to the requested data since the date and time provided.
            Optional.
        only_mod_since:
            A string containing an HTTP formatted date and
            time. Causes function to only return data that has
            changed since the date and time provided. Optional.

    Returns:
        If session.data_format == "json" or "xml", returns a Python
        dictionary object containing the response text and additional
        metadata. If session.data_format == "dataframe", returns an instances
        of tbap.classes.http.FirstDf, which is a Pandas dataframe with
        an additional `attr` property that contains a Python dictionary
        with additional metadata.
    """
    if year is None and team is not None:
        http_args = ["team", team, "districts"]
    elif year is not None and team is None:
        http_args = ["districts", year]
    else:
        raise server.ArgumentError("Incorrect Arguments")
    return send_request(session, http_args, mod_since, only_mod_since)


def get_awards(session, event=None, team=None, year=None, mod_since=None,
               only_mod_since=None):
    if event is None and team is not None and year is not None:
        http_args = ["team", team, "awards", year]
    elif team is not None and event is None and year is None:
        http_args = ["team", team, "awards"]
    elif team is not None and event is not None and year is None:
        http_args = ["team", team, "event", event, "awards"]
    else:
        raise server.ArgumentError("Incorrect Arguments")
    return send_request(session, http_args, mod_since, only_mod_since)


def get_alliances(session, event, mod_since=None, only_mod_since=None):
    http_args = ["event", event, "alliances"]

    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])
    alli_dct = collections.OrderedDict()
    alli_dct["name"] = []
    alli_dct["team"] = []
    alli_dct["backup"] = []
    alli_dct["status"] = []
    alli_dct["declines"] = []
    alli_dct["level"] = []
    alli_dct["playoff_average"] = []
    alli_dct["current_level_wins"] = []
    alli_dct["current_level_losses"] = []
    alli_dct["current_level_ties"] = []
    alli_dct["overall_wins"] = []
    alli_dct["overall_losses"] = []
    alli_dct["overall_ties"] = []

    def append_rank_data(alliance, team):
        alli_dct["name"].append(alliance["name"])
        alli_dct["team"].append(team)
        if alliance["backup"] is not None:
            if alliance["backup"]["out"] == team:
                alli_dct["backup"].append("out")
            elif alliance["backup"]["in"] == team:
                alli_dct["backup"].append("in")
            else:
                alli_dct["backup"].append(False)
        else:
            alli_dct["backup"].append(False)
        alli_dct["status"].append(alliance["status"]["status"])
        alli_dct["declines"].append(str(alliance["declines"]))
        alli_dct["level"].append(alliance["status"]["level"])
        alli_dct["playoff_average"].append(
                alliance["status"]["playoff_average"])
        for stat in ["wins", "losses", "ties"]:
            alli_dct["current_level_" + stat].append(
                    alliance["status"]["current_level_record"][stat])
            alli_dct["overall_" + stat].append(
                    alliance["status"]["record"][stat])

    for alliance in jdata:
        for team in alliance["picks"]:
            append_rank_data(alliance, team)
        if alliance["backup"] is not None:
            append_rank_data(alliance, alliance["backup"]["in"])

    return pandas.DataFrame(alli_dct).set_index(["name", "team"])


def get_insights(session, event, mod_since=None, only_mod_since=None):
    http_args = ["event", event, "insights"]

    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])

    rows = []
    for lvl in jdata.keys():
        for key, val in jdata[lvl].items():
            if isinstance(val, list):
                row = {"level": lvl, "statistic": key}
                for idx in range(len(val)):
                    row["value_" + str(idx)] = val[idx]
                rows.append(row)
            else:
                rows.append({"level": lvl, "statistic": key, "value_0": val})

    return pandas.DataFrame(rows).set_index(["level", "statistic"])


def get_oprs(session, event, mod_since=None, only_mod_since=None):
    http_args = ["event", event, "oprs"]
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])
    col_names = ["team"] + list(jdata.keys())
    cols = collections.OrderedDict([(col, []) for col in col_names])
    for team in jdata["oprs"].keys():
        cols["team"].append(team)
        for col in jdata.keys():
            cols[col].append(jdata[col][team])

    return pandas.DataFrame(cols)


def get_predictions(session, event, mod_since=None, only_mod_since=None):
    http_args = ["event", event, "predictions"]
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])
    frames = {key: None for key in ["stats", "matches", "teams"]}

    # Match Prediction Stats
    rows = []
    for lvl in jdata["match_prediction_stats"].keys():
        for key, val in jdata["match_prediction_stats"][lvl].items():
            if isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    rows.append({"level": lvl, "statistic": key + "_" + sub_key,
                                 "value": sub_val})
            else:
                rows.append({"level": lvl, "statistic": key, "value": val})
    stats_frame = pandas.DataFrame(rows).set_index(["level", "statistic"])

    # Match Predictions
    rows = []
    jdata_predictions = jdata["match_predictions"]
    for lvl in jdata_predictions.keys():
        for match_key, match_data in jdata_predictions[lvl].items():
            for alliance in ["red", "blue"]:
                for stat_lbl, stat_val in match_data[alliance].items():
                    rows.append({"level": lvl, "match": match_key,
                                 "alliance": alliance, "statistic": stat_lbl,
                                 "value": stat_val})
            rows.append({"level": lvl, "match": match_key,
                         "statistic": "prob", "value": match_data["prob"]})
            rows.append({"level": lvl, "match": match_key,
                         "statistic": "winning_alliance",
                         "value": match_data["winning_alliance"]})

    prediction_frame = pandas.DataFrame(rows).set_index(["level", "match",
                                                         "alliance",
                                                         "statistic"])

    # Ranking Predictions
    jdata_ranks = jdata["ranking_predictions"]
    rows = []
    for team in jdata_ranks:
        rows.append({"team": team[0], "rank": team[1][0], "points": team[1][4]})
    rank_frame = pandas.DataFrame(rows).set_index("team")

    # Team Predictions
    jdata_teams = jdata["stat_mean_vars"]
    levels = list(jdata_teams.keys())
    stats = list(jdata_teams[levels[0]].keys())
    points = list(jdata_teams[levels[0]][stats[0]].keys())
    teams = list(jdata_teams[levels[0]][stats[0]][points[0]].keys())
    rows = []
    for team in teams:
        for lvl, lvl_data in jdata_teams.items():
            for stat, stat_data in lvl_data.items():
                for point, point_data in stat_data.items():
                    rows.append({"team": team, "level": lvl, "statistic": stat,
                                 "point": point, "value": point_data[team]})
    teams_frame = pandas.DataFrame(rows).set_index(["team", "statistic",
                                                    "point", "level"])

    return {"event_stats": stats_frame, "predictions": prediction_frame,
            "team_rankings": rank_frame, "team_stats": teams_frame}


def get_event_team_status(session, event, team, series=False, mod_since=None,
                          only_mod_since=None):
    http_args = ["team", team, "event", event, "status"]
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data
    jdata = json.loads(data["text"])
    if team is not None:
        sort_order = list(map(lambda x: x["name"],
                              jdata["qual"]["sort_order_info"]))
        sort_data = jdata["qual"]["ranking"]["sort_orders"]
        for idx, field in enumerate(sort_order):
            jdata["qual"]["ranking"][field] = sort_data[idx]
        del(jdata["qual"]["sort_order_info"])
        del(jdata["qual"]["ranking"]["sort_orders"])
        df = server.build_single_column_frame(jdata, series)
        return df
# TODO(stacy.irwin) Replace spaces in key names with underscores


def get_event_rankings(session, event, mod_since=None, only_mod_since=None):
    http_args = ["event", event, "rankings"]
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])
    sort_order = list(map(lambda x: x["name"], jdata["sort_order_info"]))
    extra_stats = list(map(lambda x: x["name"], jdata["extra_stats_info"]))
    rec_stat = ["wins", "losses", "ties"]
    rankings = jdata["rankings"]
    rows = []
    for rank in rankings:
        row = {}
        for key, val in rank.items():
            if not isinstance(val, dict) and not isinstance(val, list):
                row[key] = val
        for stat in rec_stat:
            row[stat] = rank["record"][stat]
        for idx in range(len(sort_order)):
            row[sort_order[idx]] = rank["sort_orders"][idx]
        for idx in range(len(extra_stats)):
            row[extra_stats[idx]] = rank["extra_stats"][idx]
        rows.append(row)

    df = pandas.DataFrame(rows).set_index(["rank"])
    df.columns = map(lambda x: re.sub("team_key", "team", x), df.columns)

    # Put columns in a logical order
    sorted_cols = ["team", "matches_played"] + extra_stats + sort_order + rec_stat
    other_cols = [col for col in df.columns if col not in sorted_cols ]
    return df[sorted_cols + other_cols]


def get_district_points(session, event, mod_since=None, only_mod_since=None):
    http_args = ["event", event, "district_points"]
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])

    # District Points
    df_points = pandas.read_json(json.dumps(jdata["points"]),
                                 orient="index")

    # Tiebreakers
    rows = []
    for team, tdata in jdata["tiebreakers"].items():
        idx = 1
        for score in tdata["highest_qual_scores"]:
            row = {"team": team, "highest_qual_score": score, "score_rank": idx}
            idx += 1
            row["qual_wins"] = tdata["qual_wins"]
            rows.append(row)

    df_high_scores = pandas.DataFrame(rows).set_index(["team"])

    return {"points": df_points, "high_scores": df_high_scores}

def get_media(session, team, year, mod_since=None, only_mod_since=None):
    http_args = ["team", team, "media", str(year)]
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])

    return pandas.io.json.json_normalize(jdata)

def get_social_media(session, team, mod_since=None, only_mod_since=None):
    http_args = ["team", team, "social_media"]
    data = server.send_http_request(session, http_args, mod_since,
                                    only_mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])

    return pandas.io.json.json_normalize(jdata)


# todo(stacy.irwin): Add username back to Session, pass as User-Agent header.
# noinspection PyAttributeOutsideInit
class Session:
    """Contains information required for every TBA Read API HTTP request.

    Every tbap method that retrieves data from the TBA Read API server
    requires a Session object as the first parameter. The Session
    object contains the TBA Read API username, authorization key, and
    competition season, as well as specifies the format of the returned
    data and whether the HTTP request should be sent to the production
    or staging TBA Read API servers.
    """
    # pylint: disable=too-many-instance-attributes

    TBA_URL = "https://www.thebluealliance.com/api/v3"
    TBA_API_VERSION = "v3.0"
    PACKAGE_VERSION = "0.9"
    USER_AGENT_NAME = "tbap: Version" + PACKAGE_VERSION

    def __init__(self, key, season=None, data_format="dataframe"):
        """Creates a ``Session`` object.

        Args:
            key: (str)
                The TBA Read API authorization key
            season: (int)
                A four digit year identifying the competition season
                for which data will be retrieved. Optional, defaults
                to the current calendar year.
            data_format:(str)
                Specifies the format of the data that will be returned
                by firstApiPY that submit HTTP requests. The allowed
                values are *dataframe* (Pandas dataframe) and *json*.
                Optional, defaults to *dataframe*.
        """

        self.key = key
        self.season = season
        self.data_format = data_format

    @property
    def key(self):
        """The account authorization key that is assigned by TBA Read API.

        *Type:* String

        """
        return self._key

    @key.setter
    def key(self, key):
        if not isinstance(key, str):
            raise TypeError("key must be a string.")
        else:
            self._key = key  # pylint: disable=W0201
            # pylint W0201: attribute-defined-outside-init

    @property
    def season(self):
        """ FRC competition season.

        Returns: Four-digit integer
        """
        return self._season

    @season.setter
    def season(self, season):
        """A four digit year identifying the competition season_summary.

        Args:
            season: A four digit year. Can be either an integer, a
                string, or None. If None, assigns the current year.

        Raises:
            ValueError if season_summary is prior to 2015 or later than
            current year + 1
        """
        if isinstance(season, str) and season.isnumeric():
            season = int(season)

        current_year = int(datetime.date.today().strftime("%Y"))
        if season is None:
            self._season = current_year  # pylint: disable=W0201
            # pylint W0201: attribute-defined-outside-init
        elif (season >= 2015) and (season <= current_year + 1):
            self._season = season  # pylint: disable=W0201
            # pylint W0201: attribute-defined-outside-init
        else:
            raise ValueError("season_summary must be >= 2015"
                             "and less than current year + 1.")

    @property
    def data_format(self):
        """String specifying format of output from tbap functions.

        *Type:* String

        *Raises:*
            * ``TypeError`` if set to type other than String.
            * ``ValueError`` if other than *dataframe*, *json*, or
              *xml*.
        """
        return self._data_format

    @data_format.setter
    def data_format(self, data_format):

        error_msg = ("The data_format property must be a string containing "
                     "'dataframe', 'json', or 'xml' "
                     "(case insensitive).")
        if not isinstance(data_format, str):
            raise TypeError(error_msg)
        elif data_format.lower() not in ["dataframe", "json", "xml"]:
            raise ValueError(error_msg)
        else:
            self._data_format = data_format.lower()  # pylint: disable=W0201
            # pylint W0201: attribute-defined-outside-init
