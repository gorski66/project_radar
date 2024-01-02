import argparse
import json
from pathlib import Path
import re
import cv2
import mysql.connector
import datetime
from license_plate_processing import recognize_license_plate, get_chars_contour, train_classifier, train_KNN

def extract_timestamp_from_filename(filename):
    # Extracts timestamp from filenames like 'final_20231217153228_balice.jpg'
    match = re.search(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})_(\w+)', filename)
    if match:
        timestamp = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
        additional_info = match.group(7)
        return timestamp, additional_info
    return None, None

def insert_into_database(results):
    try:
        conn = mysql.connector.connect(
            host='192.168.10.150',
            user='sa',
            password='1234',
            database='radar'
        )
        cursor = conn.cursor()
        for combined_key, plate_number in results.items():
            timestamp, location = combined_key.split('_')  # Extract timestamp and location
            timestamp_dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            half_hour_ago = timestamp_dt - datetime.timedelta(minutes=30)

        # Check if a record exists for this plate number within the last half hour
            cursor.execute("SELECT id FROM plates WHERE plate_number_in = %s AND timestamp_in > %s", (plate_number, half_hour_ago))
            row = cursor.fetchone()
            cursor.fetchall()  # Consume any remaining results

            if row and location == 'chrzanow':
            # Update existing record for 'chrzanow'
                update_query = "UPDATE plates SET timestamp_out = %s, location_out = %s, plate_number_out = %s WHERE id = %s"
                cursor.execute(update_query, (timestamp, location, plate_number, row[0]))
                location='NULL'
            elif not row and location == 'balice':
            # Insert new record for 'balice'
                insert_query = "INSERT INTO plates (timestamp_in, location_in, plate_number_in) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (timestamp, location, plate_number))           	 

        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('images_dir', type=str)
    parser.add_argument('results_file', type=str)
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    results_file = Path(args.results_file)

    template_contours = get_chars_contour()
    classifications, flattened_images = train_classifier(template_contours)
    train_KNN(classifications, flattened_images)

    images_paths = sorted([image_path for image_path in images_dir.iterdir() if image_path.name.endswith('.jpg')])
    results = {}

    for image_path in images_paths:
        image = cv2.imread(str(image_path))
        if image is None:
            print(f'Error loading image {image_path}')
            continue

        timestamp, additional_info = extract_timestamp_from_filename(image_path.name)
        if timestamp and additional_info:
    	    results[f"{timestamp}_{additional_info}"] = recognize_license_plate(image)
        else:
            print(f'Could not extract timestamp and additional info from {image_path.name}')	


    with results_file.open('w') as output_file:
        json.dump(results, output_file, indent=4)

    insert_into_database(results)

if __name__ == '__main__':
    main()

