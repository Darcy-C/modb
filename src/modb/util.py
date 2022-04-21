import io

# local imports
import modb.constant


def fill(seq, n, obj):
    len_seq = len(seq)
    if len_seq < n:
        seq += [obj] * (n - len_seq)
    return seq


def f_seek_end(f):
    # note for myself: seek took time to perform too
    return f.seek(0, io.SEEK_END)

def max_array_length(power):
    return 2 ** power

def make_indent(level):
    return modb.constant.INDENT_TEMPLATE * level