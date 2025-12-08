#!/usr/bin/env python3
import keys
import rebrick
import json
import time
import csv

REBRICKABLE_SLEEP_DURATION = 1.1

filename = "parts.csv"  # File name
fields = []  # Column names
rows = []    # Data rows

with open(filename, 'r') as csvfile:
    csvreader = csv.reader(csvfile)  # Reader object

    fields = next(csvreader)  # Read header
    for row in csvreader:     # Read rows
        rows.append(row)

    print("Total no. of rows: %d" % csvreader.line_num)  # Row count

print('Field names are: ' + ', '.join(fields))

# init rebrick module for general reading
rebrick.init(keys.YOUR_REBRICKABLE_API_KEY)

print('\nFirst 5 rows are:\n')
for row in rows[:5]:
    for col in row:
        print("%10s" % col, end=" ")
    print('\n')

# print('\nLast 5 rows are:\n')
# for row in rows[-5:]:

for row in rows[:5]:
    part_num = row[0]
    print(part_num)
    # get part info (including other website mappings)
    response = rebrick.lego.get_part(part_num)
    print(json.loads(response.read()))
    print('/n')
    time.sleep(REBRICKABLE_SLEEP_DURATION)



    # print("%10s" % col, end=" ")
    # print('\n')

# for row in rows[5:]:
#     print(row[0])
#     # print("%10s" % col, end=" ")
#     # print('\n')