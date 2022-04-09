"""low-level api, the most core part."""


import bisect
import mmap
import os
import io
import logging
from datetime import datetime

# 3rd imports
# for my own testing purposes
# from tqdm import tqdm

# local imports
from modb import utils
from modb import error
from modb.format import *
from modb.log import logger


# note, in this source code, when I say `position` or `pointer`, they are
# the same thing, which is the absolute location of the data in the database
# file. the variable name often has `_p` suffix to indicate that is a pointer
# , which is just a int type variable. note, there IS a Pointer(or U32) class
# , that kind of class is just a helper class for us to easily load-and-dump
# some fixed pattern from-and-to the disk.

# note, in this source code, when I say `index` or `bnode`, they most of the
# time are the same thing, that is to say, we use btree as our index structure


# rough layout of the this on-disk-database file format:
#       Header:
#           root btree-node pointer
#       then:                                (main part)
#           ( btree-node | data )+
# note, `+` means repeat previous thing arbitrary times
# , in this case, previous thing is (btree-node OR data)
# , for example, the actual binary occupation is
# btree-node|data mixed.
#
#
#       btree-node:
#           [keys  values  children]
# note, I use square brackets to remind you that these
# things are contiguous in the file's binary. I may omit
# these brackets in the future.
#
#
#       keys:
#       [    ( actual-data pointer )+   ]
#       values:
#       [    ( actual-data pointer )+   ]
#       children
#       [    ( btree-node pointer )+    ]
# btree recap: the number of keys and values are the same
# while the number of children should be one more.
#
#
#       actual-data:
#           [type-code  data]
#
#       type-code:
#           8 bit unsigned integer
#
#       data:
#           anything
# note, type-code will tell you how to parse the data
# , for example, your type-code is 0, which is String
# in my database implementation, in String, we can decode
# or encode to utf-8 encoding, that is to say, you convert
# the bytes to human-readable representation, or do the
# reverse.
#
# frequently asked question:
#
# Q: why is type-code need
# A: so we can distinguish between various types of data.
#
# Q: how do I get the type-code.
# A: first, in my format spec, type-code is a unsigned 8 bit
# integer, that is enough. every time I read file just one byte
# for example: return_value = f.read(1)
# , I read one byte from the current file position, and then we
# need to parse the returned bytes to int,
# for example: I use `int.from_bytes` to do the
# conversion.
# then we'll get the integer, for example, we get the 0
# , then we know we should treat the following data as String
# (type-code 0 means String in my spec)


class Types:
    # this class load and dump every typed value
    # , plus tppe conversion between my own types
    # and python types. for example, when you do
    # insert, your passed str-type value will be
    # converted to format.String type automatically.

    # in this database implentation, value can be
    # typed and inserted(stored), just use one byte
    # length unsigned integer to indicate the type
    # of the stored value. (quick recap, in BNode
    # we store the pointer that points to the actual
    # stored data, and the data will be parsed by
    # this Types class), for example, if code if 1
    # , that indicates the data read afterwards is
    # Number-typed. so we can do the conversion,
    # like convert Number to python float.

    # note, Tree is a very special value type.
    # you can store tree in tree. in this database
    # implementation, VirtualBNode class is the place
    # where all the magics happen. with so-called Tree
    # type, you can store VirtualBNode in VirtualBNode
    # this is how it works:
    # if type code indicates the type of the value is
    # Tree, then .load method will help you jump to
    # that VirtualBNode using so-called node-start
    # -position, which is stored in format.Tree
    # this is important, the Tree data only store
    # the pointer to the next you-searched Tree (
    # VirtualBNode)

    # currently, we have following types supported.
    # where Tree is very special(I remind you this
    # again and again)
    # note, following list acts like a type-code-table
    # , the index is just like type-code.
    types = [
        String,  # 0
        Number,  # 1
        Tree,  # 2
        Empty,  # 3
        Boolean,  # 4
        Bytes,  # 5
    ]
    # note for myself,
    # types that will be added in the future:
    # Array

    @classmethod
    def load(cls, f):
        code = U8.load(f).n
        type_ = cls.types[code]
        obj = type_.load(f)

        # convert my format type to python type
        # for convenience.
        if type_ is String:
            result = obj.s
        elif type_ is Number:
            result = obj.n
        elif type_ is Tree:
            # very special. we just load it as
            # the VirtualBNode's instance right now
            # because Types.load is only called when
            # value.get() is called.

            root_node_p = obj.root_node.n
            vnode = VirtualBNode(
                f=f,
                node_p=root_node_p,
                parent=None,
            )
            vnode.access()
            result = vnode
        elif type_ is Empty:
            result = None
        elif type_ is Boolean:
            result = obj.value
        elif type_ is Bytes:
            result = obj.b
        else:
            # this else-branch will never be called.
            pass

        return result

    @classmethod
    def make_tree_type(cls, f, root_node_p):
        tree_p = f.tell()
        code = cls.types.index(Tree)
        U8(code).dump(f)

        Tree(Pointer(root_node_p)).dump(f)

        return tree_p

    @classmethod
    def create_tree(cls, f):
        # create tree in the current position.
        # return the tree data position
        # note: every data starts with code(length U8)
        # to indicate which type of data comes afterwards.
        # `Types.load` will scan this for proper init.

        root_node_p = f.tell()
        # create an empty tree(of course, BNodeFormat),
        # the process of building the tree is very
        # close to the original tree of the database
        # when you first init the database file.
        BNodeFormat(
            keys=[],
            values=[],
            children=[],
        ).dump(f)

        return Types.make_tree_type(f, root_node_p)

    @classmethod
    def dump(cls, data, f):
        # the reverse method to the load

        type_ = type(data)

        if type_ is str:
            obj = String(data)
        elif type_ in [int, float]:
            obj = Number(data)
        elif type_ is type(None):
            obj = Empty()
        elif type_ is bool:
            obj = Boolean(data)
        elif type_ is bytes:
            obj = Bytes(data)
        else:
            raise RuntimeError("Unsupported type", type_)

        code = cls.types.index(type(obj))
        U8(code).dump(f)
        obj.dump(f)


