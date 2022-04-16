import struct
from typing import List

# local imports
from modb.formatcore import *
from modb.constant import *
from modb.util import fill

# alias
Pointer = U64


class Array(Base):
    def __init__(
        self,
        # container size (2**power)
        power: U8,
        # the number of elements
        length: U32,
        start: Pointer,
    ):
        self.power = power
        self.length = length
        self.start = start

    @classmethod
    def load(cls, f):
        return cls(
            power=U8.load(f),
            length=U32.load(f),
            start=Pointer.load(f),
        )

    def dump(self, f):
        self.power.dump(f)
        self.length.dump(f)
        self.start.dump(f)


class Bytes(Base):
    def __init__(self, b: bytes):
        self.b = b

    @classmethod
    def load(cls, f):
        data_length = U32.load(f).n

        return cls(
            b=f.read(data_length),
        )

    def dump(self, f):
        data_length = len(self.b)
        U32(data_length).dump(f)

        f.write(self.b)


class Boolean(Base):
    def __init__(self, value: bool):
        self.value = value

    @classmethod
    def load(cls, f):
        if U8.load(f).n == 1:
            value = True
        else:
            value = False

        return cls(
            value=value,
        )

    def dump(self, f):
        if self.value is True:
            U8(1).dump(f)
        else:
            U8(0).dump(f)


class Empty(Base):
    # this type do nothing
    # , the type-code already indicates that is a None

    @classmethod
    def load(cls, f):
        return cls()

    def dump(self, f):
        pass


class Tree(Base):
    def __init__(self, root_node: Pointer):
        self.root_node = root_node

    @classmethod
    def load(cls, f):
        return cls(
            root_node=Pointer.load(f),
        )

    def dump(self, f):
        self.root_node.dump(f)


class Number(Base):
    def __init__(
        self,
        n: int,
    ):
        self.n = n

    @classmethod
    def load(cls, f):
        n = struct.unpack('>f', f.read(4))[0]

        return cls(
            n=n,
        )

    def dump(self, f):
        f.write(
            struct.pack('>f', self.n)
        )


class String(Base):
    def __init__(
        self,
        s: str,
    ):
        self.s = s

    @classmethod
    def load(cls, f):
        u32 = U32.load(f)
        data_length = u32.n
        s = f.read(data_length)
        return cls(
            s=s.decode('utf-8'),
        )

    def dump(self, f):
        data = self.s.encode('utf-8')
        data_length = len(data)

        U32(data_length).dump(f)
        f.write(
            data
        )


class BNodeFormat(Base):
    order = BNODE_ORDER
    capacity = order - 1

    def __init__(
        self,
        keys: List[Pointer],
        values: List[Pointer],
        children: List[Pointer],
    ):

        p = Pointer(0)
        self.keys = fill(keys, self.capacity, p)
        self.values = fill(values, self.capacity, p)
        self.children = fill(children, self.order, p)

        # note:
        # key pointer -> data (like number or string), used to compare
        # value pointer -> data (like number or string)
        # child pointer -> BNodeFormat

    @classmethod
    def load(cls, f):

        keys = [
            Pointer.load(f)
            for _ in range(cls.capacity)
        ]
        values = [
            Pointer.load(f)
            for _ in range(cls.capacity)
        ]
        children = [
            Pointer.load(f)
            for _ in range(cls.order)
        ]

        inst = cls(
            keys=keys,
            values=values,
            children=children,
        )

        return inst

    def dump(self, f):
        for i in self.keys:
            i.dump(f)

        for i in self.values:
            i.dump(f)

        for i in self.children:
            i.dump(f)


class Signature(Base):
    def __init__(
        self,
        name: str,
    ):
        self.name = name

    @classmethod
    def load(cls, f):
        name = ''
        for _ in range(3):
            c = U8.load(f).to_bytes().decode()
            name += c

        return cls(
            name=name,
        )

    def dump(self, f):
        for c in self.name:
            f.write(c.encode())


class Header(Base):
    def __init__(
        self,
        signature: Signature,
        btree_order: U16,
        root_node: Pointer,
    ):
        self.signature = signature
        self.btree_order = btree_order
        self.root_node = root_node

    @classmethod
    def load(cls, f):
        return cls(
            signature=Signature.load(f),
            btree_order=U16.load(f),
            root_node=Pointer.load(f),
        )

    def dump(self, f):
        self.signature.dump(f)
        self.btree_order.dump(f)
        self.root_node.dump(f)


if __name__ == '__main__':
    b = BNodeFormat(
        keys=[
            Pointer(10001),
        ],
        values=[
            Pointer(10002),
        ],
        children=[
            Pointer(10003),
        ],
    )

    header = Header(
        signature=Signature('BTR'),
        btree_order=U16(10),
        root_node=Pointer(10009),
    )
    print(
        len(b.dumps()),
    )
    print(
        len(header.dumps()),
    )

    print('Done.')


def make_header(root_node_ptr):
    return Header(
        signature=Signature('BTR'),
        btree_order=U16(BNODE_ORDER),
        root_node=Pointer(root_node_ptr),
    )
