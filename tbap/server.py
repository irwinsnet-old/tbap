"""Internal functions for sending http requests or retrieving cached
data.

License:
    GNU General Public License v3.0

Version:
    0.0.1

Copyright 2017, Stacy Irwin
"""
import datetime
import json
import os
import os.path
import pickle
import urllib.request
import urllib.error
import base64
import warnings

import pandas
from pandas.io import json as pj

#todo(stacy.irwin): accept integer arguments for team numbers, start, end, etc.
#todo(stacy.irwin): Rewrite build_url so it doesn't know about season or status.
#todo(stacy.irwin): Take advantage Json_normalize -- will expand dict fields if record_path = None


def build_tba_url(session, http_args):
    url = session.TBA_URL
    for arg in http_args:
        url += "/" + str(arg)
    return url


def httpdate_to_datetime(http_date, gmt=True):
    """Converts a HTTP datetime string to a Python datetime object.

    Args:
        http_date: A string formatted as an HTTP date and time.
        gmt: If True, sets timezone of resulting datetime object to
            GMT. Otherwise datetime object is timezone unaware.
            Optional, default is True.

    Returns: A Python datetime object that is timezone aware, set to
        the GMT time zone. Returns False if the http_date argument is
        not a valid HTTP date.

    Raises:
        UserWarning if the http_date argument is not a valid HTTP date
        and time.
    """
    try:
        if gmt:
            dtm = datetime.datetime.strptime(http_date,
                                             "%a, %d %b %Y %H:%M:%S %Z")
        else:
            dtm = datetime.datetime.strptime(http_date,
                                             "%a, %d %b %Y %H:%M:%S")
    except ValueError:
        warn_msg = ("Incorrect date-time format passed as argument. "
                    "Argument has been ignored."
                    "Use HTTP format ('ddd, MMM dd YYYY HH:MM:SS ZZZ') where "
                    "ddd is 3-letter abbreviation for weekday and ZZZ is "
                    "3-digit abbreviaion for time zone.")
        warnings.warn(warn_msg, UserWarning)
        return False
    else:
        if gmt:
            dtm = dtm.replace(
                tzinfo=datetime.timezone(datetime.timedelta(hours=0), "GMT"))
        return dtm


def datetime_to_httpdate(date_time, gmt=True):
    """Converts a Python datetime object to an HTTP datetime string.

    Args:
        date_time: A Python datetime object.
        gmt: If true, http date string will indicate time is in GMT
            timezone. Optional, default value is True.

    Returns: A string formatted as an HTTP datetime, using the GMT
        timezone.
    """
    if gmt:
        tzone_gmt = datetime.timezone(datetime.timedelta(hours=0), "GMT")
        date_time = date_time.replace(tzinfo=tzone_gmt)
        fmt_string = "%a, %d %b %Y %H:%M:%S %Z"
    else:
        fmt_string = "%a, %d %b %Y %H:%M:%S"
    return datetime.datetime.strftime(date_time, fmt_string)


def httpdate_addsec(http_date, gmt=True):
    """Adds one second to an HTTP datetime string.

    Args:
        http_date: An HTTP datetime string.
        gmt: If true, timezone of resulting datetime object will be set
            to GMT. Optional, default is True.

    Returns:
        An HTTP datetime string that is one second later than the
        string passed in the http_date argument.

    Raises:
        ValueError if http_date is not a vallid HTTP datetime string.
    """
    dtm = httpdate_to_datetime(http_date, gmt)
    if dtm:
        dtm_new = dtm + datetime.timedelta(seconds=1)
    else:
        raise ValueError("http_date argument is not a valid HTTP datetime"
                         "string.")
    return datetime_to_httpdate(dtm_new, gmt)


def send_http_request(session, args, mod_since=None, only_mod_since=None):
    url = session.TBA_URL
    for arg in args:
        url += "/" + str(arg)

    hdrs = {"X-TBA-Auth-Key": session.key,
            "X-TBA-App-Id": "stacy_irwin:Tbap-Python-Package:0.9",
            "User-Agent": "stacy_irwin:Tbap-Python-Package:0.9"}
    req = urllib.request.Request(url, headers=hdrs)
    data = {}
    try:
        with urllib.request.urlopen(req) as resp:
            data["code"] = resp.getcode()
            data["text"] = resp.read().decode("utf-8")
            data["url"] = resp.geturl()
            data["args"] = args
            for key, value in resp.info().items():
                data[key] = value
    except urllib.error.URLError as err:
        print(err)
    except:
        print("Some other error.")
    return data


