import json

# Load JSON data from a file
# with open('data.json', 'r') as json_file:
#     data = json.load(json_file)

data = {'set_num': '6608-1', 'name': 'Tractor', 'year': 1982, 'theme_id': 67, 'num_parts': 21, 'set_img_url': 'https://cdn.rebrickable.com/media/sets/6608-1/9875.jpg', 'set_url': 'https://rebrickable.com/sets/6608-1/tractor/', 'last_modified_dt': '2021-07-04T18:43:10.903443Z'}
data2 = {'part_num': '3001', 'name': 'Brick 2 x 4', 'part_cat_id': 11, 'year_from': 1979, 'year_to': 2025, 'part_url': 'https://rebrickable.com/parts/3001/brick-2-x-4/', 'part_img_url': 'https://cdn.rebrickable.com/media/parts/elements/300121.jpg', 'prints': ['3001pr0043', '3001pr0009', '3001pr0016', '3001pr0002', '3001pr0011', '3001pr1042', '3001pr0006', '3001pr1015', '3001pr0010', '3001pr9982', '3001pr9990', '3001pr0033', '3001pr9999', '3001pr0038', '3001pr0013', '3001pr0041', '3001pr0024', '3001pr0028', '3001pr0021', '3001pr0029', '3001pr0119', '3001pr0031', '3001pr0030', '3001pr0040', '3001pr0004', '3001pr0019', '3001pr0037', '3001pr0012', '3001pr0036', '3001pr0027', '3001pr0020', '3001pr0014', '3001pr0015', '3001pr0008', '3001pr0017', '3001pr0042', '3001pr0032', '3001pr0026', '3001pr0025', '3001pr0034', '3001pr0022', '3001pr0044', '3001pr1040', '3001pr1038', '3001pr1039', '3001pr1037', '3001pr1041', '3001pr9991', '3001pr1018', '3001pr1005', '3001pr1020', '3001pr0003', '3001pr1043', '3001pr9992', '3001pr9989', '3001pr1051', '3001pr9988', '3001pr9987', '3001pr9986', '3001pr9985', '3001pr9984', '3001pr9983', '3001pr9981', '3001pr0046', '3001pr0035', '3001pr0023', '3001pr0007', '3001pr0039', '3001pr0001', '3001pr0018', '3001pr0045'], 'molds': ['3001a', '30160', '3556', '3001d', '3001c', '3001b', '3001e'], 'alternates': ['39789', 'upn0041', 'upn0041a', 'upn0041e', 'upn0041d', 'upn0041c', 'upn0041b'], 'external_ids': {'BrickLink': ['3001'], 'BrickOwl': ['771344'], 'Brickset': ['15589', '3001', '54534', '72841'], 'LDraw': ['3001'], 'LEGO': ['15589', '3001', '54534', '72841']}, 'print_of': None}


# Access specific information
print(data['year'])  # Replace 'key' with the actual key you want to access
print(data2['external_ids'])  # Replace 'key' with the actual key you want to access