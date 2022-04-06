
# local imports
from modb.formatcore import *
from modb.format import *


def make_header(root_node_ptr):
    return Header(
        signature=Signature('BTR'),
        btree_order=U16(BNODE_ORDER),
        root_node=Pointer(root_node_ptr),
    )
