import io


class Base:
    @classmethod
    def load(cls, f):
        """
        continue reading f
        and parse it to instance of cls
        and return that instance
        """
        return NotImplemented

    def dump(self, f):
        """
        the inverse operation of load,
        writing the current bytes representation of self to f
        """
        return NotImplemented

    @classmethod
    def loads(cls, data: bytes):
        with io.BytesIO(data) as f:
            return cls.load(f)

    def dumps(self,):
        with io.BytesIO() as f:
            self.dump(f)
            f.seek(0)
            return f.read()


class PrimitiveTypeBase(Base):
    def __init__(
        self,
        n: int,
    ):
        self.n = n

    def dump(self, f):
        f.write(
            self.n.to_bytes(
                self.length,
                byteorder='big',
                signed=self.signed,
            )
        )

    @classmethod
    def load(cls, f):
        data = f.read(cls.length)
        n = int.from_bytes(
            data,
            byteorder='big',
            signed=cls.signed,
        )
        return cls(
            n,
        )

    def to_bytes(self):
        return self.n.to_bytes(
            self.length,
            byteorder='big',
        )


class U8(PrimitiveTypeBase):
    length = 1
    signed = False


class U16(PrimitiveTypeBase):
    length = 2
    signed = False


class U24(PrimitiveTypeBase):
    length = 3
    signed = False


class U32(PrimitiveTypeBase):
    length = 4
    signed = False
