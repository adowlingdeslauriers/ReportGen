import json
import csv
from appJar import gui

def create_ACE_manifest():
    #load csv
    try:
        batches_file_path = app.getEntry("batches_file_entry")
        with open(batches_file_path, "r") as batches_file:
            csv_reader = csv.reader(batches_file, delimiter = ",")
            batches_data = []
            for row in csv_reader:
                if not "#" in row: # If the row isn't a comment
                    batches_data.append(row)
    except:
        print("Error loading batches .csv")

    # load json
    try:
        json_file_path = app.getEntry("json_file_entry")
        with open(json_file_path, "r") as json_file:
            json_data = json.load(json_file)
    except:
        print("Error loading .json data")

    #compare lists and build outputs
    good_json = []
    bad_json = []
    good_batches = []
    bad_batches = []

    for json_entry in json_data:
        for row in batches_data:
            if json_entry["BATCHID"] == row[0] or json_entry["ORDERID"] == row[0]:
                good_json.append(json_entry)
                good_batches.append(row[0])
                print(f"{row[0]} {row[1]} {json_entry['consignee']['name']}")

    with open("good_ACE.json", "w") as good_json_file:
        json.dump(good_json, good_json_file, indent = 4)
    
    #bad jsons
    for json_entry in json_data:
        if json_entry not in good_json:
            bad_json.append(json_entry)
            print(f"Bad entry: {json_entry['ORDERID']} {json_entry['consignee']['name']}")

    #bad batches
    for row in batches_data:
        if row[0] not in good_batches:
            bad_batches.append(row[0])
            print(f"Bad batch: {row[0]}")

    #move unmatched entry to bad_json and bad_batches

app = gui()
app.addLabel("Batches (.csv):")
app.addFileEntry("batches_file_entry")
app.addLabel("ACE Manifest (.json):")
app.addFileEntry("json_file_entry")
app.addButton("GO", create_ACE_manifest)
app.go()
