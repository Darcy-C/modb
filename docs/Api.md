
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

    : *key* `see Data types`

    : *value* `see Data types`

    `return`

    :   *modb.low.Data*

    insert the key-value pair, return Data object of the inserted value.


    ### search

    `Parameters`

    : *key* `see Data types`

    `return`

    :   *modb.low.Data*

    search the key, if found, return Data object of the corresponding value, note, you can call `get` on returned Data object to get the actual data.
    if not found, `modb.error.KeyNotFound` will be raised.

    ### follow

    `Parameters`

    : *key_path* `list`

    `return`

    :   *modb.low.Data*

    this is a helper method to search the key recursively.

    !!! note

        * since this database implementation support nested node, which is just like json in binary format. the hierarchy can be created by using `create` method on node.
    
        * if subnode (subtree) is found, return that subtree (Data), so you need to call `get` first then you can use `create` / `insert` etc. just like you do on the root `node` object. quick recap: modb.low.VirtualBNode is the key to my database implementation.


