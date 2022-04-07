import math

# trade-off. bigger order brings faster access.
# , but there is also a growing chance correspondingly 
# that memory space will be wasted. (occupied but never used.)
# note, in this context, order is alias for page.
BNODE_ORDER = 64

# used for btree insertion
BNODE_MAX_CAPACITY = BNODE_ORDER - 1

# used for btree deletion
BNODE_MIN_CAPACITY = math.ceil(
    BNODE_ORDER / 2
) - 1
