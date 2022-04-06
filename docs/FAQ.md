## How does `search` work and what will it return

The `search` method will find your targeted key by recursively jumping to the right node of the btree, If the key is found, then `Data` type object will be returned. otherwise raise the exception (modb.error.KeyNotFound)

## What is `Data`

`Data` object will be returned often when you `search` the key from the node.

This kind of object holds the pointer which points to the actual data on you disk (if possible), if you want to read that real data, you should call `get` method on `Data` object manually to get that inserted data.

This kind of object can be used to make links also, go and check next topic for more information.

## How to make an alias of another key

This is to say that how to make multiple keys that point to the same value data.

```python title="Way to do it"
# the `insert` method will return the inserted value data (the pointer)
data = node.insert("hi", "world!")

# make an alias right now
node.insert("hello", data)
```

Now key `hi` and `hello` share the same value data, no duplicates on your disk.

Here is another way of doing so
```python
node.insert(
    key="hiya",
    value=node.search("world"),
)
```

Now key `hi` and `hello` plus `hiya` all share the same value data.

!!! tip
    You'll notice that `search`, `insert`, and `delete` all will return `Data` object which you can make use of.


## How to re-name or move the existing key

Suppose that you have the following init, and you want to rename `hi` to `hello`.

```python
node.insert(
    key="hi",
    value="world",
)
```

❌ *wrong* way to re-name

```python
node.insert(
    key="hello",
    value="world",
)
node.delete("hi")
```

:white_check_mark: *correct* way to re-name

```python
node.insert(
    key="hello",
    value=node.search("hi"),
)
node.delete("hi")
```

In this way, the already inserted value will be re-used directly, avoiding the unintended duplication of value data.

Actually, if you just want to do a re-name, you can simply do the following

:white_check_mark: *correct* and *recommended* way to re-name

```python
node.insert(
    key="hello",
    value=node.delete("hi"),
)
```
This is because `delete` method will return the deleted value data


## How does `delete` work, why file still holds its size after deletion 

After you call `delete` method, only the targeted key-value pointers will be deleted and the btree will be internally re-balanced.

!!! note "Note and Recap"
    * Only pointers will be deleted, the actual data will still be on your disk
    * In this database, I use btree as structure
  
If you want to so-called `safe-delete` the data from the file, you can call `vacuum` on `node`
```python
node.vacuum()
```
!!! warning
    This `vacuum` operation is IO-heavy, make sure you really want to free the un-used disk space.


## Can I recover the deleted key-value pair

Really hard, in current database format, when `delete` method is called, the key-value pointers will be erased. Although the inserted data will still be on your disk, but the pointer is deleted(lost), then there is no easy way to reconstruct the pair as it was before.

!!! note
    * Before you do `vacuum`, the value is still in the binary of your database file, you can do backup then do vacuum to compare the difference. This can give you your deleted bytes, but the boundary between each deleted pair is blurred, so you can not recover it automatically.
    * After you do `vacuum` operation on your `node`, there is no way at least in user-level that can recover the deleted data.

