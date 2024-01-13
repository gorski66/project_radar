# project_radar


Propozycja ustawienia crontab:

*/3 * * * * python3 /ścieżka/do/licenseplate.py

2,7,17,22,32,37,47,52 * * * * python3 /path/to/main.py ~/project_radar/cut_plate_from_picture/images/ results.json

W tym przypadku, licenseplate.py uruchamia się co 3 minuty (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57), podczas gdy main.py uruchamia się o 2 i 7 minutę każdego kwadransa (2, 7, 17, 22, 32, 37, 47, 52). Zapewnia to, że oba skrypty nie będą uruchamiane w tym samym czasie
