from rapidfuzz.fuzz import ratio

def normalize(s):
    return " ".join(str(s).lower().strip().split())

def similarity(a, b):
    return round(ratio(normalize(a), normalize(b)), 2)
