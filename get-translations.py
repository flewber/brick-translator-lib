#!/usr/bin/env python3
import keys
import rebrick
import json
import time
import csv

REBRICKABLE_SLEEP_DURATION = 10.1

# Part number prefix definitions
REBRICKABLE_PFX = "RB_"
BRICKLINK_PFX = "BL_"
BRICKOWL_PFX = "BO_"
BRICKSET_PFX = "BS_"
LEGO_PFX = "LG_"

REBRICKABLE_SUPPORTED_TRANSLATIONS = [
    ("BrickLink",   BRICKLINK_PFX),
    ("BrickOwl",    BRICKOWL_PFX),
    ("BrickSet",    BRICKSET_PFX),
    ("LEGO",        LEGO_PFX),
]


part_filename = "parts.csv"  # File name
translation_filename = "part_translations.csv"  # File name
fields = []  # Column names
part_rows = []    # Data rows
translation_rows = ["Prefixed Part Numbers"]
total_part_count = 0

# import parts list from downloadable parts.csv
try:
    with open(part_filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)  # Reader object

        fields = next(csvreader)  # Read header
        for row in csvreader:     # Read rows
            part_rows.append(row)

        total_part_count = csvreader.line_num
        # print("Total no. of rows: %d" % total_part_count)  # Row count
except:
    print("%s not found. Download and extract to %s. Downloads found here: https://rebrickable.com/downloads/" % (part_filename,part_filename))
    exit()

# print('Field names are: ' + ', '.join(fields))

# init rebrick module for general reading
rebrick.init(keys.YOUR_REBRICKABLE_API_KEY)

# if translation file exists, pickup where we left off
num_rows = 0
try:
    with open(translation_filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)  # Reader object

        translation_fields = next(csvreader)  # Read header
        for row in csvreader:     # Read rows
            translation_rows.append(row)

        num_rows = csvreader.line_num
        # print("Total no. of rows: %d" % num_rows)  # Row count
        next_part_index = num_rows - 1
    
    
except:
    print("error opening %s. Creating new file." % translation_filename)
    next_part_index = 0

# print(translation_rows[next_part_index])
# print(part_rows[next_part_index])

# # Single piece at a time
# running_part_count = next_part_index
# for row in part_rows[next_part_index:]:
#     part_num = row[0]
#     # print(part_num)
#     # get part info (including other website mappings)
#     response = rebrick.lego.get_part(part_num)
#     response_json = json.loads(response.read())
#     # print(response_json)
#     new_row = [part_num, response_json['external_ids']]
#     print(new_row)
#     # print('/n')
#     translation_rows.append(new_row)
#     running_part_count+=1
#     if(running_part_count % 100 == 0):
#         with open(translation_filename, 'w', newline='') as file:
#             print("wrote %d/%d part translations to: %s" % (running_part_count, total_part_count, translation_filename))
#             writer = csv.writer(file)
#             writer.writerows(translation_rows)
#             file.close()
#     time.sleep(REBRICKABLE_SLEEP_DURATION)



# bulk batches
BATCH = 100
last_api_time = 0
query = []
running_part_count = next_part_index
for row in part_rows[next_part_index:]:
    query.append(row[0])
    running_part_count+=1

    # every BATCH parts, query api, and write to translation file
    if(running_part_count % BATCH == 0):
        # don't call API more often then once every REBRICKABLE_SLEEP_DURATION seconds
        time_diff = time.time() - last_api_time
        if(time_diff < REBRICKABLE_SLEEP_DURATION):
            # print(f"sleeping: {REBRICKABLE_SLEEP_DURATION - time_diff:.2}s")
            time.sleep(REBRICKABLE_SLEEP_DURATION - time_diff)
        last_api_time = time.time()

        # get bulk part info (including other website mappings)
        response = rebrick.lego.get_parts(part_ids=query)
        response_json = json.loads(response.read())
        response_count = response_json['count']
        if(response_count<BATCH):
            print("Warning: API response part count was: %d. Expected: %d" % (response_count, BATCH))

        # parse out the website mappings specifically
        for response in response_json['results']:
            # print(response['part_num'])# + str(response['external_ids']))
            new_row = []
            # Rebrickable Part Numbers
            rebrickable = REBRICKABLE_PFX + response['part_num']
            # print("Rebrickable = %s" % rebrickable)
            new_row.append(rebrickable)

            # All other part numbers
            external_ids = response['external_ids']
            # print(external_ids)
            for translation in REBRICKABLE_SUPPORTED_TRANSLATIONS:
                try:
                    group = external_ids[translation[0]]
                    for part in group:
                        # print(translation[1] + part)
                        new_row.append(translation[1] + part)
                except:
                    # print("no %s Parts" % translation[0])
                    None
                
            # print(new_row)
            translation_rows.append(new_row)

        # write mappings to file often in case program gets interrupted
        with open(translation_filename, 'w', newline='') as file:
            print("wrote %d/%d part translations to: %s" % (running_part_count, total_part_count, translation_filename))
            writer = csv.writer(file)
            writer.writerows(translation_rows)
            file.close()
        query = []

# write remaining parts to file
response = rebrick.lego.get_parts(part_ids=query)
response_json = json.loads(response.read())
print("row count: %d" % response_json['count'])
for response in response_json['results']:
    new_row = [response['part_num'], response['external_ids']]
    translation_rows.append(new_row)
with open(translation_filename, 'w', newline='') as file:
    print("wrote %d/%d part translations to: %s" % (running_part_count, total_part_count, translation_filename))
    writer = csv.writer(file)
    writer.writerows(translation_rows)
    file.close()

print("done")



    # print("%10s" % col, end=" ")
    # print('\n')

# for row in rows[5:]:
#     print(row[0])
#     # print("%10s" % col, end=" ")
#     # print('\n')