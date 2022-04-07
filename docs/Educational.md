
## Why do we need database

If you look the word `database ` up in your dictionary.

!!! summary "Meaning of *database*"
    an organized set of data that is stored in a computer and can be looked at and used in various ways

That is to say, whenever you need to store something, you need a database. Actually there are many and various ways to store and query. Let me show you a few, first let's do something simple and navie.

### Using plain text

!!! note
    In this example, we are using `csv-like` format, `csv` stands for comma separated value.

First init.
``` title="db.txt"
Name,Description
python,a computer language
english,a human natural language
```

Then we can do some query
```python
with open('db.txt', mode='r') as f:
    contents = f.read()

# construct our database
database = []

rows = contents.split('\n')
for row in rows:
    cells = row.split(',')
    database.append(cells)
    
# now, for example, we want to query 
# the `python` in the first column.

# input variable
query = "python"
col = 0

# output variable
results = []

# do logic part
for record in database:
    if record[col] == query:
        results.append(record)


# display the results
print(results)
```

This is our first naive and simple database implementation, we have pros and cons here.

* Pros
    1. Simple implementation.
    2. Using plain-text, so it's human-readable when you open it with text-editor.

        !!! note
            That is to say, if you send this file to your friend, they're not forced to install anything-else but using `notepad` or `excel` for example directly. note, `excel` can open `csv` extension file directly.

* Cons
    1. The database structure can not store very hierarchical information, only has two-dimensional table for now.

    2. Slow in two ways when data is big

        * `Loading part`, that will take long time. Since every bytes should be read first from your hard drive, that's the bottleneck.

        * `Query part`, the query method we are using take N loops. That'll slow your query speed down dramatically while data is increasing.

### Using `dict`/JSON

Using python dict to store and query your data.

```python title="Build database and do query on it"
database = {
    "head": {
        "name"： "my database",
        "version": 1,
    },
    "body" : {
        "records": [
            {
                "name": "john",
                "online": False,
            },
            {
                "name": "darcy",
                "online": True,
            }
        ]
    }
}

# you can do every operations you learned about `dict` and `list` python type
...
```

```python title="Dump your `dict` to JSON"
import json

with open("db.json", mode="w") as f:
    json.dump(dict, f)
```

```python title="Load your JSON to `dict`"
import json

with open("db.json", mode="r") as f:
    database = json.load(f)

# database dict is available here, you can do query and insert again now.
...

# do not forget to `dump` your updated dict object.
...
```

This JSON way solves one previous problem, where in `csv` format, you can not store hierarchical data structures easily, now you can.

!!! tip
    In fact, this dict-JSON way are being used by a lot of engineers around, you just load and dump, for example, the setting of your software.

* Pros

    1. You can store very hierarchical data structure with ease.
    2. You can manipulate you database `dict` by using python built-in methods.
    3. Really fast access after you load your database json to python `dict`.

* Cons

    1. If the data is big, you still face the problem as in plain-text csv way, the loading time problem.
    2. If the database file can not fit in your RAM, your query speed will be reduced dramatically.
        
        !!! summary
            In fact, if you are using this dict-JSON way, there is no way do get around this, since you can't do something like telling the python, how to load or which things should not be loaded into RAM.


### Using `real` database

To solve the problems we have faced above, we need a thing called `index`. Every database engine should have `index`.


## What is `index`

`index` is a great thing. It allows you to quickly access your targeted value. This `index` in database plays a same role as the `index` in your book. Think about that, when you open a book, then you are looking for something, for example one specific chapter, rather than turning your page one by one, you look for `index` of contents directly, and get that page number.

!!! summary
    ** index is pointers ** which point to the targeted value directly without hesitation.

Let me show you a simple `index` with core concept in it.

```title="index"
1 3 4 6 7 8 10 13 14 18 19 21 24 37 40 45 71
```
The numbers listed above are the keys that user insert, they are already **indexed**, since they are **sorted**.

!!! note
    Every key have a corresponding value, which is not listed above. you can think of number keys as days or something similar that you will insert.


With a sorted list, you can do something called **binary search** to do really really fast query. 

![binarysearch](https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Binary_Search_Depiction.svg/705px-Binary_Search_Depiction.svg.png)

The above image shows you how to find the `7`. From the middle first, then do a comparison, which will tell you **go left** or **go right**, then repeat the same process recursively until you find your targeted number. As the image shows you, only 4 steps are needed. In fact, you can try to find other numbers like `6` o `37`, the result is just the same, fast.



