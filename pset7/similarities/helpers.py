from nltk.tokenize import sent_tokenize


def lines(a, b):
    """Return lines in both a and b"""
    a_lines = set(a.split("\n"))
    b_lines = set(b.split("\n"))
    return a_lines & b_lines


def sentences(a, b):
    """Return sentences in both a and b"""
    a_stn = set(sent_tokenize(a))
    b_stn = set(sent_tokenize(b))
    return a_stn & b_stn


def substring_tokenize(str, n):
    substrings = []

    for i in range(len(str) - n + 1):
        substrings.append(str[i:i + n])

    return substrings


def substrings(a, b, n):
    """Return substrings of length n in both a and b"""
    a_substring = set(substring_tokenize(a, n))
    b_substring = set(substring_tokenize(b, n))
    return a_substring & b_substring
