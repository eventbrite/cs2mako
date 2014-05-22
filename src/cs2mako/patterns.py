# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

import re

open_r_str = r'\<\?cs\s*([a-zA-Z]+)([:]|\s)'
close_r_str = r'\<\?cs\s*/([a-zA-Z]+)\s*\?\>'
open_r = re.compile(open_r_str)
close_r = re.compile(close_r_str)
