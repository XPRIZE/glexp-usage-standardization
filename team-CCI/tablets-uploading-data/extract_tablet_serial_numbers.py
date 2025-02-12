# Extracts tablet serial numbers from log files collected from tablets, and stores them in a standardized format.
#
# Example usage:
#     cd tablets-uploading-data
#     python3 extract_tablet_serial_numbers.py ../tablet-usage-data/2019-03-01
#
# The extracted data will be stored in a file named `tablets-uploading-data-CCI_<DATE>.csv`.

import sys
import datetime
import os
import warnings
import glob
import ntpath
import csv
import base64

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
            village_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
            village_id = int(village_id_dir_entry.name)
            print(os.path.basename(__file__), "village_id: {}".format(village_id))
            if village_id not in village_ids:
                warnings.warn("village_id not in village_ids: {}".format(village_id))
                continue

            # Add each extracted tablet serial number to an array
            tablet_serials = []

            # Iterate all subdirectories and files contained within the village ID directory
            print(os.path.basename(__file__), "Iterating all subdirectories and files for village_id " + str(village_id) + ": \"{}/**/*\"".format(village_id_dir_entry.path))
            for file_path in glob.iglob(village_id_dir_entry.path + "/**/*", recursive=True):
                print(os.path.basename(__file__), "file_path: {}".format(file_path))

                # Expect the following directory structure:
                #  - "2019-03-01/4/REMOTE/NjExMjAwMTE2Ni0xLS9hbmRyb2lkX2Fzc2V0L3d3dy9zY2hvb2wvdHV0b3JpYWxzL1N3SG93VG8vaW5kZXguaHRtbC1hbmFseXRpY3MtOTQ3MzEzNTk4MDEw.json"
                #  - "2019-01-18/8/REMOTE/NjExMjAwMDAxNy0xLS9hbmRyb2lkX2Fzc2V0L3d3dy9zY2hvb2wvRXBpYyUyMFF1ZXN0L3VuaXQtRXBpY1F1ZXN0LUJvb2tzLUJvb2tzLUVRX0IxX1BldHJvcy5odG1sLWFuYWx5dGljcy0xNTQ3MTUzNjUxNjY5-Copy.json"

                # Skip if the current item is a directory
                if os.path.isdir(file_path):
                    # warnings.warn("os.path.isdir(file_path): {}".format(file_path))
                    continue

                # Get the filename, e.g. "NjExMjAwMTE2Ni0xLS9hbmRyb2lkX2Fzc2V0L3d3dy9zY2hvb2wvdHV0b3JpYWxzL1N3SG93VG8vaW5kZXguaHRtbC1hbmFseXRpY3MtOTQ3MzEzNTk4MDEw.json"
                basename = ntpath.basename(file_path)
                print(os.path.basename(__file__), "basename: \"{}\"".format(basename))

                # Remove filename extension before decoding from Base64
                # E.g. "NjExMjAwMTE2Ni0xLS9hbmRyb2lkX2Fzc2V0L3d3dy9zY2hvb2wvdHV0b3JpYWxzL1N3SG93VG8vaW5kZXguaHRtbC1hbmFseXRpY3MtOTQ3MzEzNTk4MDEw.json" --> ""NjExMjAwMTE2Ni0xLS9hbmRyb2lkX2Fzc2V0L3d3dy9zY2hvb2wvdHV0b3JpYWxzL1N3SG93VG8vaW5kZXguaHRtbC1hbmFseXRpY3MtOTQ3MzEzNTk4MDEw"
                # or "NjExMjAwMDAxNy0xLS9hbmRyb2lkX2Fzc2V0L3d3dy9zY2hvb2wvRXBpYyUyMFF1ZXN0L3VuaXQtRXBpY1F1ZXN0LUJvb2tzLUJvb2tzLUVRX0IxX1BldHJvcy5odG1sLWFuYWx5dGljcy0xNTQ3MTUzNjUxNjY5-Copy.json" --> "NjExMjAwMDAxNy0xLS9hbmRyb2lkX2Fzc2V0L3d3dy9zY2hvb2wvRXBpYyUyMFF1ZXN0L3VuaXQtRXBpY1F1ZXN0LUJvb2tzLUJvb2tzLUVRX0IxX1BldHJvcy5odG1sLWFuYWx5dGljcy0xNTQ3MTUzNjUxNjY5"
                filename_without_extension = basename.replace("-Copy.json", "")
                filename_without_extension = filename_without_extension.replace(".json", "")
                print(os.path.basename(__file__), "filename_without_extension: \"{}\"".format(filename_without_extension))

                # Decode from Base64
                decoded_value_as_bytes = base64.b64decode(filename_without_extension)
                print(os.path.basename(__file__), "decoded_value_as_bytes: \"{}\"".format(decoded_value_as_bytes))

                # Convert from bytes to String
                # Expected format: "6112001166-1-/android_asset/www/school/tutorials/SwHowTo/index.html-analytics-947313598010"
                decoded_value = decoded_value_as_bytes.decode("utf-8")
                print(os.path.basename(__file__), "decoded_value: \"{}\"".format(decoded_value))

                # Extract tablet serial from decoded filename
                tablet_serial = decoded_value[0:10]
                print(os.path.basename(__file__), "tablet_serial: \"{}\"".format(tablet_serial))

                # Skip if the current filename does not contain a valid tablet serial number
                is_valid_tablet_serial_number = serial_number_util.is_valid(tablet_serial)
                print(os.path.basename(__file__), "is_valid_tablet_serial_number: {}".format(is_valid_tablet_serial_number))
                if not is_valid_tablet_serial_number:
                    raise ValueError("Invalid tablet_serial: \"{}\"".format(tablet_serial))
                elif tablet_serial not in tablet_serials:
                    tablet_serials.append(tablet_serial)

            # Sort tablet_serials by value (ascending)
            tablet_serials = sorted(tablet_serials)

            csv_row = ['CCI', village_id, date, len(tablet_serials), tablet_serials]
            print("Adding CSV row: {}".format(csv_row))
            csv_rows.append(csv_row)

        # Define columns
        csv_fieldnames = ['team', 'village_id', 'week_end_date', 'tablet_serials_count', 'tablet_serials']

        # Sort rows by village_id (2nd column)
        csv_rows = sorted(csv_rows, key=lambda x: x[1])

        # Export to a CSV file
        csv_filename = "tablets-uploading-data-CCI_" + date + ".csv"
        print("Writing tablet serials to the file \"" + csv_filename + "\"")
        with open(csv_filename, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, csv_fieldnames)
            csv_writer.writerow(csv_fieldnames)
            csv_writer.writerows(csv_rows)


if __name__ == "__main__":
    # Only run when not called via "import" in another file

    print(os.path.basename(__file__), "sys.version: {}".format(sys.version))

    # Expect an argument representing a directory containing one week of data, e.g. "../tablet-usage-data/2019-03-01"
    if len(sys.argv) < 2:
        # Abort execution
        exit("Directory argument missing. Example usage: python3 extract_tablet_serial_numbers.py ../tablet-usage-data/2019-03-01")
    dir_containing_weekly_data = sys.argv[1]
    print(os.path.basename(__file__), "dir_containing_weekly_data: \"{}\"".format(dir_containing_weekly_data))

    extract_from_week(dir_containing_weekly_data)
