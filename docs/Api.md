
## *class* **modb.high.Database**
> Alias: modb.Database


`Parameters`

:   * **filename** `str`

    open the database file by path, if it does not exist, the empty database file will be created.

    !!! note "Note about file path"
        If the given path involves missing directory, you must create that directory first, then open the file.


    * **read_only** `bool`

        if set, *mmap* will be used internally to speed up the query performance **AND** you can not do any operations involving write-IO.


`Methods`

:   ### connect

    `return`

    :   *modb.low.VirtualBNode*

    get the root node of the database.



    ### close

    freeze the root node then release the file object. This method must be called in the end.


## *class* **modb.low.Data**
> Alias: modb.Data

!!! tip

    * this class will be used to refer to the data on the disk using pointer in my btree implentation, the inserted key data will be cached directly. and the inserted value data can be theoretically cached too, but since cache uses RAM to boost speed, while most value data is quite big, so RAM used only to cache the index (the bnode structure and the key data for comparison) will be more practical. 

    * that does not mean value data is not recommended to cache, you can cache your frequently accessed value in your logic code. you just need to make sure the cached value data is carefully selected in order to take full advantage of your RAM.   


`Methods`

:   ### get

    `Parameters`

    :   **using_cache** `bool`
        
        : this parameter is only used internally. or do a warm-up to database cache.

    get real data from disk


## *class* **modb.low.VirtualBNode**

`Methods`

:   ### insert

    `Parameters`

    : **key** `see Data types`

    : **value** `see Data types`

    `return`

    :   *modb.low.Data*

    insert the key-value pair, return Data object of the inserted value.


    ### search

    `Parameters`

    : **key** `see Data types`

    `return`

    :   *modb.low.Data*

    search the key, if found, return Data object of the corresponding value, note, you can call `get` on returned Data object to get the actual data.
    if not found, `modb.error.KeyNotFound` will be raised.

    ### follow

    `Parameters`

    : **key_path** `list`

    `return`

    :   *modb.low.Data*

    this is a helper method to search the key recursively.

    !!! note

        * since this database implementation support nested node, which is just like json in binary format. the hierarchy can be created by using `create` method on node.
    
        * if subnode (subtree) is found, return that subtree (Data), so you need to call `get` first then you can use `create` / `insert` etc. just like you do on the root `node` object. quick recap: modb.low.VirtualBNode is the key to my database implementation.

    ### items

    `Parameters`

    : **reverse** `bool`

        :   if set, the returned stream will be in reverse order.

    `return`

    :   key, value Data *generator*

    !!! tip "Technical details"

        this `items` method do an in-order traversal. 


    ### range

    `Parameters`

    : **key_low** `see Data types`

    : **key_high** `see Data types`

    : **reverse** `bool`

        : if set, the returned stream will be in reverse order.

    `return`

    :   key, value Data *generator*

    do a range query.

    !!! note

        this operation is very efficient thanks to the btree structure.


    ### update

    `Parameters`

    : **key** `see Data types`

    : **new_value** `see Data types`

    `return`

    : *modb.low.Data* - old value

    update the value of the given key. return the old value Data object.

    !!! warning

        the old value will not be eraised from your disk before you do `vacuum`.

    !!! tip "Technical details"

        This operation only replaces the old value pointer with the new value pointer. quick recap: Data object holds the pointer.
    
    ### vacuum

    `return`

    : *int* - the freed file size in bytes

    do vacuum to the database file, the freed file size will be returned.

    !!! note "Benefit"

        the only benefit of calling this `vacuum` method is your freed disk space if possible

    !!! tip "Technical details"

        after this operation, the database file should be vacuumed, that is to say, the un-used space will be freed.
        recap: `update` and `delete` will make un-used space.

        The procedure as follows:

        1. make a new empty file
        2. init the file as database
        3. traverse current opened database while moving any valid data to the new database file
        4. replace the old database with the new one
   
    !!! warning

        since this operation makes copy, please only do when it's really really needed.
    

    ### delete

    `Parameters`

    : **key** `see Data types`

    `return`

    : *modb.low.Data* - the deleted value data

    delete the key-value pair by key, then return the deleted value data(Data object)

    !!! warning

        your deleted data will still be in your binary of the file. do `vacuum` to make sure it's safe-deleted. go and check FAQ for more information.

    ### create

    `Parameters`

    : **key** `see Data types`

    `return`

    : *modb.low.Data* - the new created sub-node value

    !!! note

        * this `create` method is a special `insert` method instead of inserting normal type (string, number etc.) you'll insert a empty tree (tree type)

        * most of the time, this is for building a hierarchical structure.

    ```python title="Sample code"
    node.create("sub")

    # then you can get the sub node by doing
    sub = node.search("sub").get()

    # ... there you can do any operations just
    # like you do to the root `node`
    sub.insert("hello", "world")
    ```
    
    ### freeze

    moves `index` to the disk for future reuse

    !!! note

        * before this method is called, index will be cached in memory and all the index (btree) operation (like splitting, merging etc) is performed in memory for performance reasons.

        * this `freeze` method will be called automatically while you call `close` to the database object.

    !!! warning

        this method involves disk-IO operations, call it when it's really needed.


    
