"""high-level api."""

# note, if you want some educational comment
# , go and see low.py


# local imports
from modb import low


class Database:
    # most-high-level api, which wrap the core DataBase.

    # go and check low.Database for more information

    def __init__(self, filename, read_only=False):
        self.filename = filename
        self.read_only = read_only

        self.db = low.Database(
            filename=self.filename,
            read_only=self.read_only,
        )

    def connect(self) -> low.VirtualBNode:
        return self.db.connect()

    def close(self):
        # close the database file

        self.db.close()


if __name__ == '__main__':
    import os

    filename = "./db.modb"

    db = Database(filename)
    node = db.connect()

    try:

        node.insert(
            key="hello",
            value="world",
        )

        resp = node.search(
            key="hello",
        )

        value = resp.get()
        print(
            "value:", value,
        )

    finally:
        db.close()
        os.remove(filename)
