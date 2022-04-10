## Install

Most users choose to simply install from pypi.
```
pip install modb-py
```


## Import

```python
import modb
```

## Open
We open a database file by filename just like `open`.
```python
db = modb.Database('./a.modb')
```
!!! note "Note about file path"
    If the given path involves missing directory, you must create that directory first, then open the file.

Now, we have `db` as our database.
If the database is initialized correctly, then the database should already have an empty `node` for us to `insert` something to our current database.
!!! tip
    `node` is like a handler in this context which acts like a deliverer that passes our operations to the correct sub-node, you will be more familiar with it later. To those guys that already know the Btree structure. this `node` is the root node of Btree.

Let's get that initial node!
```python
node = db.connect()
```

This kind of node is the key to our database, they play a KEY role in almost every operations you need later.

## Insert

Maybe we should insert something to our `node` now.

```python
node.insert(
    key="hello",
    value="world",
)
```
We insert a `key` into our database with a corresponding `value`. You may remember that key-value pair is something related to `python dict` structure or `JSON-like` structures, then you are right. In my database implementation, the whole thing is just like a fast on-disk dictionary.

Let's add one more
```python
node.insert(
    key="hi",
    value="my own database",
)
```

## Search

So now, since we have something inserted into our `node` 

!!! note
    In this context, `node` and `database` share the same meaning

Let's retrieve that value back by searching the key.

```python
resp = node.search("hello")
```

This line of code will return `Data` object.
!!! summary "What's `Data` object?"
    In this context, `Data` is a class, this class only holds the pointer information, which guides us to find the real data.

After you get a basic understanding of `Data`, you'll know that this `search` method only find the data pointer that points to the actual data.

If you want to get that actual data(the value data you inserted before), you can do the following.

```python
value = resp.get()
# value -> "world"
```
This time, the actual data will be read (if on disk).

!!! tip
    `resp` is short for response if you're curious. That's just a fancy word for return value.

## Create

If you want to build a very hierarchical structure just like `dict` or `json`, you can use `create` method of your targeted node.
!!! note "Note about `create` method"
    `create` is a very special `insert` operation in this database

For example, you can have subtree in our initial `node`
```python
# first create a subtree with the key "my_subtree" 
node.create("my_subtree")

# then get that `node` representing that subtree
my_subtree = node.search("my_subtree").get()
```

For now, the variable `my_subtree` is just like the initial `node`, they are of the same type. You can do every operations you just learned to this `my_subtree`.

For those guys that still do not take this concept, you can think of the current `node` as follows:
```python
{
    "hello": "world",
    "hi": "my own database",
    "my_subtree": {
        # when you do operations to my_subtree,
        # like .insert, then the inserted key-value
        # pair will go here.
    },
}
# I hope you understand it now.
```

So, recap again, this `create` method is just a special case of `insert`.

## Update

```python
node.update(
    key="hi",
    new_value="modb!",
)
```
!!! warning
    `update` may make un-used disk space just like `delete`, since the old value data remains in the binary of your file. go and check next topic to know more about this behavior.

## Delete

You can delete the inserted data from that node too.
```python
node.delete('hello')
```
!!! warning
    if you do delete a lot, you better go and check out [this topic](./../FAQ/#how-does-delete-work-why-file-still-holds-its-size-after-deletion).



## Freeze

Actually, there is a secret that I have not told you until now. All the operations that you have done so far are all happening in your RAM, the `node` is the embodiment of your actual node on your hard drive. This is for performance reasons, since IO-speed is way faster in RAM than on your disk.
!!! note
    Only key data and `node` is stored in your RAM, the `node` has an alias called `index`. So you can think that `index` is cached in you RAM.

So, if the `node` is in your RAM now, how do you move that `node` into your hard drive for future read. You guessed it, that's where `freeze` method comes into play.

```python
node.freeze()
```

This one line of code will move everything in that `node` to the disk.
!!! tip
    * If you use this database library on your server, you probably should call this `freeze` method on `node` periodically. the database itself will not call this method automatically but only when `close` is called.
    * Most of the time, you only need to call this method on so-called top `node`, the node which .connect() returns to you, the `freeze` method will figure it out which key-value pair data should really be freezed to the disk, which ensures that minimum disk-IO will be done.

## Close

`close` the database object is important. otherwise your inserted data will be lost.
!!! note "Recap"
    `close` will `freeze` your `node` automatically, then close the file descriptor.

```python
db.close()
```

```python title="Best practice"
import modb

db = modb.Database("./a.modb")
try:
    node = db.connect()
    ...

finally:
    db.close()
```


