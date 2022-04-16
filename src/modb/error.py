"modb.error brings custom exceptions."


class KeyNotFound(Exception):
    # delete or search will raise this
    pass


class DuplicateKeyFound(Exception):
    # insert or create will raise this
    # (racap again, create is a special insert
    # in my database implementation)
    pass

class ArrayIndexOutOfRange(Exception):
    # raised by Array.access method
    
    pass
