# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

import re

def add_intl(template_string):
    """Wraps the language specific text in an html mako template in the
    proper get text formatting.

    template_string -- The string to convert.

    returns The converted string
    """
    analyze = [template_string]
    # An array of patterns that should be ignored
    # when adding the get text function.
    # Warning order is important!!!
    to_ignore = [
            r'<script.*?>.*?</script>',
            r'<style.*?>.*?</style>',
            r'<!--.*?-->',
            r"% if.*?:",
            r"% elif.*?:",
            r"% else.*?:",
            [r'<input.*?(?<=[^%])>',
                [r'(?:title|alt)=[\'"](.*?)[\'"]', r'^.*[=<>%]+.*$']],
            [r'<area.*?(?<=[^%])>',
                [r'(?:title|alt)=[\'"](.*?)[\'"]', r'^.*[=<>%]+.*$']],
            [r'<option.*?(?<=[^%])>',
                [r'(?:title|alt)=[\'"](.*?)[\'"]', r'^.*[=<>%]+.*$']],
            r'<%doc>.*?</%doc>',
            r'&nbsp;',
            r'checked\\',
            r'selected\\',
            r'display: none;\\',
            r"</?[^>]+>",
            r"</?[^>]+\\",
            r" onclick=.?>",
            r"\r?\n",
            r"\"",
            r"\\",
            r'^\s+',
            r'^\s*% .*',
            r"\$\{.*?\}",
            r'^\s+$'
           ]
    # Convert the array of IgnoredSections and strings to a array
    # of just strings with the non ignored ones wrapped in the gettext
    # formatting
    analyze = isolate_strings(to_ignore, analyze)

    def flatten_string(res, cur_str):
        if isinstance(cur_str, IgnoredSection):
            res.append(cur_str.val)
        else:
            res.append('${ _("%s") }' % cur_str)
        return res
    res_array = reduce(flatten_string, analyze, [])
    # character clean up.
    res_string = "".join(res_array).replace('${ _(">") }', '>').replace('${ _("/>") }','/>')
    res_string = res_string.replace('${ _(" ', ' ${ _("').replace(' ") }','") } ')
    res_string = res_string.replace('${ _("(") }', '(').replace('${ _(")") }', ')')
    res_string = res_string.replace('${ _("(', '(${ _("').replace(')") }', '") })')
    res_string = res_string.replace('${ _(":") }', ':').replace('${ _("*") }', '*')
    res_string = res_string.replace('${ _("-") }', '-').replace('${ _("%") }', '%')
    res_string = res_string.replace('${ _("[") }', '[').replace('${ _("]") }', ']')
    res_string = res_string.replace('${ _("|") }', '|')
    return res_string

def isolate_strings(to_ignore, analyze):
    """Takes the array of reg_ex's in to_ignore and applies them
    to the analyze array in a loop. When matches are found the array
    is split and the matched portion is replaced with an IgnorableSection
    object.

    to_ignore -- An array of regular expressions to match on. If this array
        contains an array as an element, than the first element of the contained
        array is the expression to match on, and the second element should
        contain an array which will be used for a recursive call to
        isolate_strings. The recursive call will only traverse the matched
        portion of the string.
        Important: The regular expressions in this array are applied in order!
    analyze -- An array of strings and IgnorableSection objects that is being
        processed. Each string will be checked against the to_ignore expressions
        to see if part of it can itself be ignored.

    returns An array of strings and Ignorable section objects.
    """
    for regex in to_ignore:
        def analyze_string(analyze_list, cur_str):
            if not isinstance(cur_str, IgnoredSection):
                sec_ex = None
                pri_ex = regex
                if type(pri_ex).__name__ == 'list':
                    pri_ex = regex[0]
                    sec_ex = regex[1]
                matches = analyze_matches(pri_ex, cur_str, sec_ex)
                for item in matches:
                    analyze_list.append(item)
            else:
                analyze_list.append(cur_str)
            return analyze_list

        analyze = reduce(analyze_string, analyze, [])
    return analyze

def analyze_matches(regex, string, sec_exs=None):
    """Splits the string based on the regex and returns a list containing the
    split string along with the matched tokes as IgnoredSection objects.

    regex -- The regular expression pattern to match on.
    string -- The string to analyze

    example:
        analyze_matches("\n", "test\nstring")
                -> ["test", IgnoredSection("\n"), "string"]
    """
    analyzed_list = []
    cur_index = 0
    for match in re.finditer(regex, string, (re.M | re.S)):
        #Split in around the matches and set the matches to ignore
        start = match.start()
        end = match.end()
        if(cur_index != start):
            analyzed_list.append(string[cur_index:start])

        if sec_exs is None:
            _analyze_groups(match, analyzed_list)
        else:
            analyzed_list += isolate_strings(sec_exs, [match.group(0)])
        cur_index=end

    if cur_index != len(string):
        analyzed_list.append(string[cur_index:len(string)])
    return analyzed_list

def _analyze_groups(match, analyzed_list):
    """Takes the match object and appends it to the list as an IgnoredSection,
    however any capturing groups specified in the match will instead be appended
    as a normal string.

    match -- The match object
    analyzed_list -- The list to append to.
    """
    group_str = match.group(0)
    cur_index = 0
    group_index = 1
    for group in match.groups():
        start = match.start(group_index)-match.start()
        end = match.end(group_index)-match.end()
        if(cur_index != start):
            analyzed_list.append(IgnoredSection(group_str[cur_index:start]))

        analyzed_list.append(group_str[start:end])
        cur_index=end
        group_index += 1

    if cur_index != len(group_str):
        ignore = group_str[cur_index:len(group_str)]
        analyzed_list.append(IgnoredSection(ignore))
    return analyzed_list


class IgnoredSection(object):
    """Class used as a place holder for regions in the document that do not need
    to be wrapped with the get_text function.
    """
    def __init__(self, val):
        self.val = val
