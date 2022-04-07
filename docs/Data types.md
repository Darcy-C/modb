We have data in database, the stored data must be typed for our convenience.

## Supported types

| Type    | Code | Type in Python          |
| ------- | ---- | ----------------------- |
| String  | 0    | str                     |
| Number  | 1    | float                   |
| Tree    | 2    | `modb.low.VirtualBNode` |
| Empty   | 3    | None                    |
| Boolean | 4    | bool                    |
| Bytes   | 5    | byte                    |

1. The first column is the type class used by modb internally.
2. The second column is the type code used by modb internally to identify the type of the data read in database binary. 

    !!! note "What is type code"
        Your inserted data must be represented as bytes then stored on you file binary. After the data is written as bytes. There should be a type code to help `modb` to indentify the type of the data comes afterwards.

3. The third column is the type you will get when you do `get` on `Data` object. The conversion will be done automatically from `Type` to `Type in Python`. For example, if you insert a str-typed data value, your inserted `str` object will be converted to `modb.format.String`, and vice versa.

    !!! note
        Actually you don't need to care about this type conversion, `modb` will do the conversion automatically for you.


## Layout in binary

!!! note
    A unsigned 8-bit integer will be followed by concrete bytes data, like so
    ```
    type code | Data
    U8        | vary
    ```

### String

Your str-typed object will be encoded using `utf-8` encoding.
```
data length | encoded-string
U32         | vary
```


### Number

Using IEEE 754 binary32 conversion.



