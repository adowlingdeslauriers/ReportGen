import json
import csv
import datetime
import sys
from appJar import gui
from reportlab.pdfgen import canvas

def validate_json(in_json):
    out_json = []

# Get rid of duplicates
    for entry in in_json:
        states_list = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "AS", "DC", "FM", "GU", "MH", "MP", "PW", "PR", "VI"]
        #International Orders (shipped to IMS)
        if entry["consignee"]["address"]["country"] != "US":
            entry["consignee"]["address"]["addressLine"] = "2540 Walden Ave Suite 450"
            entry["consignee"]["address"]["country"] = "US"
            entry["consignee"]["address"]["city"] = "Buffalo"
            entry["consignee"]["address"]["stateProvince"] = "NY"
            entry["consignee"]["address"]["postalCode"] = "14225"
        #Name
        if len(entry["consignee"]["name"]) <= 2:
            entry["consignee"]["name"] = entry["consignee"]["name"].ljust(3, "A")
        elif len(entry["consignee"]["name"]) >= 60:
            entry["consignee"]["name"] = entry["consignee"]["name"][:59]
        #Address
        if len(entry["consignee"]["address"]["addressLine"]) <= 2:
            entry["consignee"]["address"]["addressLine"] = entry["consignee"]["address"]["addressLine"].ljust(3, "A")
        elif len(entry["consignee"]["address"]["city"]) >= 55:
            entry["consignee"]["address"]["addressLine"] = entry["consignee"]["address"]["addressLine"][:54]
        #City
        if len(entry["consignee"]["address"]["city"]) <= 3:
            entry["consignee"]["address"]["city"] = entry["consignee"]["address"]["city"].ljust(2, "A")
        elif len(entry["consignee"]["address"]["city"]) >= 30:
            entry["consignee"]["address"]["city"] = entry["consignee"]["address"]["city"][:29]
        #State
        if entry["consignee"]["address"]["stateProvince"] not in states_list:
            entry["consignee"]["address"]["stateProvince"] = "NY"
        #Zip
        if len(entry["consignee"]["address"]["postalCode"]) != 5:
            entry["consignee"]["address"]["postalCode"] = entry["consignee"]["address"]["postalCode"].rjust(5, "0")
        #Check for duplicates
        if entry not in out_json:
            out_json.append(entry)
    return out_json

