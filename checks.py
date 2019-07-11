import auth
import tbap.api as api

sn = api.Session(auth.username, auth.key)
dist = api.get_districts(sn, 2019)
print(dist)
