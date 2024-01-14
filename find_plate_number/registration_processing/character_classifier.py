def get_chars_contour():
    # ścieżka do obrazów znaków
    images_dir = "resources/characters/"
    data_path = os.path.join(images_dir, '*g')
    # pobierz wszystkie pliki ze ścieżki
    files = glob.glob(data_path)

    # słownik do przechowywania konturów każdego znaku
    chars_contour = {}

    # generowanie konturu dla każdego znaku
    for f1 in files:
        # odczytaj obraz znaku
        img_character = cv2.imread(f1, 0)
        # odczytaj, jaki to znak
        letter = re.findall(r"q\w", f1)
        # stwórz obraz krawędzi znaku
        img_letter_edges = cv2.Canny(img_character, 30, 200)
        # znajdź kontur znaku
        contours, hierarchy = cv2.findContours(img_letter_edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # zapisz znaleziony kontur do słownika z kluczem jako znak
        chars_contour[str(letter[0][1])] = contours

    return chars_contour


def train_classifier(chars_contour):
    """
    metoda adaptowana z https://github.com/MicrocontrollersAndMore/OpenCV_3_KNN_Character_Recognition_Python
    """
    # odczytaj obraz treningowy ze wszystkimi znakami
    img_training_chars = cv2.imread("resources/all_characters.jpg")
    # sprawdź, czy obraz został poprawnie odczytany
    if img_training_chars is None:
        print("błąd: nie można odczytać z pliku. Sprawdź ścieżkę do pliku. \n \n")
        os.system("pause")
        return

    # przekonwertuj obraz na skalę szarości
    img_gray = cv2.cvtColor(img_training_chars, cv2.COLOR_BGR2GRAY)

    # progowanie obrazu
    ret, img_thresh = cv2.threshold(img_gray, 150, 255, cv2.THRESH_BINARY_INV)
    # kopia progowanego obrazu, ponieważ findContours modyfikuje obraz
    img_thresh_copy = img_thresh.copy()

    # znajdź kontury dla wszystkich znaków
    npa_contours, npa_hierachy = cv2.findContours(img_thresh_copy,
                                                  cv2.RETR_EXTERNAL,
                                                  cv2.CHAIN_APPROX_SIMPLE)

    # zadeklaruj pustą tablicę numpy. Będzie używana do zapisywania do pliku
    # zero wierszy, wystarczająco kolumn, aby pomieścić wszystkie dane obrazu
    npa_flattened_images = np.empty((0, RESIZED_IMAGE_WIDTH*RESIZED_IMAGE_HEIGHT))

    # zadeklaruj pustą listę klasyfikacji. To lista, jak klasyfikujemy nasze znaki z danych użytkownika
    int_classifications = []

    # dla każdego konturu
    for idx, npa_contour in enumerate(npa_contours):
        # sprawdź, czy kontur jest wystarczająco duży, aby uznać go za znak
        if cv2.contourArea(npa_contour) > MIN_CONTOUR_AREA:
            # pobierz prostokąt otaczający każdy kontur
            [intX, intY, intW, intH] = cv2.boundingRect(npa_contour)

            # wycięcie znaku z progowanego obrazu.
            # Upewnij się, aby wyciąć większy ROI, ponieważ musimy znaleźć kontur znaku

            img_ROI = img_thresh[intY-5:intY+intH+5, intX-5:intX+intW+5]
            img_ROI1 = img_thresh[intY:intY+intH, intX:intX+intW]
            # przeskaluj ROI, aby był bardziej spójny w rozpoznawaniu i przechowywaniu
            img_ROI_resized = cv2.resize(img_ROI1, (RESIZED_IMAGE_WIDTH, RESIZED_IMAGE_HEIGHT))

        # stwórz obraz krawędzi przeskalowanego ROI
        img_ROI_edges = cv2.Canny(img_ROI.copy(), 30, 200)

        # znajdź kontury na obrazie ROI
        contours_ROI, hierarchy_ROI = cv2.findContours(img_ROI_edges.copy(),
                                                       cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # słownik do przechowywania dopasowania każdego znaku
        matches = {}
        # dla każdego konturu znaku
        for letter, letter_cntr in chars_contour.items():
            # pobierz dopasowanie rozważanego konturu treningowego znaku do każdego znaku
            ret = cv2.matchShapes(letter_cntr[0], contours_ROI[0], 1, 0.0)
            # zapisz dopasowanie do znaku
            matches[letter] = ret
        # znajdź najlepsze dopasowanie
        best = min(matches, key=matches.get)

        # sprawdź, czy nie ma fałszywych klasyfikacji
        # wiemy, że kontury są zawsze uporządkowane od prawego dolnego rogu
        # i znamy pozycje naszych znaków na obrazie treningowym (all_characters.jpg)
        # te fałszywe klasyfikacje pojawiły się podczas testowania:
        if idx == 0 and best == '6':
            best = '9'
        if idx == 7 and best == 'S':
            best = '2'
        if idx == 10 and best == 'O':
            best = 'M'
        if idx == 11 and best == 'O':
            best = "N"
        if idx == 15 and best == 'O':
            best = 'X'
        if idx == 23 and best == '0':
            best = 'D'
        if idx == 30 and best == 'O':
            best = 'W'
        # dodaj naszą klasyfikacyjną literę do listy całkowitych znaków
        int_classifications.append(ord(best))
        # spłaszcz obraz do 1-wymiarowej tablicy numpy
        npa_flattened_image = img_ROI_resized.reshape((1, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))
        # dodaj spłaszczony obraz do listy spłaszczonych obrazów
        npa_flattened_images = np.append(npa_flattened_images, npa_flattened_image, 0)

# przekształć listę klasyfikacji całkowitych na tablicę numpy zmiennoprzecinkową
flt_classifications = np.array(int_classifications, np.float32)
# spłaszcz tablicę numpy do 1D, aby można było zapisać do pliku
npa_classifications = flt_classifications.reshape((flt_classifications.size, 1))
# cv2.waitKey()

print("\n \n trening zakończony! \n \n")

return npa_classifications, npa_flattened_images

