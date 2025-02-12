# Extracts storybook events from log files collected from tablets, and stores them in a standardized format.
#
# Example usage:
#     cd storybook-events
#     python3 extract_storybook_events_from_txt.py ../tablet-usage-data/2018-05-25
#
# The extracted data will be stored in a file named `storybook-events-KITKIT_<DATE>.csv`.

import sys
import datetime
import os
import warnings
import glob
import ntpath
import csv
import json
import zipfile

import serial_number_util


def verify_date(date_text):
    print(os.path.basename(__file__), "verify_date")
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect date format. Should be YYYY-mm-dd")


def extract_from_week(directory_containing_weekly_data):
    print(os.path.basename(__file__), "extract_from_week")

    # Extract the date (the last 10 characters) from the directory path
    date = directory_containing_weekly_data[len(directory_containing_weekly_data) - 10:len(directory_containing_weekly_data)]
    print(os.path.basename(__file__), "date: \"{}\"".format(date))

    # Verify that the directory name is on the format "YYYY-mm-dd"
    verify_date(date)

    # Iterate each subdirectory
    date_directory_iterator = os.scandir(directory_containing_weekly_data)
    print(os.path.basename(__file__), "date_directory_iterator: {}".format(date_directory_iterator))
    with date_directory_iterator as village_id_dir_entries:
        csv_rows = []

        for village_id_dir_entry in village_id_dir_entries:
            print(os.path.basename(__file__), "village_id_dir_entry: {}".format(village_id_dir_entry))

            # Skip if the current DirEntry is not a directory
            if not village_id_dir_entry.is_dir():
                warnings.warn("not village_id_dir_entry.is_dir(): {}".format(village_id_dir_entry))
                continue

            # Skip if the current Village ID is not valid
            village_ids = [57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85]
            village_id = int(village_id_dir_entry.name)
            print(os.path.basename(__file__), "village_id: {}".format(village_id))
            if village_id not in village_ids:
                warnings.warn("village_id not in village_ids: {}".format(village_id))
                continue

            # Iterate all subdirectories and files contained within the village ID directory
            print(os.path.basename(__file__), "Iterating all subdirectories and files for village_id " + str(village_id) + ": \"{}/**/*\"".format(village_id_dir_entry.path))
            for file_path in glob.iglob(village_id_dir_entry.path + "/**/*", recursive=True):
                print(os.path.basename(__file__), "file_path: {}".format(file_path))

                # Expect the following file structure:
                #  - "2017-12-22/57/remote/5A27001661_log_1.txt"
                #  - "2017-12-22/57/remote/5A27001661_log_2.txt"
                #  - "2018-08-03/80/remote/library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log(1)(1).zip"
                #  - "2018-05-25/57/REMOTE/com_enuma_booktest.6115000540.lastlog.txt"
                #  - "2018-05-25/57/REMOTE/com_enuma_xprize.5A23001564.lastlog.txt"
                #  - "2018-05-25/57/REMOTE/com_enuma_xprize.6116002162.A.log.zip"
                #  - "2018-05-25/57/REMOTE/com_enuma_xprize.6116002162.B1.log.zip"
                #  - "2018-05-25/57/REMOTE/library_todoschool_enuma_com_todoschoollibrary.6111001905.lastlog.txt"
                #  - "2018-05-25/57/REMOTE/todoschoollauncher_enuma_com_todoschoollauncher.5A23001564.lastlog.txt"
                #  - "2018-05-25/59/REMOTE/6114000050_user0.zip"
                #  - "2018-06-22/84/remote/5A28000934_.aux.zip"
                #  - "2018-11-09/83/REMOTE/crashlog.com_enuma_todoschoollockscreen.txt
                #  - "2018-11-09/83/REMOTE/crashlog.library_todoschool_enuma_com_todoschoollibrary.txt

                basename = ntpath.basename(file_path)
                print(os.path.basename(__file__), "basename: \"{}\"".format(basename))

                # Separate log files for each Android app where not introduced until 2018-05-25, so we can expect a
                # different file structure before this date.
                date_of_1st_software_update = datetime.datetime(2018, 5, 25)
                date_as_datetime = datetime.datetime.strptime(date, '%Y-%m-%d')
                if date_as_datetime < date_of_1st_software_update:
                    print(os.path.basename(__file__), "date_as_datetime < date_of_1st_software_update")

                    # Skip if the current file's name does not end with ".txt", e.g. "5A27001661_log_1.txt"
                    if not basename.endswith(".txt"):
                        warnings.warn("Skipping file: \"{}\"".format(basename))
                        continue

                    # Extract the tablet serial number from the filename.
                    # E.g. "5A27001661_log_1.txt" or "5A27001661_log_10.txt"
                    tablet_serial = basename[0:10]
                else:
                    print(os.path.basename(__file__), "date_as_datetime >= date_of_1st_software_update")

                    # Skip if the current file's name does not start with "library_todoschool_enuma_com_todoschoollibrary.",
                    # e.g. "library_todoschool_enuma_com_todoschoollibrary.6129002346.lastlog.txt" or
                    # "library_todoschool_enuma_com_todoschoollibrary.6118002503.A.log.zip"
                    if not basename.startswith("library_todoschool_enuma_com_todoschoollibrary."):
                        warnings.warn("Skipping file: \"{}\"".format(basename))
                        continue

                    # Extract the tablet serial number from the filename
                    # E.g. "library_todoschool_enuma_com_todoschoollibrary.6111001905.lastlog.txt" or
                    # "library_todoschool_enuma_com_todoschoollibrary.6118002503.A.log.zip"
                    tablet_serial = basename[47:57]

                # Skip if the filename does not contain a valid tablet serial number
                is_valid_tablet_serial_number = serial_number_util.is_valid(tablet_serial)
                print(os.path.basename(__file__), "is_valid_tablet_serial_number: {}".format(is_valid_tablet_serial_number))
                if not is_valid_tablet_serial_number:
                    raise ValueError("Invalid tablet_serial: \"{}\"".format(tablet_serial))

                # If ZIP, unzip file. E.g. "library_todoschool_enuma_com_todoschoollibrary.6118002503.A.log.zip".
                # Expect the ZIP file to contain only one file, and with the same name as the ZIP file itself
                # (but with ".log.txt" extension instead of ".log.zip").
                unzipped_file_to_be_deleted = None
                if basename.endswith(".zip"):
                    print(os.path.basename(__file__), "Unzipping: {}".format(file_path))
                    try:
                        zip_file = zipfile.ZipFile(file_path)
                    except zipfile.BadZipFile:
                        # Handle "zipfile.BadZipFile: Bad magic number for central directory"
                        # Example: 2018-07-27/78/REMOTE/library_todoschool_enuma_com_todoschoollibrary.6118002322.A.log.zip
                        warnings.warn("zipfile.BadZipFile. Skipping bad ZIP file (zipfile.ZipFile(file_path)): {}".format(file_path))
                        continue
                    with zip_file as zip_ref:
                        # Extract log file temporarily to the storybook-events/ directory
                        try:
                            zip_ref.extractall()
                        except zipfile.BadZipFile:
                            # Handle "zipfile.BadZipFile: Bad magic number for file header"
                            # Example: 2018-06-22/62/REMOTE/remote/library_todoschool_enuma_com_todoschoollibrary.6118002087.B1.log.zip
                            warnings.warn("zipfile.BadZipFile. Skipping bad ZIP file (zip_ref.extractall()): {}".format(file_path))
                            continue
                        except OSError:
                            # Handle "OSError: [Errno 22] Invalid argument"
                            # Example: 2018-11-02/62/REMOTE/remote/library_todoschool_enuma_com_todoschoollibrary.6118001612.C16.log.zip
                            warnings.warn("OSError. Unzipping failed. Skipping file.")
                            continue

                        # Update the path of the current file so that it points to the unzipped file instead of the ZIP file.
                        # E.g. "library_todoschool_enuma_com_todoschoollibrary.6118002087.B1.log.zip" -->
                        #      "library_todoschool_enuma_com_todoschoollibrary.6118002087.B1.log.txt"
                        # or   "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log(1)(1).zip" -->
                        #      "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log.txt"
                        # or   "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log_(1).zip" -->
                        #      "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log.txt"
                        # or   "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log_(1)_(1).zip" -->
                        #      "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log.txt"
                        file_path = basename
                        file_path = file_path.replace(".log.zip", ".log.txt")
                        file_path = file_path.replace(".log(1)(1).zip", ".log.txt")
                        file_path = file_path.replace(".log_(1).zip", ".log.txt")
                        file_path = file_path.replace(".log_(1)_(1).zip", ".log.txt")
                        print(os.path.basename(__file__), "file_path: {}".format(file_path))
                        unzipped_file_to_be_deleted = file_path

                # Skip if the filename extension is not ".txt" nor ".zip".
                # In some cases, a file contains "(1)" or "(1)(1)" in the filename (with or without spaces), which caused
                # files to be copied with a wrong file extension. E.g. "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log(1)(1).zip"
                # --> "library_todoschool_enuma_com_todoschoollibrary.6111000373.A.log". This left a file with the
                # extension ".log", even though it's actuallty a ZIP file, thus causing an error when calling `with open(file_path) as txt_file`:
                # "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xdd in position 97: invalid continuation byte".
                # In this case, skip the file.
                if basename.endswith(".log"):
                    warnings.warn("Skipping unexpected .log filename")
                    continue

                with open(file_path) as txt_file:
                    for txt_line in txt_file:
                        # Look for lines containing "action":"start_book"
                        if "start_book" in txt_line:
                            print(os.path.basename(__file__), "file_path: {}".format(file_path))
                            print(os.path.basename(__file__), "txt_line: {}".format(txt_line))
                            # Extract storybook event from JSON object
                            # Example: {"appName":"library.todoschool.enuma.com.todoschoollibrary","timeStamp":1483935746,"event":{"category":"library","action":"start_book","label":"sw_216","value":0},"user":"user0"}
                            try:
                                json_object = json.loads(txt_line)
                            except json.decoder.JSONDecodeError:
                                # In some cases, a row of JSON data may end abruptly.
                                # Example: {"category":"library","action":"start_video","label":"B"
                                warnings.warn("JSON decoding failed")
                                continue

                            json_object_event = json_object["event"]
                            print(os.path.basename(__file__), "json_object_event: {}".format(json_object_event))

                            # label (e.g. "sw_216")
                            label = json_object_event["label"]
                            storybook_id = label[3:len(label)]

                            # timeStamp (e.g. 1483935746)
                            timestamp = json_object["timeStamp"]
                            storybook_start_time = timestamp

                            # Storybook end time is not stored, so set to None
                            # TODO: can "action":"finish_read" events be linked to "action":"start_book" events for the same book ID?
                            storybook_end_time = None

                            csv_row = [tablet_serial, storybook_id, storybook_start_time, storybook_end_time]
                            if csv_row not in csv_rows:
                                print(os.path.basename(__file__), "Adding CSV row: {}".format(csv_row))
                                csv_rows.append(csv_row)

                    txt_file.close()

                    # If the file was unzipped, delete it.
                    print(os.path.basename(__file__), "unzipped_file_to_be_deleted: {}".format(unzipped_file_to_be_deleted))
                    if unzipped_file_to_be_deleted is not None:
                        # Delete the unzipped file
                        os.remove(unzipped_file_to_be_deleted)

        # Define columns
        csv_fieldnames = ['tablet_serial', 'storybook_id', 'start_time', 'end_time']

        # Sort rows by tablet_serial (1st column), start_time (3rd column)
        csv_rows = sorted(csv_rows, key=lambda x: (x[0], x[2]))

        # Export to a CSV file
        csv_filename = "storybook-events-KITKIT_" + date + ".csv"
        print("Writing storybook events to the file \"" + csv_filename + "\"")
        with open(csv_filename, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, csv_fieldnames)
            csv_writer.writerow(csv_fieldnames)
            csv_writer.writerows(csv_rows)


if __name__ == "__main__":
    # Only run when not called via "import" in another file

    print(os.path.basename(__file__), "sys.version: {}".format(sys.version))

    # Expect an argument representing a directory containing one week of data, e.g. "../tablet-usage-data/2018-05-25"
    if len(sys.argv) < 2:
        # Abort execution
        exit("Directory argument missing. Example usage: python3 extract_storybook_events_from_txt.py ../tablet-usage-data/2018-05-25")
    dir_containing_weekly_data = sys.argv[1]
    print(os.path.basename(__file__), "dir_containing_weekly_data: \"{}\"".format(dir_containing_weekly_data))

    extract_from_week(dir_containing_weekly_data)