class Data:
    # using .get() to access the real data stored on disk or RAM.

    # this class will be used to refer to the data on the disk using pointer
    # in my btree implentation, the inserted key data will be cached directly.
    # and the inserted value data can be theoretically cached too, but since
    # cache uses RAM to boost speed, while most value data is quite big, so
    # RAM used only to cache the index (the bnode structure and the key data
    # for comparison) will be more practical.
    # note, that does not mean value data is not recommended to cache, you can
    # cache your frequently accessed value in your logic code. you just need to
    # make sure the cached value data is carefully selected in order to take
    # full advantage of your RAM.

    def __init__(
        self,
        p: Pointer,
        f,
        cached=None,
    ):
        self.p = p
        self.f = f
        self.cached = cached

        # if this marker is set, .freeze will freeze data
        # (type: VirtualBNode) too.
        # this marker will be set after data is first loaded
        # and type-checked(if loaded data is VirtualBNode
        # , then set this marker True).
        self.is_tree = False

    # deprecated.
    def get_cached(self):
        if self.cached is not None:
            return self.cached

        # ----------------------------
        data = self.get()
        # ----------------------------

        self.cached = data
        return data

    def get(self, using_cache=False):
        # this method get real data from disk
        # most of the time, you don't need to use cache.

        if self.is_tree:
            # tree type must use cache
            # reason 1:
            # tree type will return VirtualBNode
            # , just another index, index should be cached
            # for the reason of performance(already explained).
            # reason 2:
            # read the data again and again from the disk is
            # not even possible if reason 1 is true.
            # since this .get method will read the actual
            # data from .p position, and the real data(tree)
            # won't be present on disk until you call .freeze
            # in another expression:
            # before you call .freeze, the data at the .p
            # position will always be the old one
            # (for example, if you .create tree, you will get
            # the empty Tree on your disk, after you create
            # that, you should always manipulate instance in
            # your RAM for the sake of performance, then the
            # tree on your disk will not be touched until
            # .freeze is called.)
            using_cache = True

        if all([
            self.cached,
            using_cache,
        ]):
            return self.cached

        f = self.f
        p = self.p.n

        f.seek(p)
        # ----------------------------

        data = Types.load(self.f)

        # ----------------------------

        is_tree = type(data) is VirtualBNode
        if is_tree:
            self.is_tree = True

        if (
            is_tree
            or using_cache
        ):
            self.cached = data

        return data

    def __lt__(self, other):
        # compare function used by btree
        # that's the key to the btree implementation.

        if type(other) in [str, int, float, bytes]:
            return self.get(using_cache=True) < other
        elif type(other) is Data:
            return self.get(using_cache=True) < other.get(using_cache=True)


class MyIO:
    # this MyIO class makes change-file-object-on-the-fly
    # possible, just using `change_f` method to change
    # the current using file object.

    # note, in `modb`, MyIO will be used for the hot-reloading
    # of the database file, go and check `VirtualBNode.vacuum`
    # which take advantage of `MyIO.change_f`, since `vacuum`
    # method will create a new copy of current database file
    # , then a switch from old `f` to new `f` should be done.

    def __init__(self, f):
        # real one
        self.f = f

    @property
    def name(self):
        return self.f.name

    def change_f(self, new_f):
        # this method will be used
        # by VirtualBNode.vacuum method
        # to change the file-used on the fly.

        # make sure old one will be closed
        self.f.close()
        self.f = new_f

    def tell(self):
        return self.f.tell()

    def seek(self, offset, whence=io.SEEK_SET):
        p = self.f.seek(offset, whence)
        return p

    def read(self, size):
        contents = self.f.read(size)
        return contents

    def write(self, b):
        self.f.write(b)

    def close(self):
        self.f.close()


