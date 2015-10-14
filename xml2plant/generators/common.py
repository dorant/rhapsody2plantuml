import re

def quote_restricted_chars(string):
    if re.search('[ :;()-=*?]', string):
        return '"%s"' % (string)
    else:
        return string

def quote_if_text(string):
    if len(string) > 0:
        return ' "%s" ' % (string)
    else:
        return ' '
