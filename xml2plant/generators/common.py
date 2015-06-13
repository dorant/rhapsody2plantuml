def quote_if_space(string):
    if " " in string:
        return '"%s"' % (string)
    else:
        return string

def quote_if_text(string):
    if len(string) > 0:
        return '"%s"' % (string)
    else:
        return string
