"""
The tbap package is designed to retrieve data from the Blue Alliance
Read API and format that tdata as _Pandas_ dataframes. _Pandas_
datagrames are a powerful tabular data structure that supports
sorting and filtering, as well as many advanced data analysis
techniques.

Users may also choose to have tbap functions provide data in the JSON
formate, which is the format provided by the Blue Alliance Read API.

License
=======

The tbap package uses the BSD-3 license. The full text is available
in the LICENSE file.

Copyright (c) 2017, Stacy Irwin

Pandas Package: Copyright (c) 2008-2012, AQR Capital Management,
LLC, Lambda Foundry, Inc. and PyData Development Team All rights
reserved.

Common Tbap Function Arguments
==============================

There are several function arguments that occur in multiple tbap
functions:

**session**
    An instance of ``tbap.api.Session`` that contains a valid
    username and authorization key. The ``Session`` object also a
    _data/_format_ property that can be set to "dataframe" (default) or
    "json". The _session_ argument is required for every function that
    sends an http request to the Blue Alliance Read API server.
**year**
    Either a string or an integer. The year argument specifies the FRC
    season as a four-digit year. Use the current year to obtain data on
    the current FRC season, or past years to get data on prior seasons.
    This argument can be either optional or required.
**event**
    A string containing a TBA Read API event key. The event key
    contains both the competition year and an abbreviation
    representing the event, which TBA calls an event code. For
    example, "2017pnw" is the event key for the 2017 Pacific
    Northwest district championships. An event key is requried
    because many tbap functions return information on just a single
    event.
**response**
    A string containing either "full" (default), "simple", or "keys".
    If set to "simple", the function returns fewer columns of data. If
    set to "keys", the function returns a single column of team key
    values, e.g., "frc1318". If set to "full", the function will return
    all columns of data that are available. This argument is always
    optional.
**mod_since**
    A string containing an HTTP formatted date and time. This argument
    is always optional. If specified, the Blue Alliance Read API
    server will compare the date and time in the mod_since argument
    to the date and time that the data was last updated on the Read
    API server. If the data has not been updated since *mod_since*, the
    Read API server will return no data and http code 304. Tbap
    functions will return a Python dictionary object (regardless of
    the value of the Session.data_format property) with code 304 and
    no content. Users are encoraged to record the date and time
    returned in the "Last-Modified" attribute and provide that value
    in the mod_since attribute on subsequent requests for the same
    data to reduce load on the Read API server.

Tbap Function Return Values
===========================


"""
import collections
import datetime
import json
import re
import warnings

import numpy
import pandas.io.json
import pandas

import tbap.server as server
import tbap.dframe as dframe


def get_status(session):
    """ Gets the status of the Blue Alliance Read API server.

    Args:
        session: (api.Session)
            An object created with the api.Session() constructor.
    Returns:
        Either a pandas.Dataframe object or a Python dictionary object.
    """
    http_args = ["status"]
    return send_request(session, http_args, "single_column")


def get_districts(session, year=None, team=None, mod_since=None):
    """
    Retrieves information on FIRST districts.

    Args:
        session:
            An object created with the api.Session() constructor.
        year (int or str):
            The four digit year specifying the FRC season. Optional.
        team (str):
            FRC team number in format *frcNNNN*, e.g., "frc1318".
        mod_since:
            A string containing an HTTP formatted date and time.
            Optional.

    Returns:
        Either a pandas.Dataframe object or a Python dictionary object.
    """
    if year is None and team is not None:
        http_args = ["team", team, "districts"]
    elif year is not None and team is None:
        http_args = ["districts", year]
    else:
        raise server.ArgumentError("Incorrect Arguments")
    return send_request(session, http_args, "table", mod_since)


