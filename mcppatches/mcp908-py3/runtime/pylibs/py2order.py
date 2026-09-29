# Python 3 port helper: reproduce the order in which Python 2.7 iterated a dict
# or set of strings.
#
# Python 2.7 dicts and sets iterate in hash-table order; Python 3 dicts iterate
# in insertion order and Python 3 randomizes string hashes. MCP picks "the
# first match" while iterating several dicts, so the order decides what ends up
# in the decompiled and reobfuscated output. MCP 9.08 ships a 32-bit Python 2.7
# (runtime/bin/python/python_mcp.exe), so this uses its 32-bit C long hash.
# Python 2.7 dicts and sets use the same probing and resize rules.


def _py2_str_hash(key):
    b = key.encode('utf-8') if isinstance(key, str) else bytes(key)
    if not b:
        return 0
    x = (b[0] << 7) & 0xFFFFFFFF
    for c in b:
        x = ((1000003 * x) ^ c) & 0xFFFFFFFF
    x ^= len(b) & 0xFFFFFFFF
    if x == 0xFFFFFFFF:  # -1 is reserved for errors
        x = 0xFFFFFFFE
    return x


def py2_dict_order(keys):
    """Return keys (given in first-insertion order) in Python 2.7 iteration order."""
    table, used = [None] * 8, 0

    def insert(tbl, key, h):
        mask = len(tbl) - 1
        i = h & mask
        perturb = h
        while tbl[i & mask] is not None:
            i = ((i << 2) + i + perturb + 1) & 0xFFFFFFFF
            perturb >>= 5
        tbl[i & mask] = (key, h)

    for key in keys:
        insert(table, key, _py2_str_hash(key))
        used += 1
        if used * 3 >= len(table) * 2:
            minused = used * 2 if used > 50000 else used * 4
            size = 8
            while size <= minused:
                size <<= 1
            old, table = table, [None] * size
            for entry in old:
                if entry is not None:
                    insert(table, entry[0], entry[1])
    return [entry[0] for entry in table if entry is not None]
