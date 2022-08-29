import re


__all__ = [
    "dotify",
    "pascalify",
    "snakify",
    "synify",
]


def dotify(s):
    s = ".".join(w.lower() for w in s.split(":"))
    # DEV: file:bytes.seen -> file.bytes._seen
    s = s.replace("..", "._")
    return s


def pascalify(s):
    return "".join(w.title() for w in s.split(":"))


def snakify(s):
    return "_".join(w.lower() for w in s.replace(".", "_").split(":"))


def synify(s):
    # Requires 3.7+
    # DEV: Handle special case where IPv4 has multiple contiguous capital
    #      letters.
    s = s.replace("IP", "Ip")
    return ":".join(w.lower() for w in re.split("(?=[A-Z])", s) if w)