def get_teams(session,  # pylint: disable=too-many-arguments
              page=None, year=None, event=None, district=None,
              response="full", mod_since=None):
    """Retrieves FRC teams from the TBA Read API Server.

    Args:
        session (tbap.api.Session):
            An instance of tbap.api.Session that contains
            a valid username and authorization key.
        page (int):
            get_teams() splits response data into several different
            pages, each page containing a block of 1000 teams. The
            page attribute specifies which page of teams to return.
            Optional.
        year (int or str):
            Specifies for which year to return team data. Optional.
        event (str):
            A string containing the TBA Read API event code. If
            included, function will return only teams that are
            competing in that event. Use tbap.api.get_events to lookup
            event codes. Optional.
        district (str):
            A string containing the TBA Read API district code. If
            included, function will only return teams that are
            competing in that event. Optional.
        response (str):
            Either "full" (default), "simple", or "keys". Optional.
        mod_since:
            A string containing an HTTP formatted date and time.
            Optional.

    Returns:
        A pandas.Dataframe object or a Python dictionary object.

    Raises:
        tbap.Classes.ArgumentError:
            For the *page*, *year*, *event*, and *district* arguments,
            *year* can only be specified if *page* is also specified.
            Otherwise, one and only one of these four arguments can be
            specified, or `get_teams()` raises an ArugumentError.
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
    results = send_request(session, http_args, "table", mod_since)
    if response == "keys":
        results.columns = ["team"]
    return results


def get_team(session, team, response="full", mod_since=None):
    """Retrieves information about a single FRC team.

    Args:
        session (tbap.api.Session):
            An instance of tbap.api.Session that contains
            a valid username and authorization key.
        team (str):
            FRC team number in format *frcNNNN*, e.g., "frc1318".
        response (str):
            Either "full" (default), "simple", "years_participated", or
            "robots". Optional.
        mod_since:
            A string containing an HTTP formatted date and time.
            Optional.

    Returns:
        A pandas.Dataframe object or a Python dictionary object.
    """
    http_args = ["team", team]
    if response.lower() in ["simple", "years_participated", "robots"]:
        http_args.append(response.lower())
    results = send_request(session, http_args, "table", mod_since)
    if response == "years_participated":
        results.columns = ["year"]
    return results


def get_events(session,  # pylint: disable=too-many-arguments
               year=None, district=None, team=None, event=None, response="full",
               mod_since=None):
    """Retrieves information on one or more FRC competitions.

    Args:
        session (tbap.api.Session):
            An instance of tbap.api.Session that contains
            a valid username and authorization key.
        year (int or str):
            Specifies for which year to return team data. Optional.
        district (str):
            A string containing the TBA Read API district code. If
            included, function will only return teams that are
            competing in that event. Optional.
        team (str):
            The four digit FRC team number as an integer.
        event (str):
            A key value specifying the competition year and event.
        response (str):
            Either "full" (default), "simple", or "keys". Optional.
        mod_since (str):
            A string containing an HTTP formatted date and time.
            Optional.

    Returns:
        A pandas.Dataframe object or a Python dictionary object.

    Raises:
        tbap.Classes.ArgumentError:
            For the *team*, *year*, *event*, and *district* arguments,
            *year* can only be specified if *team* is also specified.
            Otherwise, one and only one of these four arguments can be
            specified, or `get_teams()` raises an ArugumentError.
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
    results = send_request(session, http_args, "table", mod_since)
    if response == "keys":
        results.columns = ["key"]
    return results


def get_matches(session, event=None, team=None, year=None, match=None,
                response="full", mod_since=None):
    """Returns detailed information on competition matches.

    The allowed combinations of optional arguments are *event*,
    *team* and *event*, *team* and *year*, and *match*. This function
    will raise an error if any other combinations of arguments are
    provided.

    Args:
        session (tbap.api.Session):
            An instance of tbap.api.Session that contains
            a valid username and authorization key.
        event (str):
            A key value specifying the competition year and event.
        team (str):
            The four digit FRC team number as an integer.
        year (int or str):
            Specifies for which year to return team http_data. Optional.
        match (str):
            The key value for the desired match. The key value has the
            format "YYYY{EventCode}_{CompetitionLevel}NNN" where YYYY
            is the four digit year and NN is the match number with no
            leading zeros. For example, *2017wasno_qm79* is the 79th
            qualification match at the 2017 district competition at
            Glacier Peak High School in Snohomish, WA.
        response (str):
            Either "full" (default), "simple", or "keys". Optional.
        mod_since (str):
            A string containing an HTTP formatted date and time.
            Optional.

    Returns:
        A pandas.Dataframe object or a Python dictionary object.

    Raises:
        tbap.Classes.ArgumentError: If any unallowed combinations of
        arguments are provided to the function.

    """
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
    http_data = server.send_http_request(session, http_args, mod_since)
    if session.data_format != "dataframe":
        return http_data

    if response.lower() == "keys":
        df = server.build_frame(http_data)
        df.columns = ["key"]
        return server.attach_attributes(df, http_data)

    # Convert nested JSON text into a flat dataframe
    jdata = json.loads(http_data["text"])
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

    def append_match_data(mtch, team_key, alliance, surrogate):
        # Skip appending if no score has been reported for match.
        if mtch["score_breakdown"] is None:
            warnings.warn("No score data for match {}.".format(mtch["key"]))
            return

        for key in flat_match.keys():
            if key[0:1] not in ["_", "*"]:
                flat_match[key].append(mtch[key])
            elif key[0:1] == "*":
                flat_match[key].append(
                    mtch["score_breakdown"][alliance][key[1:]])
        flat_match["_team_key"].append(team_key)
        flat_match["_alliance"].append(alliance)
        flat_match["_surrogate"].append(surrogate)
        if "_videos" in flat_match:
            flat_match["_videos"].append(str(mtch["videos"]))
        flat_match["_score"].append(mtch["alliances"][alliance]["score"])

    for indv_match in jdata:
        for team in indv_match["alliances"]["blue"]["team_keys"]:
            append_match_data(indv_match, team, "blue", False)
        for team in indv_match["alliances"]["blue"]["surrogate_team_keys"]:
            append_match_data(indv_match, team, "blue", True)
        for team in indv_match["alliances"]["red"]["team_keys"]:
            append_match_data(indv_match, team, "red", False)
        for team in indv_match["alliances"]["red"]["surrogate_team_keys"]:
            append_match_data(indv_match, team, "red", True)

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
    return server.attach_attributes(df[order], http_data)