class VirtualBNode:
    # the class where all the magic happens in my implementation

    # frequently asked question:
    # Q: what is the relation between BNode and BTree?
    # A: BNode and Btree in this context are almost the same thing
    # , you see, a BNode can have its own children, so have everything
    # , but if you consider it overall, it is the BTree now.
    # now you see why there is BNode and Btree in the same time.
    #
    # Q: and what about VirtualBNode.
    # A: in aspect of behaviour, they are the same
    # , but VirtualBNode keeps the balance in the data transfer
    # between the hard drive(slow speed) and RAM(fast speed).
    # in a sentence, just a cache that cache the used node.
    # important note: the thing that truly makes process faster
    # is that all the construction process(splitting etc.) of
    # btree is happening in RAM. not in hard drive.
    #
    # Q: if the real btree construction process is happening
    # in the RAM, then when the tree is moved(written) back to the disk
    # for future access.
    # A: when .freeze is called. .freeze will be called automatically
    # when you close the database file. .freeze will do a relatively
    # smart check to avoid unnecessary f.write calls.
    # about technical details: .freeze do a so-called post-traverse.
    # that is children then parent traverse routine,
    # children will be traversed first, then we'll get the children's
    # pointers, and then passed to parent as parent's children.
    # you can also check the rough layout of this on-disk-database
    # file format.(in this source file on top)
    #

    def __init__(
        self,
        f: MyIO,
        node_p=-1,
        parent=None,
    ):
        self.f = f

        # indicate physical position,
        # -1 stands for new physical node
        self.node_p = node_p

        # another VirtualBNode
        # or None if no parent node
        self.parent = parent
        # quick check
        assert type(self.parent) in [
            VirtualBNode,
            type(None),
        ], f'meets {type(self.parent)}. VirtualBNode or NoneType expected.'

        # these three will be filled when .access is called
        self.keys = []
        self.values = []
        self.children = []

        # this marker make .freeze performance better
        # , since .freeze can skip un-modified node confidently
        self.modified = False

        # indicate whether self is accessed (using .access)
        self.accessed = False

        # new node must have these properties
        # since they are not on disk and they must
        # be written to disk when .freeze is called.
        if self.node_p == -1:
            self.modified = True
            self.accessed = True

    # public method as follows

    def insert(self, key, value):
        # insert the key-value pair
        # , return Data object of the inserted value.

        # , the inserted pair can be searched using .search method.
        # when inserting, if the key already exists
        # , modb.error.DuplicateKeyFound will be raised.

        # note, the supported type of inserted data is listed in docs.

        # type of value can be any supported type except Tree type
        # , since Tree type value can be created by .create method.
        # OR can be a Data object, in this case, the pointed data
        # will be used directly rather than .write_data again in
        # order to get the pointer. this feature can be used to
        # rename the key of the already inserted data OR move the
        # inserted key to somewhere-else, (actually `rename` and
        # `move` are the same thing, I'll explain that deeply in
        # the docs).

        # note for myself,
        # .write_data will do a f-seek-end operation
        # that will slow speed down dramatically
        # , maybe add bulk-insert or something like
        # that in the future.

        new_key_p = self.write_data(key)

        if type(value) is Data:
            # explained above.
            new_value_p = value_p = value.p.n
        else:
            new_value_p = self.write_data(value)

        key_data = Data(
            Pointer(new_key_p),
            self.f,
            cached=key,
        )
        value_data = Data(
            Pointer(new_value_p),
            self.f,
            # do not cache value data for the sake of RAM.
            cached=None,
        )

        self._insert(
            key_data,
            value_data,
        )

        return value_data

    def search(self, key):
        # search the key

        # if key found, return Data object
        # , you can .get() to get the actual structure(data) later
        # , otherwise, modb.error.KeyNotFound will be raised.

        node, idx = self._search(key)
        return node.values[idx]

    def follow(self, key_path: list):
        # this is a helper method to
        # search the key recursively.

        # since this database structure
        # is just like json. the hierarchy
        # can be created using .create method.

        # note if subtree is found, return that subtree
        # (Data), so you need to .get() first then
        #  you can use .create / .insert etc. just
        # like you do on the database object.
        # quick recap: VirtualBNode is the key
        # to my database implementation,
        # just like a database on its own.

        # init
        value = self

        # then search recursively
        for idx, key in enumerate(key_path):
            value = value.search(key)

            # following .get() is important
            # , every data value should be
            # .get() prior to access the real data
            # , tree-typed data is no exception.

            # for consistency, the last key will not be
            # .get(), we return Data to the user directly.
            if idx != len(key_path) - 1:
                value = value.get()
            # the idea is that the last key's type
            # is not predictable.
            # but, when you .follow(['a', 'b', 'c'])
            # the key 'a' and key 'b' must be tree typed.
            # so we can search the subtree recursively.
            # for example,
            # following two lines are identical.
            # 1. .follow(['a'])
            # 2. .search('a')

        return value

    def items(self, reversed=False):
        # items method acts just like dict.items do
        # , yield list of key-value pairs (all Data typed)

        # technical details:
        # this method will do an in-order traversal on self.

        if reversed:
            def do(x): return list(reversed(x))  # mirrored
        else:
            def do(x): return x  # nothing

        # like any other method, you should make sure that
        # the manipulated node is accessed first.
        if not self.accessed:
            self.access()

        keys = do(self.keys)
        values = do(self.values)
        children = do(self.children)

        # 1. traverse one side
        # 2. yield relative root node (pair)
        # 3. traverse the most-other side

        # two possibilities, leaf or internal node
        # note, following codes can shrink even further
        # , if you use custom `zip` function.
        # (like using fill parameter)
        if self.is_leaf():
            for key, value in zip(
                keys,
                values,
            ):
                yield key, value

        else:
            for key, value, child in zip(
                keys,
                values,
                children,
            ):
                # has child, do recursive call.
                yield from child.items(reversed)

                # same as is_leaf if branch
                yield key, value

            # has child, do recursive call.
            yield from children[-1].items(reversed)

    def range(
        self,
        key_start,
        key_stop,
    ):
        # do a range query, yield key-value pair stream
        # this operation is very efficient thanks
        # to btree.

        # note, key_stop will not be included in the stream.

        node_a, idx_a = self.peek(key_start)
        node_b, idx_b = self.peek(key_stop)

        if idx_b is not None:
            stop_indicator = node_b.keys[idx_b]
        else:
            stop_indicator = None

        for key, value in node_a.inorder_from(idx_a):
            if (
                stop_indicator
                and key is stop_indicator
            ):
                break

            yield key, value

    def inorder_from(self, idx):

        for idx in range(
            idx,
            len(self.keys),
        ):
            yield self.keys[idx], self.values[idx]

            if not self.is_leaf():
                yield from self.children[idx+1].items()

        if self.parent is not None:
            which_idx = self.find_from_which_branch()
            yield from self.parent.inorder_from(which_idx)

    def update(self, key, new_value):
        # update the value of the given key.

        # note, the old value will not be
        # eraised from your disk before you do
        # .vacuum

        # technical detail:
        # replace the old value pointer
        # with the new value pointer
        # , then return the old value Data object
        # (quick recap: Data object holds pointer)

        node, idx = self._search(key)
        old_value_data = node.values[idx]
        new_value_p = self.write_data(new_value)
        value_data = Data(
            Pointer(new_value_p),
            self.f,
            # again, do not cache value data for the sake of RAM.
            cached=None,
        )
        node.values[idx] = value_data
        return old_value_data

    def vacuum(self):
        # do vacuum, the freed size will be returned.

        # after this operation, the database file
        # should be vacuumed, the un-used space will
        # be freed.
        # (recap, .update and .delete operation are
        # the two that may make un-used space)
        # note, the only benefit of doing so is your
        # freed disk space if possible.
        # warning, this vacuum operation is slow
        # since it makes copy, please do this operation
        # when it's really really needed.

        # the procedure as follows
        # 1. make a new empty file
        # 2. init the file as database
        # 3. traverse current database while moving
        # any valid data to the new database file
        # 4. replace the old database

        logger.info('start vacuuming')

        # for correct vacuuming, every modification needs to
        # be already written to the disk, so we need to
        # do a freeze first to make sure that.
        self.freeze()

        before_size = self.f_seek_end()

        # - create and init a new file

        # get current database file name
        filename = self.f.name
        name = os.path.basename(filename)
        folder = os.path.dirname(filename) or '.'

        now = datetime.now()
        t = f'{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}'
        tmp_path = f'{folder}/{name}.{t}.tmp'

        with open(
            tmp_path,
            mode='wb',
        ) as f:
            file_start_p = f.tell()
            utils.make_header(0).dump(f)
            # -------------------------------
            # make a link table for _vacuum to use
            self.tmp_vacuum_link_table = {}
            # note about link
            # you can insert two keys with the same data pointer
            # use tmp_vacuum_link_table to avoid duplicates when
            # copying the data
            new_node_start_p = self._vacuum(f)
            # -------------------------------
            f.seek(file_start_p)
            utils.make_header(new_node_start_p).dump(f)

            del self.tmp_vacuum_link_table

        # close then remove right now
        self.f.close()
        os.remove(filename)

        # replace the old one
        os.rename(tmp_path, filename)

        # open new one
        new_f = open(
            filename,
            mode='r+b',
        )
        # change the file-used on the fly
        # thanks to the MyIO class
        self.f.change_f(new_f)

        # important: re-start the vnode(self) too
        self.node_p = new_node_start_p
        self.access()

        after_size = self.f_seek_end()

        logger.info('end vacuuming')

        freed_size = before_size - after_size
        # if following assertion fails
        # , file will be broken in a high chance.
        assert freed_size >= 0, "weird thing happened."

        return freed_size

    def delete(self, key):
        # delete the key-value pair by key
        # , then return the deleted value(Data object)

        node_targeted, idx = self._search(key)
        deleted_value_data: Data = node_targeted.values[idx]

        if node_targeted.is_leaf():
            # delete now, then check

            del node_targeted.keys[idx]
            del node_targeted.values[idx]

            node_targeted.check_after_delete()

        else:
            # try to find inorder predecessor node

            predecessor_node = node_targeted.find_inorder_predecessor_node(idx)

            node_targeted.keys[idx] = predecessor_node.keys.pop(-1)
            node_targeted.values[idx] = predecessor_node.values.pop(-1)

            predecessor_node.check_after_delete()

        return deleted_value_data

    def create(self, key):
        # note, this method is a special insert method
        # instead of inserting normal type(string, number etc. type)
        # you will insert a empty tree(tree type).

        # create a tree-typed value data.
        # most of the time, this is for building
        # hierarchical structure.

        # , you can then .search, and insert data
        # to this sub-tree

        # for example, first,
        #       node.create('sub')
        # then,
        #       sub = node.search('sub').get()
        #       sub.insert('mykey', 'myvalue')
        # just act like another database.
        # (tree in tree, recursively)

        # recap again, most of the time
        # , this is for building hierarchical structure.

        new_key_p = self.write_data(key)

        self.f_seek_end()
        new_value_p = Types.create_tree(self.f)

        key_data = Data(
            Pointer(new_key_p),
            self.f,
            cached=key,
        )
        value_data = Data(
            Pointer(new_value_p),
            self.f,
            cached=None,
        )

        self._insert(
            key_data,
            value_data,
        )

        return value_data

    def freeze(self):
        # this method moves index to the disk.

        # before this method is called, index is cached
        # in memory and all the index operation (like
        # splitting, merging) is performed in memory to
        # boost the index performance.

        # this method involves disk IO operations
        # , call me when it's really needed.

        logger.info('start freezing')
        self._freeze()
        logger.info('end freezing')

    # private method as follows

    def init_node(self, node: BNodeFormat):
        keys = [
            Data(p, self.f)
            for p in node.keys
            if p.n != 0
        ]
        values = [
            Data(p, self.f)
            for p in node.values
            if p.n != 0
        ]
        children = [
            VirtualBNode(
                self.f,
                node_p=p.n,
                parent=self,
            )
            for p in node.children
            if p.n != 0
        ]

        return keys, values, children

    def access(self):
        # this method will grab real bnode from disk.
        # whenever this method is called, that on-disk bnode
        # will be grabbed and converted to the in-memory bnode
        # (note, `in-memory bnode` is just a fancy expression for instance
        # of class in this context)
        # note, ONLY that ONE bnode is accessed, its children will not
        # be accessed until you access that each individual child too.
        # note, this .access method is designed to take advantage of
        # RAM, the main memory on your computer, which is way faster
        # than your secondary memory, hard drive. so you have to make
        # sure that you call .access when it's really needed.
        # note, when given bnode is accessed(is already a instance), all
        # the operation(tree-splitting etc.) in the future will be performed
        # directly on the instance for performance reasons, and write
        # it back to the disk when .freeze is called.

        self.accessed = True

        self.f.seek(self.node_p)
        node = BNodeFormat.load(self.f)
        keys, values, children = self.init_node(node)

        self.keys = keys
        self.values = values
        self.children = children

    def is_leaf(self):
        if self.accessed:
            return self.children == []
        else:
            raise RuntimeError('must self.access() first.')

    def find_closest_leaf_node(self, key):
        if not self.accessed:
            # for continuing finding self, you must ensure that
            # self is already accessed from the disk before finding.
            self.access()

        # quickly check whether our goal is reached.
        if self.is_leaf():
            return self

        idx = bisect.bisect_left(
            self.keys,
            key,
        )

        child = self.children[idx]
        if not child.accessed:
            # same reason, if not accessed yet. access it right now.
            # we have no choice, we are destined to find the closest
            # leaf node.
            child.access()

        # keep looking till leaf node found (recursively)
        return child.find_closest_leaf_node(key)

    def f_seek_end(self):
        # note for myself: seek took time to perform too
        return self.f.seek(0, io.SEEK_END)

    def write_data(self, data):
        # write data(key or value) to the disk
        # , then return the start position of that data

        blob_p = self.f_seek_end()
        # ---------------------------------
        Types.dump(data, self.f)
        # ---------------------------------

        return blob_p

    def _insert(self, key: Data, value: Data):
        vnode_targeted = self.find_closest_leaf_node(
            key.get(using_cache=True)
        )

        idx = bisect.bisect_left(
            vnode_targeted.keys,
            key.get(using_cache=True),
        )

        # check duplicate key here
        if idx < len(vnode_targeted.keys):
            # `placed` is the placed key
            # (already inserted key)
            placed = vnode_targeted.keys[idx].get(using_cache=True)

            # `requested` is the requested key
            # (we, the database, are requested to
            # insert that key, or in another expression
            # , that key will be inserted right now
            # if possible)
            requested = key.get(using_cache=True)

            # if following condition is true
            # , the duplicate key must exist.
            # since we do duplicate-key check
            # everytime, we can make sure
            # the Error is raised in time.
            if placed == requested:
                raise error.DuplicateKeyFound(
                    requested,
                )

        vnode_targeted.keys.insert(
            idx,
            key,
        )
        vnode_targeted.values.insert(
            idx,
            value,
        )
        vnode_targeted.modified = True

        vnode_targeted.check_after_insert()

    def check_after_insert(self):
        if len(self.keys) > BNODE_MAX_CAPACITY:
            self.split_me()

    def check_after_delete(self):
        # minimum capacity required except for the root node
        if (
            len(self.keys) < BNODE_MIN_CAPACITY
            and self.parent is not None
        ):
            self.merge_me()

    def find_inorder_predecessor_node(self, idx):
        if self.is_leaf():
            return self

        child = self.children[idx]
        return child.find_inorder_predecessor_node(-1)

    def find_from_which_branch(self):
        idx = self.parent.children.index(self)
        return idx

    def merge_me(self):
        def change_parent(nodes, new_parent):
            for node in nodes:
                node.parent = new_parent

        # if leaf node
        #       if more than minimum number of keys
        #               do nothing

        # if leaf node
        #       if not more than minimum number of keys
        idx = self.find_from_which_branch()

        if idx == 0:
            # find right sibling
            right_sibling = self.parent.children[idx+1]

            # if right sibling can give me a key
            if len(right_sibling.keys) > self.min_capacity:
                self.keys.append(
                    self.parent.keys[idx]
                )
                self.values.append(
                    self.parent.values[idx]
                )

                if not right_sibling.is_leaf():
                    self.children.append(
                        right_sibling.children.pop(0)
                    )
                    self.children[-1].parent = self

                self.parent.keys[idx] = right_sibling.keys.pop(0)
                self.parent.values[idx] = right_sibling.values.pop(0)

            # if right sibling can not give me a key
            else:
                # merge self and right sibling

                self.keys = (
                    self.keys
                    + [self.parent.keys[0]]
                    + right_sibling.keys
                )
                self.values = (
                    self.values
                    + [self.parent.values[0]]
                    + right_sibling.values
                )

                if not self.is_leaf():
                    self.children = (
                        self.children
                        + right_sibling.children
                    )
                    change_parent(self.children, self)

                del self.parent.keys[0]
                del self.parent.values[0]
                del self.parent.children[idx+1]

                self.parent: VirtualBNode
                self.parent.check_after_delete()

        else:
            # find left sibling
            left_sibling = self.parent.children[idx-1]

            # if left sibling can give me a key
            if len(left_sibling.keys) > self.min_capacity:
                self.keys.insert(
                    0,
                    self.parent.keys[idx-1],
                )
                self.values.insert(
                    0,
                    self.parent.values[idx-1],
                )

                if not left_sibling.is_leaf():
                    self.children.insert(
                        0,
                        left_sibling.children.pop(-1)
                    )
                    self.children[0].parent = self

                self.parent.keys[idx-1] = left_sibling.keys.pop(-1)
                self.parent.values[idx-1] = left_sibling.values.pop(-1)

            # if left sibling can not give me a key
            else:
                # merge left and self sibling

                self.keys = (
                    left_sibling.keys
                    + [self.parent.keys[idx-1]]
                    + self.keys
                )
                self.values = (
                    left_sibling.values
                    + [self.parent.values[idx-1]]
                    + self.values
                )
                if not self.is_leaf():
                    self.children = (
                        left_sibling.children
                        + self.children
                    )
                    change_parent(self.children, self)

                del self.parent.keys[idx-1]
                del self.parent.values[idx-1]
                del self.parent.children[idx-1]

                self.parent.check_after_delete()

        if len(self.parent.keys) == 0:
            self.parent.keys = self.keys
            self.parent.values = self.values
            self.parent.children = self.children

            change_parent(self.parent.children, self.parent)

    def split_me(self):
        # this method is the key to the Btree building
        # if you are for educational comment, go and check
        # another python btree source code.
        # this current file source code is all about
        # file format and on-disk-database.

        def two_parts(node, middle_idx):

            left_keys = node.keys[:middle_idx]
            right_keys = node.keys[middle_idx+1:]
            left_values = node.values[:middle_idx]
            right_values = node.values[middle_idx+1:]
            left_children = node.children[:middle_idx+1]
            right_children = node.children[middle_idx+1:]
            return (
                left_keys,
                right_keys,
                left_values,
                right_values,
                left_children,
                right_children,
            )

        def change_parent(nodes, new_parent):
            for node in nodes:
                node.parent = new_parent

        middle_idx = int(BNODE_MAX_CAPACITY / 2)
        middle_key = self.keys[middle_idx]
        middle_value = self.values[middle_idx]

        (
            left_keys,
            right_keys,
            left_values,
            right_values,
            left_children,
            right_children,
        ) = two_parts(
            self, middle_idx,
        )

        left_node = VirtualBNode(self.f)
        right_node = VirtualBNode(self.f)
        left_node.keys = left_keys
        left_node.values = left_values
        right_node.keys = right_keys
        right_node.values = right_values
        change_parent(left_children, left_node)
        change_parent(right_children, right_node)
        left_node.children = left_children
        right_node.children = right_children

        if self.parent is None:
            left_node.parent = self
            right_node.parent = self
            self.keys = [middle_key]
            self.values = [middle_value]
            self.children = [left_node, right_node]
            self.modified = True

        elif self.parent is not None:
            self.parent.modified = True

            left_node.parent = self.parent
            right_node.parent = self.parent

            # space re-used
            left_node.node_p = self.node_p

            idx = bisect.bisect_left(
                self.parent.keys,
                middle_key,
            )

            self.parent.keys.insert(idx, middle_key)
            self.parent.values.insert(idx, middle_value)
            new_left_child_idx = idx
            new_right_child_idx = idx + 1

            self.parent.children[
                new_left_child_idx
            ] = left_node
            self.parent.children.insert(
                new_right_child_idx,
                right_node,
            )

        if self.parent is not None:
            self.parent.check_after_insert()

    def peek(self, key):
        # get exact or closest-right match, used by _search

        idx = bisect.bisect_left(
            self.keys,
            key,
        )

        not_most_right = idx < len(self.keys)

        if not_most_right:
            if self.keys[idx].get(using_cache=True) == key:
                return self, idx

        if self.is_leaf():
            # if the searched key is still not found
            # , the searched key does not exist.

            # but in `peek`, try to return the closest
            # -right one.

            if not_most_right:
                return self, idx
            else:
                return self, None

        else:
            # otherwise, keep searching.

            child = self.children[idx]
            if not child.accessed:
                # not accessed yet. access it right now.
                child.access()

            node, idx = child.peek(key)
            if idx is not None:
                return node, idx
            elif not_most_right:
                return self, idx
            else:
                return self, None

    def _search(self, key):

        idx = bisect.bisect_left(
            self.keys,
            key,
        )

        if idx < len(self.keys):
            if self.keys[idx].get(using_cache=True) == key:
                return self, idx

        if self.is_leaf():
            # if the searched key is still not found
            # , the searched key does not exist.

            raise error.KeyNotFound(
                key,
            )

        else:
            # otherwise, keep searching.

            child = self.children[idx]
            if not child.accessed:
                # not accessed yet. access it right now.
                child.access()

            return child._search(key)

    def seek_written_position(self):
        # recap again, if node_p is set to -1
        # , that means this node have never existed before
        # , so we need to use new disk space
        # , as to new space, the end of the file
        # will be a good choice.
        # otherwise, just seek to the old node position
        # for space re-use.

        if self.node_p == -1:
            start_position = self.f_seek_end()
        else:
            start_position = self.f.seek(self.node_p)

        # return the seeked position for future purpose
        # , like we will pass position to so-called parent
        # node, and position be stored as parent's value-data
        # pointer or something like that.
        return start_position

    def _freeze(self):
        # this post-order traversal will be good
        # bottom(left to right) then top(root)

        # if current node is never be accessed
        # , then its children will never be accessed too
        # , just return the original position will be OK.
        if not self.accessed:
            return self.node_p

        # extract just pointers, which will be written back
        # to the disk using the helper-format-class
        # (note, self.keys and self.values are Data typed.
        # the Data class simplifies the process where
        # actual can be read from the disk. just use .get()
        # and every conversion will be done automatically.
        # obviously when we do freeze, everything we need
        # is just the pointers(ints), the pointer that guides
        # us to the place where actual data is stored.
        # recap: the actual data is always started with one
        # byte length unsigned integer, that is type code.)
        keys = [
            each.p for each in self.keys
        ]
        values = [
            each.p for each in self.values
        ]

        # recursive check and traverse tree-typed value
        for value in self.values:
            # in my implentation, if .is_tree is set to True
            # , the type of the value must be Tree and must
            # have been accessed. if value.is_tree is False
            # , that value may be tree still, but just not
            # be accessed yet. in this context, `access` means
            # that the value.get() has been called.
            # (recap: value.get() will return VirtualBNode if
            # value type is Tree)
            if value.is_tree:
                subtree = value.get(using_cache=True)
                # use following code to debug, you can see
                # the python object id of the tree
                # print('subtree', subtree)

                # use ._freeze() to avoid logging
                subtree._freeze()

        if self.is_leaf():
            start_position = self.seek_written_position()

            if not self.modified:
                return start_position

            BNodeFormat(
                keys=keys,
                values=values,
                children=[],
            ).dump(self.f)

            self.modified = False

            return start_position

        children_ptr = []
        for idx in range(len(self.children)):
            child = self.children[idx]
            ptr = child._freeze()
            children_ptr.append(ptr)

        start_position = self.seek_written_position()

        if not self.modified:
            return start_position

        BNodeFormat(
            keys=keys,
            values=values,
            children=[Pointer(p) for p in children_ptr],
        ).dump(self.f)

        self.modified = False

        return start_position

    def _vacuum(self, f: io.RawIOBase):
        if not self.accessed:
            self.access()

        keys = []
        values = []
        for data in self.keys:
            p = data.p.n
            # --------------------------
            self.f.seek(p)
            k = Types.load(self.f)
            # --------------------------

            start_position = f.tell()
            Types.dump(k, f)
            keys.append(start_position)

        for data in self.values:

            p = data.p.n
            # --------------------------
            if p in self.tmp_vacuum_link_table:
                values.append(
                    self.tmp_vacuum_link_table[p]
                )
                continue

            self.f.seek(p)
            v = Types.load(self.f)
            # --------------------------

            if type(v) is VirtualBNode:
                node_p = v._vacuum(f)
                start_position = Types.make_tree_type(f, node_p)

            else:
                start_position = f.tell()
                Types.dump(v, f)

            self.tmp_vacuum_link_table[p] = start_position
            values.append(start_position)

        keys = [
            Pointer(p) for p in keys
        ]
        values = [
            Pointer(p) for p in values
        ]

        if self.is_leaf():
            start_position = f.tell()

            BNodeFormat(
                keys=keys,
                values=values,
                children=[],
            ).dump(f)

            return start_position

        children_ptr = []
        for idx in range(len(self.children)):
            child = self.children[idx]
            ptr = child._vacuum()
            children_ptr.append(ptr)

        print('wat'*20, children_ptr)

        start_position = f.tell()

        BNodeFormat(
            keys=keys,
            values=values,
            children=[Pointer(p) for p in children_ptr],
        ).dump(f)

        return start_position