def build_single_column_frame(data, response, series=False):
    jdata = json.loads(data) if isinstance(data, str) else data
    rows = []

    def append_scaler(key, val):
        if isinstance(val, dict):
            if not val:
                rows.append({"label": key, "value": None})
            else:
                for subkey, subval in val.items():
                    append_scaler(key + "_" + subkey, subval)
        elif isinstance(val, list):
            if not val:
                rows.append({"label": key, "value": None})
            else:
                for idx, item in enumerate(val):
                    append_scaler(key + "_" + str(idx), item)
        else:
            rows.append({"label": key, "value": val})

    for jkey, jval in jdata.items():
        append_scaler(jkey, jval)

    if series:
        s_list = [(x["label"], x["value"]) for x in rows]
        dframe = pandas.Series(map(lambda x: x[1], s_list),
                               index=map(lambda x: x[0], s_list))
    else:
        dframe =  pandas.DataFrame(rows).set_index(["label"])

    return attach_attributes(dframe, response)


def send_http_request_old(session, url, cmd, mod_since=None, only_mod_since=None):
    """Sends http request to FIRST API server and returns response.

    send_http_request() is an internal function that is not intended to
    be called by the user. In addition to sending the http request,
    send_http_request() converts the JSON-formatted response text into
    a Pandas dataframe.

    Args:
        session:
            An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        url:
            A string containing the url that will be sent to the
            FIRST API server.
        cmd:
            A string specifying the FIRST API command.
        mod_since:
            A string containing an HTTP formatted date and time.
            Causes send_http_request() to return None if no changes have been
            made to the requested data since the date and time provided.
            Optional.
        only_mod_since:
            A string containing an HTTP formatted date and
            time. Causes send_http_request() to only return data that has
            changed since the date and time provided. Optional.

    Returns:
        If session.data_format == "dataframe", returns an instances of
        tbap.classes.FirstDF, which is a Pandas dataframe with
        an `attr` property. The `attr` property is a Python dictionary
        with the keys listed below.
        If session.data_format == "schedule.json" or "xml", returns a Python
        dictionary object with the xml or json text accessible via the "text"
        attribute.

    """

    # Check arguments
    if(mod_since is not None) and (only_mod_since is not None):
        raise ArgumentError("Cannot specify both mod_since and "
                            "only_mod_since arguments.")

    # Create authorization and format headers
    raw_token = session.username + ":" + session.key
    token = "Basic " + base64.b64encode(raw_token.encode()).decode()

    data = {}
    if session.data_format == "xml":
        format_header = "application/xml"
        data["text_format"] = "xml"
    else:
        format_header = "application/schedule.json"
        data["text_format"] = "json"

    hdrs = {"Accept": format_header, "Authorization": token}
    if mod_since is not None and httpdate_to_datetime(mod_since, True):
        hdrs["If-Modified-Since"] = mod_since
    if only_mod_since is not None and httpdate_to_datetime(only_mod_since):
        hdrs["FMS-OnlyModifiedSince"] = only_mod_since

    # Submit HTTP request
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req) as resp:
            data["code"] = resp.getcode()
            data["text"] = resp.read().decode("utf-8")
            data["url"] = resp.geturl()
            for key, value in resp.info().items():
                data[key] = value
    except urllib.error.HTTPError as err:
        # FIRST API returns 304 if data has not been modified since
        if err.code == 304:
            data["code"] = 304
            data["text"] = None
            data["url"] = url
        else:
            raise

    data["time_downloaded"] = datetime_to_httpdate(datetime.datetime.now(),
                                                   False)
    data["local_data"] = False
    data["local_time"] = None
    data["requested_url"] = data["url"]
    data["frame_type"] = cmd
    data["mod_since"] = mod_since
    data["only_mod_since"] = only_mod_since
    return data


def send_local_request(session, url, cmd):
    """Retrieves a FIRSTResponse object from a local data cache.

    Args:
        session: An instance of tbap.classes.Session that contains
            a valid username and authorization key.
        url: A string containing the url containing all FIRST API
            parameters.
        cmd: A string specifying the FIRST API command.

    Returns: A Response object.
    """

    # Determine API command from URL
    if session.data_format.lower() == "xml":
        filename = cmd + "_xml.pickle"
    else:
        filename = cmd + "_json.pickle"

    os.chdir(
        "C:/Users/stacy/OneDrive/Projects/FIRST_API/tbap/data")
    with open(filename, 'rb') as file:
        local_data = pickle.load(file)

    local_time = datetime_to_httpdate(datetime.datetime.now(), False)
    local_data["local_data"] = True
    local_data["local_time"] = local_time
    local_data["requested_url"] = url
    return local_data


class ArgumentError(Exception):
    """Raised when there are incorrect combinations of arguments.
    """
    pass


class JsonParseError(Exception):
    pass