def get_rankings(session, district, mod_since=None):
    """Retrieves the team rankings based on the qualification rounds.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        event:
            A key value specifying the competition year and event.
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

    Returns:

    """
    http_args = ["district", district, "rankings"]
    return send_request(session, http_args, mod_since)


def get_awards(session, event=None, team=None, year=None, mod_since=None):
    if event is None and team is not None and year is not None:
        http_args = ["team", team, "awards", year]
    elif team is not None and event is None and year is None:
        http_args = ["team", team, "awards"]
    elif team is not None and event is not None and year is None:
        http_args = ["team", team, "event", event, "awards"]
    else:
        raise server.ArgumentError("Incorrect Arguments")
    return send_request(session, http_args, mod_since)


def get_alliances(session, event, mod_since=None):
    http_args = ["event", event, "alliances"]

    data = server.send_http_request(session, http_args, mod_since)
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


def get_insights(session, event, mod_since=None):
    http_args = ["event", event, "insights"]

    data = server.send_http_request(session, http_args, mod_since)
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


def get_oprs(session, event, mod_since=None):
    http_args = ["event", event, "oprs"]
    data = server.send_http_request(session, http_args, mod_since)
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


def get_predictions(session, event, mod_since=None):
    http_args = ["event", event, "predictions"]
    data = server.send_http_request(session, http_args, mod_since)
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


def get_event_team_status(session, event, team, series=False, mod_since=None):
    http_args = ["team", team, "event", event, "status"]
    data = server.send_http_request(session, http_args, mod_since)
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


def get_event_rankings(session, event, mod_since=None):
    http_args = ["event", event, "rankings"]
    data = server.send_http_request(session, http_args, mod_since)
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


def get_district_points(session, event, mod_since=None):
    http_args = ["event", event, "district_points"]
    data = server.send_http_request(session, http_args, mod_since)
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


def get_media(session, team, year, mod_since=None):
    http_args = ["team", team, "media", str(year)]
    data = server.send_http_request(session, http_args, mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])

    return pandas.io.json.json_normalize(jdata)


def get_social_media(session, team, mod_since=None):
    http_args = ["team", team, "social_media"]
    data = server.send_http_request(session, http_args, mod_since)
    if session.data_format != "dataframe":
        return data

    jdata = json.loads(data["text"])

    return pandas.io.json.json_normalize(jdata)


def send_request(session, http_args, normalize, mod_since=None):
    """Routes data request to correct internal functions.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        http_args:
            A Python list of parameters that will be added to the http
            request.
        normalize (str):
            Specifies which alorithm will be used to convert and
            normalize the JSON data into a pandas dataframe.
        mod_since:
            A string containing an HTTP formatted date and time.
            Causes function to return None if no changes have been
            made to the requested data since the date and time provided.
            Optional.

    Returns:
        Either a pandas.Dataframe object (if session.data_format =
        "dataframe") or a Python dictionary.

    """
    response = server.send_http_request(session, http_args, mod_since)
    if session.data_format != "dataframe" or response["code"] == 304:
        return response
    else:
        if normalize == "table":
            frame = server.build_frame(response)
        elif normalize == "single_column":
            frame = dframe.build_single_column_frame(response["text"])
    return server.attach_attributes(frame, response)


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

    def __init__(self, username, key, data_format="dataframe"):
        """Creates a ``Session`` object.

        Args:
            username: (str)
                TBA Read API username
            key: (str)
                TBA Read API authorization key
            data_format:(str)
                Specifies the format of the data that will be returned
                by firstApiPY that submit HTTP requests. The allowed
                values are *dataframe* (Pandas dataframe) and *json*.
                Optional, defaults to *dataframe*.
        """

        self.username = username
        self.key = key
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
    def username(self):
        """The account authorization key that is assigned by TBA Read API.

        *Type:* String

        """
        return self._username

    @username.setter
    def username(self, username):
        if not isinstance(username, str):
            raise TypeError("username must be a string.")
        else:
            self._username = username  # pylint: disable=W0201
            # pylint W0201: attribute-defined-outside-init

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
                     "'dataframe' or 'json' (case insensitive).")
        if not isinstance(data_format, str):
            raise TypeError(error_msg)
        elif data_format.lower() not in ["dataframe", "json"]:
            raise ValueError(error_msg)
        else:
            self._data_format = data_format.lower()  # pylint: disable=W0201
            # pylint W0201: attribute-defined-outside-init
