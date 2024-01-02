import cv2
import pytesseract
import numpy as np
import os
import re

# configuring pytesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
start = 'balice'
meta = 'chrzanow'

def process_image(image_filename):
    img = cv2.imread(image_filename)
    imgray1 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    canny = cv2.Canny(imgray1, 320, 480)
    contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    for i in contours:
        area = cv2.contourArea(i)
        approx = cv2.approxPolyDP(i, 0.01*cv2.arcLength(i, True), True)
        if len(approx) == 4 and area > 800:
            cv2.drawContours(img, [approx], 0, (0, 255, 0), 2)
            x, y, w, h = cv2.boundingRect(i)
            img4 = imgray1[y:y+h, x:x+w]

    try:
        license_plate = pytesseract.image_to_string(img4, config='--psm 7')
    except:
        print("Could not read the license plate.")
        return
        
    # Extract timestamp from the filename
    filename_parts = os.path.basename(image_filename).split('_')
    timestamp = filename_parts[0]
    additional_text = filename_parts[1].split('.')[0]    

    cv2.putText(img, license_plate, (x-10, y-25), cv2.FONT_ITALIC, 0.8, (0, 255, 0), 2)
    cv2.imwrite('workdir/only_plate.jpg', img4)
    img = cv2.imread('workdir/only_plate.jpg')
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Apply morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph_img = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_DILATE, kernel)

    # Apply Pytesseract OCR
    plate_number_raw = pytesseract.image_to_string(morph_img, config='--psm 8 --oem 3')

    # Post-processing: Remove unwanted characters
    plate_number = plate_number_raw.replace(':', '').strip()

    print("Extracted Plate Number:", plate_number)
    print(plate_number)

    # Save the cropped license plate image
    cv2.imwrite('workdir/cropped_license_plate.jpg', img4)

    # Read the cropped license plate image
    cropped_img = cv2.imread('workdir/cropped_license_plate.jpg')

    # Create a white canvas that is slightly larger than the cropped license plate image
    canvas_height, canvas_width = cropped_img.shape[:2]
    scale_factor = 1.5  # Adjust this factor to control the size of the canvas
    white_canvas = 255 * np.ones((int(2 * scale_factor * canvas_height), int(scale_factor * canvas_width), 3), dtype=np.uint8)

    # Calculate the position to place the original size image on the canvas
    x_offset = (white_canvas.shape[1] - canvas_width) // 2
    y_offset = (white_canvas.shape[0] - canvas_height) // 2

    # Place the original size image on the canvas
    white_canvas[y_offset:y_offset + canvas_height, x_offset:x_offset + canvas_width] = cropped_img

    if not os.path.exists(save_directory):
    	os.makedirs(save_directory)



    # Save the final image
    final_image_filename = f'final_{timestamp}_{additional_text}.jpg'
    full_save_path = os.path.join(save_directory, final_image_filename)
    cv2.imwrite(full_save_path, white_canvas)
    
 
    if os.path.exists(work_directory):
    # Loop through all files in the directory
        for filename in os.listdir(work_directory):
            work_path = os.path.join(work_directory, filename)
        # Remove the file (or remove the directory if it's a directory)
            if os.path.isfile(work_path) or os.path.islink(work_path):
                os.unlink(work_path)
            elif os.path.isdir(work_path):
            # Note: Directory removal is not handled here.
                pass  # or use shutil.rmtree() to remove non-empty directories


# Directory where the images are located
directory = '/srv/ftp/camera/VehicleDetection/'
save_directory = 'images/'
work_directory = 'workdir/'


# Regex pattern for 'date_location.jpg'
pattern = r"\d{14}_\w+\.jpg"

start_files = []
meta_files = []


# Loop through all files in the directory
for filename in os.listdir(directory):
    if re.match(pattern, filename):
        if filename.endswith(start + '.jpg'):  # Check if filename ends with 'balice'
            start_files.append(filename)
        elif filename.endswith(meta + '.jpg'):
            meta_files.append(filename)


def process_files(file_list):
    for filename in file_list:
        file_path = os.path.join(directory, filename)
        process_image(file_path)

# Process 'balice' files first
print("Processing 'balice' files:")
process_files(start_files)

# Then process the rest of the files
print("Processing 'chrzanow' files:")
process_files(meta_files)


