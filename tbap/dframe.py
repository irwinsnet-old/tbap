import json
import re

import pandas
from pandas.io import json as pj


def build_single_column(data, series=False):
    jdata = json.loads(data) if isinstance(data, str) else data
    rows = []

    def append_scaler(key, val):
        key = re.sub(" ", "_", key)  # Replace spaces with underscores in keys.
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

    for top_key, top_val in jdata.items():
        append_scaler(top_key, top_val)

    if series:
        s_list = [(x["label"], x["value"]) for x in rows]
        return pandas.Series(map(lambda x: x[1], s_list),
                             index=map(lambda x: x[0], s_list))
    else:
        return pandas.DataFrame(rows).set_index(["label"])


def build_table(response):
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

    return dframe


def expand_column(dframe, col_name):
    def get_val(cell):
        return cell.get(key) if isinstance(cell, dict) else None

    if col_name in dframe:
        col_dframe = dframe.dropna(subset=[col_name])
        if col_dframe.shape[0] > 0:
            for key in col_dframe[col_name][0].keys():
                sub_col_name = col_name + "_" + key
                dframe[sub_col_name] = list(map(get_val, dframe[col_name]))
            dframe.drop(col_name, axis=1, inplace=True)
    return dframe


