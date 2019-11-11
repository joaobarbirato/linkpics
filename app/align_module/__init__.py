def _treat_raw_text(text):
    """
    :type text: str
    """
    return text.replace(" -LRB- ", " (") \
        .replace(" -RRB- ", ") ") \
        .replace(" `` ", " \"") \
        .replace("'' ", "\" ") \
        .replace(" ,", ", ") \
        .replace(" .", ". ") \
        .replace("--", '-') \
        .replace("  ", " ")

