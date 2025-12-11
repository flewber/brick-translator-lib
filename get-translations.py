#!/usr/bin/env python3
import keys
import rebrick
import json
import time
import csv

REBRICKABLE_SLEEP_DURATION = 1.1

part_filename = "parts.csv"  # File name
translation_filename = "part_translations.csv"  # File name
fields = []  # Column names
part_rows = []    # Data rows
translation_rows = ['rebrickable_part_num, non_rebrickable_part_num(s)']
total_part_count = 0

with open(part_filename, 'r') as csvfile:
    csvreader = csv.reader(csvfile)  # Reader object

    fields = next(csvreader)  # Read header
    for row in csvreader:     # Read rows
        part_rows.append(row)

    total_part_count = csvreader.line_num
    print("Total no. of rows: %d" % total_part_count)  # Row count
    csvfile.close()

print('Field names are: ' + ', '.join(fields))

# init rebrick module for general reading
rebrick.init(keys.YOUR_REBRICKABLE_API_KEY)

# print('\nFirst 5 rows are:\n')
# for row in part_rows[:5]:
#     for col in row:
#         print("%10s" % col, end=" ")
#     print('\n')

#pickup where we left off
num_rows = 0
try:
    with open(translation_filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)  # Reader object

        translation_fields = next(csvreader)  # Read header
        for row in csvreader:     # Read rows
            translation_rows.append(row)

        num_rows = csvreader.line_num
        print("Total no. of rows: %d" % num_rows)  # Row count
        next_part_index = num_rows - 1
    
    
except:
    print("exception")
    next_part_index = 0

# print(translation_rows[next_part_index])
# print(part_rows[next_part_index])




# print('\nLast 5 rows are:\n')
# for row in rows[-5:]:
running_part_count = next_part_index
for row in part_rows[next_part_index:]:
    part_num = row[0]
    # print(part_num)
    # get part info (including other website mappings)
    response = rebrick.lego.get_part(part_num)
    response_json = json.loads(response.read())
    # print(response_json)
    new_row = [part_num, response_json['external_ids']]
    print(new_row)
    # print('/n')
    translation_rows.append(new_row)
    running_part_count+=1
    if(running_part_count % 100 == 0):
        with open(translation_filename, 'w', newline='') as file:
            print("wrote %d/%d part translations to: %s" % (running_part_count, total_part_count, translation_filename))
            writer = csv.writer(file)
            writer.writerows(translation_rows)
            file.close()
    time.sleep(REBRICKABLE_SLEEP_DURATION)

print("done")



    # print("%10s" % col, end=" ")
    # print('\n')

# for row in rows[5:]:
#     print(row[0])
#     # print("%10s" % col, end=" ")
#     # print('\n')