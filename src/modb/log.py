import logging

# note, you can use following code in your project
# to change the default level for example
#
# import modb
# modb.log.logger.setLevel(logging.DEBUG)
#

# basic setting
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s|%(asctime)s|%(message)s',
)

# global logger used by `modb`
logger = logging.getLogger("modb_logger")