def build_frame(response):
    jtxt = response["text"]
    jdata = json.loads(jtxt)
    scaler_cols = []
    dict_cols = []
    list_cols = []

    # Pandas functions throw error if json is single dict object.
    if isinstance(jdata, dict):
        jdata = [jdata]
        jtxt = "[" + jtxt + "]"

    if isinstance(jdata[0], dict):
        for key, var in jdata[0].items():
            if isinstance(var, dict):
                dict_cols.append(key)
            elif isinstance(var, list):
                list_cols.append(key)
            else:
                scaler_cols.append(key)

    if len(list_cols) == 1:
        dframe = pj.json_normalize(jdata, record_path=list_cols,
                                   meta=scaler_cols)
    elif len(dict_cols) > 0:
        dframe = pj.json_normalize(jdata)
        for val in dict_cols:
            if val in dframe.columns:
                dframe.drop(val, axis=1, inplace=True)
    elif not scaler_cols and not list_cols:
        dframe = pandas.read_json(jtxt)
    else:
        dframe = pandas.read_json(jtxt, orient="records")

    return attach_attributes(dframe, response)


def attach_attributes(dframe, response):
    dframe.attr = {}
    for key, val in response.items():
        if key != "text":
            dframe.attr[key] = val
    return dframe


class Dframe(pandas.DataFrame):
    """A subclass of pandas.Dataframe with FIRST API metadata attributes.

    Attributes:
        attr: A python Dictionary that contains FIRST API metatadata,
             such as the URL used to download the data and the time
             downloaded.
        frame_type: A string, such as "teams" or "events", that denotes
             the FIRST API command used to download the data, as well
             as the format of the dataframe.
        build: A method that takes a tbap.response object and returns a
            tbap.Dframe.
    """

    # Required because pandas overrides __getattribute__().
    # See http://pandas.pydata.org/pandas-docs/stable/internals.html
    # #subclassing-pandas-data-structures
    metadata = ["attr", "frame_type"]

    def __init__(self, response):
        """

        Args:
            response: (tbap.Response) The data that will be
                converted to a tbap.DFrame
            record_path: (string) The JSON name that identifies the
                list of objects that will be converted to dataframe
                rows.
            meta: (List of Strings) A list of JSON names that identify
                JSON values that will be added to each dataframe row.
        """

        # Accept dataframe for pandas.concat function ==========================
        if not isinstance(response, dict):
            super().__init__(response)
            self._attr = None
            return

        # Create empty dataframe if no data returned due to no recent ==========
        # changes to FIRST data
        if response["code"] == 304 and response["text"] is None:
            if response["mod_since"] is not None:
                frame_data = {"If-Modified-Since": response["mod_since"]}
            else:
                assert response["only_mod_since"] is not None
                frame_data = {"FMS-OnlyModifiedSince":
                              response["only_mod_since"]}
            super().__init__(frame_data, [0])
            self._attr = response
            return

        # Convert json text to dataframe =======================================
        json_data = json.loads(response["text"])
        record_path = list()
        meta = list()
        # json_normalize function below will error if json_data
        #   consists of a dict with a single item that is a list. So in
        #   this case, extract list and make it top-level item in
        #   json_data.
        if len(json_data.keys()) == 1:
            json_data = json_data[list(json_data.keys())[0]]
            if not isinstance(json_data, list):
                msg = ("Incorrect JSON format: When JSON consists of a "
                       "dict with a single key, dict value must be a list.")
                raise json.JSONDecodeError(msg, doc=response["data_format"],
                                           pos=0)

        # json_normalize function below requires identifying all keys
        #   in JSON data that themselves contain lists and passing this
        #   data as a list to the record_path argument. Other non-list
        #   keys must be passed as a lit via the meta argument. This
        #   enables json_normalize to flatten the data into a
        #   dataframe.
        if isinstance(json_data, dict):
            items = json_data.items()
        else:  # If not a dict, json_data must be a list of dicts.
            items = json_data[0].items()
        list_keys = map(lambda x: x[0] if isinstance(x[1], list) else False,
                        items)
        record_path = list(filter(lambda x: x, list_keys))
        othr_keys = map(lambda x: x[0] if not isinstance(x[1], list) else False,
                        items)
        meta = list(filter(lambda x: x, othr_keys))

        if not record_path:
            # json_normalize will not accept json consisting of a
            #   single dict with no nested lists.
            if isinstance(json_data, list):
                dframe = pandas.read_json(json.dumps(json_data),
                                          orient="records", typ="frame")
                super().__init__(dframe)
            else:
                super().__init__(pandas.read_json("[" + response["text"] + "]",
                                                  orient="records",
                                                  typ="frame"))
        else:
            super().__init__(pj.json_normalize(json_data,
                                               record_path=record_path,
                                               meta=meta))
        self._attr = response

    @property
    def _constructor(self):
        """
        Ensures pandas functions return FirstDf instead of Dataframe.

        See http://pandas.pydata.org/pandas-docs/stable/internals.html
        #subclassing-pandas-data-structures

        Returns: FirstDf
        """
        return Dframe

    @property
    def attr(self):
        """Contains FIRST API metadata attributes.

        Examples of metadata attributes includes the time the data was
        downloaded from the FIRST API server, the url used to download
        the data, etc.

        Returns: A Python dictionary.
        """
        return self._attr

    @attr.setter
    def attr(self, attr):
        self._attr = attr
