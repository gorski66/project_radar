# project_radar

The project concerns the creation of an intelligent system for monitoring vehicle traffic on a given road section, which is optimized to work on a low-performance mini-PC. It uses a segmental radar to measure vehicle speeds and a camera to recognize license plates. Vehicle detection is performed by the camera software, allowing for optimal use of hardware resources. The IP camera, an integral part of the vehicle traffic monitoring system, communicates with the server using the FTP (File Transfer Protocol). As a result, images and data collected by the camera are transmitted to the server in an organized and secure manner. The license plate identification process is divided into two phases: in the first phase, the image from the camera is used to extract the graphic containing the license plate number, and in the second phase, the actual recognition of the license plate occurs.




Crontab setup proposal:

2,7,17,22,32,37,47,52 * * * * python3 /home/bob/project_radar/find_plate_number/main.py /home/bob/project_radar/cut_plate_from_picture/images/ /home/bob/project_radar/find_plate_number/results.json

*/3 * * * * python3 /home/bob/project_radar/cut_plate_from_picture/licenseplate.py

In this case, licenseplate.py is executed every 3 minutes (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57), while main.py runs at the 2nd and 7th minute of each quarter hour (2, 7, 17, 22, 32, 37, 47, 52). This ensures that both programs are not run at the same time.