def create_ACE_manifest():
    print(">Validating Orders")
    
    # File Name
    today = str(datetime.date.today())
    today = app.getEntry("File Name (optional)")
    
    #load csv
    batches_file_path = app.getEntry("batches_file_entry")
    try:
        with open(batches_file_path, "r") as batches_file:
            csv_reader = csv.reader(batches_file, delimiter = ",")
            batches_data = []
            for row in csv_reader:
                if not "#" in row[0] and row[0] != "": # If the row isn't a comment
                    if row[2].upper() == "YES": #3rd column is override for commercially cleared batches
                        batches_data.append((row[0], row[1], "YES"))
                    else:
                        batches_data.append((row[0], row[1], "NO"))
    except:
        print("Error loading batches data")

    # load json
    try:
        json_file_path = app.getEntry("json_file_entry")
        with open(json_file_path, "r") as json_file:
            json_data = json.load(json_file)
    except:
        print("Error loading .json data")

    try:
        blacklist = []
        with open("__BLACKLIST.txt", "r") as blacklist_file:
            lines = blacklist_file.readlines()
            for line in lines:
                if not "#" in line and line[0] != "": # Comments
                    blacklist.append(line.replace("\n", ""))
    except:
        print("Error loading blacklist. Was it moved?")

    #compare lists and build outputs
    good_json = []
    bad_json = []
    good_batches = []
    bad_batches = []
    detailed_report_json = []

    for json_entry in json_data:
        for row in batches_data:
            if json_entry["BATCHID"] == row[0] or json_entry["ORDERID"] == row[0]: #If there's a match
                if row[2] == "YES": #If the product is commercially cleared
                    _json_entry = json_entry
                    _json_entry["GAYLORD"] = row[1]
                    #good_json.append(_json_entry) #Doesn't go on the JSON, only Detailed Report
                    detailed_report_json.append(_json_entry)
                    good_batches.append(row[0])
                else: #If it's not commercially cleared
                    blacklist_match = False
                    for commodity in json_entry["commodities"]: #Check if product is on the blacklist
                        for item in blacklist:
                            if commodity["description"] == item:
                                blacklist_match = True
                                print("Blacklisted commodity found: {} in {}".format(item, json_entry["BATCHID"]))
                                good_batches.append(row[0])
                    if not blacklist_match:
                        _json_entry = json_entry
                        _json_entry["GAYLORD"] = row[1]
                        good_json.append(_json_entry)
                        detailed_report_json.append(_json_entry)
                        good_batches.append(row[0])
    good_json = validate_json(good_json)
    
    file_name = today + "-ACE.json"
    with open(file_name, "w") as good_json_file:
        json.dump(good_json, good_json_file, indent = 4)
    
    #bad jsons
    file_name = today + "-Error_Log.txt"
    with open(file_name, "w") as error_file:
        for json_entry in json_data:
            if json_entry not in detailed_report_json:
                bad_json.append(json_entry)
                #print(f"Unmatched JSON Entry: {json_entry['BATCHID']} {json_entry['consignee']['name']}")
                error_file.write(f"Unmatched JSON Entry: {json_entry['BATCHID']} {json_entry['ORDERID']}\n")

        #bad batches
        for row in batches_data:
            if row[0] not in good_batches and row[2] != "YES":
                bad_batches.append(row[0])
                print(f"Unmatched batch: {row[0]} {row[1]} {row[2]}")
                error_file.write(f"Unmatched batch: {row[0]} {row[1]} {row[2]}\n")

        length = str(len(detailed_report_json))
        error_file.write(f"Outputting {length} entries to Detailed Report")

    #Create Detailed Report
    file_name = today + "-Detailed_Report.csv"
    with open(file_name, "w", newline = "") as report_file:
        csv_writer = csv.writer(report_file)
        csv_writer.writerow(["Gaylord", "Name", "Address", "City", "State", "Country", "Zip Code", "SKUs:"])
        for entry in detailed_report_json:
            out_line = [entry["GAYLORD"], entry["consignee"]["name"], entry["consignee"]["address"]["addressLine"], entry["consignee"]["address"]["city"], entry["consignee"]["address"]["stateProvince"], entry["consignee"]["address"]["country"], entry["consignee"]["address"]["postalCode"]]
            for commodity in entry["commodities"]:
                out_line.append(commodity["description"])
            csv_writer.writerow(out_line)
    #for line in out_text:
    #    print(line)
    
    #PDF Gen
    file_name = today + "-Detailed_Report.pdf"
    c = canvas.Canvas(file_name, pagesize = (841.89, 595.27), bottomup = 0)
    entries = len(detailed_report_json)
    print("Outputting {} entries to Detailed Report".format(str(entries)))
    
    count = 0
    for page in range((entries // 41 + 1)): #Do x/41 times
        c.setFont("Courier", 12)
        for i in range(41):
            if count < entries:
                out = detailed_report_json[count]["GAYLORD"].ljust(4, " ")
                out = out + detailed_report_json[count]["consignee"]["name"][:24].ljust(24, " ")
                out = out + detailed_report_json[count]["consignee"]["address"]["addressLine"][:30].ljust(30, " ")
                out = out + detailed_report_json[count]["consignee"]["address"]["city"][:16].ljust(16, " ")
                out = out + detailed_report_json[count]["consignee"]["address"]["stateProvince"][:3].ljust(3, " ")
                out = out + detailed_report_json[count]["consignee"]["address"]["country"][:3].ljust(3, " ")
                out = out + detailed_report_json[count]["commodities"][0]["description"]
                count = count + 1
                c.drawString(10, (22 + i * 14), out)
        c.showPage()
    c.save()

    print(">Orders validated and Detailed Report created")
    input("Press [Enter] to exit")
    sys.exit(1)

app = gui()
app.addLabel("Batches (.csv):")
app.addFileEntry("batches_file_entry")
app.addLabel("ACE Manifest (.json):")
app.addFileEntry("json_file_entry")
app.addLabelEntry("File Name (optional)")
app.setEntry("File Name (optional)", f"{str(datetime.date.today())}")
app.addButton("GO", create_ACE_manifest)
app.go()