class Database:
    # relatively high-level api that users can use directly.

    def __init__(self, filename, read_only=False):
        self.filename = filename
        self.read_only = read_only

        if not os.path.exists(self.filename):
            self.init_database_file()

        # original file object
        self._f = open(
            self.filename,
            mode='r+b',
        )

        # note,
        # self._f is definitely original file object
        # self.f is mmap object or self._f

        if self.read_only:
            # using mmap-io is faster for query on disk
            self.f = mmap.mmap(
                self._f.fileno(),
                length=0,
                access=mmap.ACCESS_READ,
            )
        else:
            # do nothing, just using stardard-io
            self.f = self._f

        # wrapper, go check `MyIO` class for more information
        self.f = MyIO(self.f)

        # make sure we are at the beginning
        # , then read the header
        self.f.seek(0, io.SEEK_SET)

        self.header = Header.load(self.f)
        self.root_p = self.header.root_node.n

        # will be VirtualBNode instance after .connect() is called.
        self.vnode = None

    def connect(self):
        # return the VirtualBNode instance of current database
        # note again: VirtualBNode is where all the magic happens.
        # you can do insert, search etc. operation on it.

        self.vnode = VirtualBNode(
            f=self.f,
            node_p=self.root_p,
            parent=None,
        )
        self.vnode.access()
        return self.vnode

    def close(self):
        # close the database.
        # you must call this method before you exit your program.
        # otherwise, there's a high chance that your inserted data will
        # be lost.

        if self.read_only:
            pass
        else:
            # if database connected
            if self.vnode:
                # make sure the index will be written to the disk
                self.vnode.freeze()

                # try to close file
                # that node's using
                self.vnode.f.close()

        # try to close initial file
        self._f.close()

    @classmethod
    def write_initial_database_header(cls, f):
        file_start_p = f.tell()
        utils.make_header(0).dump(f)
        node_start_p = f.tell()
        # empty node
        BNodeFormat(
            keys=[],
            values=[],
            children=[],
        ).dump(f)
        f.seek(file_start_p)
        utils.make_header(node_start_p).dump(f)

    def init_database_file(self):
        logger.info('start init database file')
        with open(self.filename, mode='wb') as f:
            Database.write_initial_database_header(
                f
            )
