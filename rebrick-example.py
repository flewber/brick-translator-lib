#!/usr/bin/env python3
import keys

import rebrick
import json

# init rebrick module for general reading
rebrick.init(keys.YOUR_REBRICKABLE_API_KEY)

# get set info
# response = rebrick.lego.get_set(6608)
# print(json.loads(response.read()))

# get part info (including other website mappings)
# response = rebrick.lego.get_part(3001)
# print(json.loads(response.read()))

#get part info based on non-rebrickable id:
# response = rebrick.lego.get_parts(bricklink_id = "20377c00pb04")
# print(json.loads(response.read()))
# response = rebrick.lego.get_parts(brickowl_id = "355765")
# print(json.loads(response.read()))
# response = rebrick.lego.get_parts(lego_id = "20379")
# print(json.loads(response.read()))

#get a batch of parts at once:
response = rebrick.lego.get_parts(part_ids=["20379c01dummy","20379c01pr0001","20379c01pr0002","20379c01pr0003","20379c01pr0004","20379c01pr0005","20379c01pr0006","20379c01pr0007","20379c01pr0008","20379c01pr0109"])
print(json.loads(response.read()))


# init rebrick module including user reading
# rebrick.init("your_API_KEY_here", "your_USER_TOKEN_here")

# if you don't know the user token you can use your login credentials
# rebrick.init("your_API_KEY_here", "your_username_here", "your_password_here")

# get user partlists
# response = rebrick.users.get_partlists()
# print(json.loads(response.read()))