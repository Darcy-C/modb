
## Why do we need database

If you look the word `database ` up in your dictionary.

!!! summary "Meaning of *database*"
    an organized set of data that is stored in a computer and can be looked at and used in various ways

That is to say, whenever you need to store something, you need a database. Actually there are many and various ways to store and query. Let me show you a few, first let's do something simple and navie.

### `naive` Plain text with `csv-like` format.

!!! note
    `csv` stands for comma separated value.

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
    
# now, # for example, we want to query 
# the `english` in the first coloumn.
query = "python"
results = []

for record in database:
    if record[0] == query:
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
