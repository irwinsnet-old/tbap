import json
import pandas


def build_single_column_frame(data, series=False):
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
        return pandas.Series(map(lambda x: x[1], s_list),
                             index=map(lambda x: x[0], s_list))
    else:
        return pandas.DataFrame(rows).set_index(["label"])