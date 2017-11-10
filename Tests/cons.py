import tbap.api as api
import tbap.server as server

key = "6Sx6a2gOyNWwNNTAd9UYBOpWp7MxaNrZgO4CqConwJwwDooKQV3DbZXvnk8TBL7A"


def chk_insights():
    sn = api.Session(key)
    insights = api.get_predictions(sn, "2017pncmp")
    return insights

insights = chk_insights()