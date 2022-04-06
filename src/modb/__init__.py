"""modb, on-disk-database, the replacement for open.
no third party dependency, using btree internally.

note, modb stands for My Own DataBase."""

# note,
# high and low means high-level and low-level api.
# it's worth mentioning that in modb.low
# , we have Database class too
# , but it just has more low-level api to call.
# we will just use modb.high.Database in default.

from modb.high import Database
from modb.low import Data