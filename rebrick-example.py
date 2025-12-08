#!/usr/bin/env python3
import keys

import rebrick
import json

# init rebrick module for general reading
rebrick.init(keys.YOUR_REBRICKABLE_API_KEY)

# get set info
response = rebrick.lego.get_set(6608)
print(json.loads(response.read()))

# get part info (including other website mappings)
response = rebrick.lego.get_part(3001)
print(json.loads(response.read()))

# init rebrick module including user reading
# rebrick.init("your_API_KEY_here", "your_USER_TOKEN_here")

# if you don't know the user token you can use your login credentials
# rebrick.init("your_API_KEY_here", "your_username_here", "your_password_here")

# get user partlists
# response = rebrick.users.get_partlists()
# print(json.loads(response.read()))