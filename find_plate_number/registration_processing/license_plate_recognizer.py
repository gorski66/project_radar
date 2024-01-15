import numpy as np
import cv2

kNearest = cv2.ml.KNearest_create()

# Rozmiar tablicy rejestracyjnej w Polsce wynosi 520 x 114 mm.
# wybierz mniejszy stosunek, aby zaakceptować większe kontury
# Stosunek szerokości do wysokości tablic rejestracyjnych w Polsce.
PLATE_HEIGHT_TO_WIDTH_RATIO = 90 / 520

# Stosunek szerokości do wysokości znaku
CHAR_RATIO_MIN = 0.25
CHAR_RATIO_MAX = 0.85

# Liczba znaków na polskiej tablicy rejestracyjnej
LICENSE_PLATE_LENGTH = 7

RESIZED_CHAR_IMAGE_WIDTH = 20
RESIZED_CHAR_IMAGE_HEIGHT = 30

SHOW_STEPS = False


def train_KNN(classifications, flattened_images):
    """
    Funkcja trenująca obiekt kNearest na podstawie podanych klasyfikacji znaków i spłaszczonych obrazów znaków
    :param classifications: classification of characters
    :param flattened_images: flattened images with characters
    :return: True when finished
    """
    # klasyfikacje treningowe
    npa_classifications = classifications.astype(np.float32)
    # obrazy treningowe
    npa_flattened_images = flattened_images.astype(np.float32)
    # przekształcenie tablicy numpy na 1d, konieczne do przekazania do wywołania funkcji train
    npa_classifications = npa_classifications.reshape((npa_classifications.size, 1))
    # ustawienie domyślnego K na 1
    kNearest.setDefaultK(1)
    # trening obiektu KNN
    kNearest.train(npa_flattened_images, cv2.ml.ROW_SAMPLE, npa_classifications)

    return True


def get_potential_chars_ROI(chars_potential_plate):
    """
    Funkcja, która znajduje potencjalne tablice rejestracyjne z najbliższymi do 7 znaków na nich
    :param chars_potential_plate: list of list of potential plate ROIs
    :return: index of list containing ROIs with closest to 7 characters
    """

    offset = 0  # ta zmienna pomaga, jeśli jest więcej potencjalnych znaków na potencjalnej tablicy niż zdefiniowano w CHARACTERS_NUMBER
    while True:
        for ROI_idx, potential_chars_ROI in enumerate(chars_potential_plate):
            if len(potential_chars_ROI) > 0:
                if len(potential_chars_ROI) == (LICENSE_PLATE_LENGTH + offset):
                    return ROI_idx
                if len(potential_chars_ROI) == (LICENSE_PLATE_LENGTH - offset):
                    return ROI_idx
        offset += 1


def recognize_chars_in_plate(potential_chars_ROI, img_gray):
    """
    Funkcja, która rozpoznaje znaki na podanym obrazie na podstawie ROI potencjalnych znaków
    :param potential_chars_ROI: ROIs of potential characters
    :param img_gray: gray scale image containing potential characters
    :return:
    license_plate - string containing recognized characters on license plate
    potential_chars_ROI - list of potential chars ROIs
    """
    # progowanie obrazu
    ret, img_threshed = cv2.threshold(img_gray, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    # tablica rejestracyjna do zwrócenia. Dodamy każdy rozpoznany znak.
    license_plate = ""
    # sortuj potencjalne ROI znaków od lewej do prawej
    potential_chars_ROI = sorted(potential_chars_ROI, key=lambda ROI: ROI[0])
    dist_list = []
    for current_char in potential_chars_ROI:
        # uzyskaj ROI każdego potencjalnego znaku
        img_ROI = img_threshed[current_char[1]:current_char[1] + current_char[3],
                  current_char[0]:current_char[0] + current_char[2]]
        # zmień rozmiar ROI do zdefiniowanego rozmiaru w treningu KNN
        img_ROI_resized = cv2.resize(img_ROI, (RESIZED_CHAR_IMAGE_WIDTH, RESIZED_CHAR_IMAGE_HEIGHT))
        # przekształć ROI, aby pasowało do danych KNN
        npa_ROI_resized = img_ROI_resized.reshape((1, RESIZED_CHAR_IMAGE_WIDTH * RESIZED_CHAR_IMAGE_HEIGHT))
        # przekonwertuj domyślny typ obrazu (int) na float
        npa_ROI_resized = np.float32(npa_ROI_resized)
        # znajdź najbliższego sąsiada
        retval, npa_results, neigh_resp, dists = kNearest.findNearest(npa_ROI_resized, k=1)
        # zapisz odległość zwróconą przez KNN, aby określić, który znak jest rozpoznany nieprawidłowo, gdy jest więcej znaków
        # niż w CHARACTERS_NUMBER
        dist = dists[0][0]
        dist_list.append(dist)
        # pobierz znak
        currentChar = str(chr(int(npa_results[0][0])))
        # dodaj znak do ciągu tablicy rejestracyjnej
        license_plate = license_plate + currentChar

    if SHOW_STEPS:
        print(f"KNN distances: {dist_list}")
    # gdy jest więcej znaków niż powinno być, ustal, który znak jest rozpoznany nieprawidłowo
    while len(license_plate) > LICENSE_PLATE_LENGTH:
        incorrect_char_idx = np.argmax(dist_list)
        license_plate = license_plate[0:incorrect_char_idx:] + license_plate[incorrect_char_idx + 1::]
        del (dist_list[incorrect_char_idx])
        del (potential_chars_ROI[incorrect_char_idx])

    if SHOW_STEPS:
        print(f"Recognized chars in license plate {license_plate}")

    return license_plate, potential_chars_ROI


def license_plate_rules(license_plate, three_chars):
    """
    Sprawdź, czy zwrócona tablica rejestracyjna pasuje do zasad dotyczących tablic rejestracyjnych w Polsce.
    Jeśli znak na tablicy rejestracyjnej jest w nieprawidłowym miejscu (na przykład Z jest w drugiej części tablicy) zmień go na poprawny
    (Z -> 2)
    https://pl.wikipedia.org/wiki/Tablice_rejestracyjne_w_Polsce#Opis_systemu_tablic_rejestracyjnych_w_Polsce
    :param license_plate: string containing license plate
    :param three_chars: TRUE if license plate has 3 chars in first part
    :return: license_plate: string containing fixed license plate
    """

    #  zakazane litery w pierwszej części tablicy rejestracyjnej i ich odpowiadające dopasowania
    forbidden_chars_1 = {'0': 'O', '1': 'I', '2': 'Z', '3': 'B', '4': 'A', '5': 'S',
                         '6': 'G', '7': 'Z', '8': 'B', '9': 'P', 'X': 'K'}
    # zakazane litery w drugiej części tablicy rejestracyjnej i ich odpowiadające dopasowania
    forbidden_chars_2 = {'B': '8', 'D': '0', 'I': '1', 'O': '0', 'Z': '2'}

    first_part_len = 2
    if three_chars:
        first_part_len = 3

    # jeśli długość podanej tablicy rejestracyjnej jest mniejsza niż LICENSE_PLATE_LENGTH
    # wtedy nie zmieniaj dwóch pierwszych cyfr na litery
    if len(license_plate) == LICENSE_PLATE_LENGTH:
        # jeśli którykolwiek z pierwszych dwóch znaków to cyfra, zmień ją na odpowiadającą literę
        for i in range(first_part_len):
            if license_plate[i] in forbidden_chars_1:
                new_char = forbidden_chars_1[license_plate[i]]
                s = list(license_plate)
                s[i] = new_char
                license_plate = "".join(s)
        # sprawdź drugą część tablicy rejestracyjnej
        for i in range(first_part_len, len(license_plate)):
            if license_plate[i] in forbidden_chars_2:
                new_char = forbidden_chars_2[license_plate[i]]
                s = list(license_plate)
                s[i] = new_char
                license_plate = "".join(s)

    if SHOW_STEPS:
        print(f"License plate after rules checking: {license_plate}")

    return license_plate


def fill_empty_chars(license_plate, chars_ROI):
    """
    Funkcja wypełniająca puste znaki znakiem '?' w wykrytej tablicy rejestracyjnej.

    :param license_plate: license plate to fill
    :param chars_ROI: [x, y, w, h] for each character
    :return:
    license plate - string with filled license plate
    chars_ROI - ROIs of ? on image
    """
    # znajdź najszerszy znak
    widest_char = max(map(lambda x: x[2], chars_ROI))

    while len(license_plate) != LICENSE_PLATE_LENGTH:
        # odległości między wykrytymi znakami
        distance_between_chars = []
        # oblicz odległość między każdym znakiem
        for i, ROI in enumerate(chars_ROI):
            if i == 0:
                distance = ROI[0]
                distance_between_chars.append(distance)
            else:
                distance = chars_ROI[i][0] - (chars_ROI[i - 1][0] + chars_ROI[i - 1][2])
                distance_between_chars.append(distance)

        # znajdź największą odległość między znakami i wypełnij to miejsce znakiem oraz wygenerowanym ROI
        char_idx = np.argmax(distance_between_chars)
        # dodaj znak na miejscu char_idx
        s = list(license_plate)
        s.insert(char_idx, '?')  # wstaw '?' w puste miejsce
        license_plate = "".join(s)
        # dodaj wygenerowane ROI na miejscu char_idx
        new_ROI = list(np.copy(chars_ROI[char_idx]))
        new_ROI[0] -= (widest_char + 1)
        chars_ROI.insert(char_idx, new_ROI)

    if SHOW_STEPS:
        print(f"Recognized license plate with filled empty spaces {license_plate}")

    return license_plate, chars_ROI


def preprocess(image, parameters=(False, False)):
    """
    Funkcja przygotowująca obraz do dalszej obróbki.
    Konwersja obrazu na skale szarości, zmiana rozmiaru obrazu, rozmycie obrazu, wykrywanie krawędzi na obrazie.

    :param image: image you want to preprocess
    :param parameters:
            index 0 -> if True chooses second parameters for image filtering
            index 1 -> if True chooses second parameters for detecting edges
    :return:
    gray_blur -> grayscale blurred image
    gray_edge -> grayscale image with edges
    width -> width of image after resizing
    """
    # konwertuj obraz na skalę szarości
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # zmień rozmiar obrazu dla szybszej obróbki
    gray_img = cv2.resize(gray_img, (768, 576))
    # image_resied = cv2.resize(image, (768, 576))

    # pobierz wymiary zmienionego rozmiaru obrazu
    height = gray_img.shape[0]
    width = gray_img.shape[1]

    # rozmyj obraz
    if not parameters[0]:
        gray_blur = cv2.bilateralFilter(gray_img, 11, 55, 55)
    else:  # change parameters of filter if we couldn't find any license plate before
        gray_blur = cv2.bilateralFilter(gray_img, 11, 17, 17)

    # wykryj krawędzie na obrazie
    if not parameters[1]:
        gray_edges = cv2.Canny(gray_blur, 85, 255)
    else:  # zmień parametry wykrywania krawędzi, jeśli wcześniej nie udało się znaleźć żadnej tablicy rejestracyjnej
        gray_edges = cv2.Canny(gray_blur, 30, 200)

    return gray_blur, gray_edges, width


def find_potential_plates_vertices(gray_edges, width):
    """
     Funkcja znajdująca wierzchołki potencjalnych tablic rejestracyjnych na obrazie z wykrytymi krawędziami.

    :param gray_edges: edge image
    :param width: width of image
    :return: list of potential plates vertices
    """
    # znajdź kontury na obrazie z krawędziami
    contours, hierarchy = cv2.findContours(gray_edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # znajdź potencjalne kontury pasujące do wymiarów tablicy rejestracyjnej
    potential_plates_vertices = []
    for contour in contours:
        [x, y, w, h] = cv2.boundingRect(contour)

         # wyklucz kontury mniejsze niż 1/3 szerokości obrazu i których wysokość nie odpowiada stosunkowi wymiarów tablicy rejestracyjnej
        if w < (width / 3) or h < (w * PLATE_HEIGHT_TO_WIDTH_RATIO) or w == width:
            continue

        # poniższe linie oraz get_birds_eye_view są zaadaptowane z:
        # https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
        # https://www.pyimagesearch.com/2014/05/05/building-pokedex-python-opencv-perspective-warping-step-5-6/
        # przekształć kontur potencjalnej tablicy
        pts = contour.reshape(contour.shape[0], 2)
        # wierzchołki prostokąta tablicy
        vertices = np.zeros((4, 2), dtype="float32")
        # górny lewy punkt ma najmniejszą sumę, a dolny prawy ma największą
        s = pts.sum(axis=1)
        vertices[0] = pts[np.argmin(s)]
        vertices[2] = pts[np.argmax(s)]
         # górny prawy ma najmniejszą różnicę, a dolny lewy największą
        diff = np.diff(pts, axis=1)
        vertices[1] = pts[np.argmin(diff)]
        vertices[3] = pts[np.argmax(diff)]
        potential_plates_vertices.append(vertices)

    return potential_plates_vertices


def get_birds_eye_view(potential_plates_vertices, gray_edges, gray_blur, skip_ratio_check=False):
    """
    Zmienia perspektywę we wszystkich potencjalnych tablicach rejestracyjnych na widok z lotu ptaka.

    :param potential_plates_vertices: list of vertices of potential license plate
    :param gray_edges: edge image used in warp perspective
    :param gray_blur: blurred image used in warp perspective
    :param skip_ratio_check: skip checking ratio of potential license plate to match all warp all potential contours
    :return: warped_plates_edges: list containing birds eye view edge images with license plate
    warped_plates_gray: list containing birds eye view blur images with license plate
    """
    # zmienia perspektywę we wszystkich potencjalnych tablicach rejestracyjnych, aby uzyskać "widok z lotu ptaka"
    warped_plates_edges = []
    warped_plates_gray = []
    for idx, vertices in enumerate(potential_plates_vertices):
         # uzyskaj wszystkie rogi w prostszy sposób do kodowania
        (tl, tr, br, bl) = vertices
        # oblicz szerokość i wysokość obrazu utworzonego przez rogi
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        # wybierz maksymalne wartości szerokości i wysokości, aby osiągnąć końcowe wymiary
        maxWidth = max(int(widthA), int(widthB))
        maxHeight = max(int(heightA), int(heightB))

        # jeśli w pierwszej próbie nie udało się uzyskać widoku z lotu ptaka, ponieważ obraz nie odpowiadał stosunkowi wymiarów tablicy rejestracyjnej
        # wtedy pomiń ten krok
        if not skip_ratio_check:
             # przestań rozważać obrazy, które nie odpowiadają stosunkowi szerokości do wysokości tablicy rejestracyjnej
            if maxHeight < maxWidth * PLATE_HEIGHT_TO_WIDTH_RATIO:
                continue

        # skonstruuj punkty docelowe, które będą używane do mapowania ekranu na widok z góry, "widok z lotu ptaka"
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
         # oblicz macierz transformacji perspektywy i przekształć perspektywę, aby uchwycić ekran
        M = cv2.getPerspectiveTransform(vertices, dst)
        warp_edges = cv2.warpPerspective(gray_edges, M, (maxWidth, maxHeight))
        warp_gray = cv2.warpPerspective(gray_blur, M, (maxWidth, maxHeight))

       # przestań rozważać obraz, który zawiera tylko zera
        if not np.any(warp_edges):
            continue
        # dodaj przekształcony obraz do listy
        warped_plates_edges.append(warp_edges)
        warped_plates_gray.append(warp_gray)

    return warped_plates_edges, warped_plates_gray


def find_potential_chars_on_plates(warped_plates_edges):
    """
    Funkcja znajdująca ROI potencjalnych znaków na obrazie zawierającym tablicę rejestracyjną.

    :param warped_plates_edges: list containing birds eye view edge images with license plate
    :return: list of ROIS of potential chars on license plate
    """
    chars_potential_plate = []
    for idx, plate in enumerate(warped_plates_edges):

        plate_area = plate.size

        char_contours, char_hierarchy = cv2.findContours(plate.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        cntr_img = cv2.drawContours(plate.copy(), char_contours, -1, 100, thickness=2)
        potential_chars_ROI = []
        for i, cntr in enumerate(char_contours):
            [x, y, w, h] = cv2.boundingRect(cntr)
            bounding_area = w * h
             # sprawdź rozmiar konturu, aby dopasować potencjalny rozmiar znaku
            if (bounding_area < (0.025 * plate_area) or bounding_area > (0.4 * plate_area)) or \
                    (CHAR_RATIO_MIN * h > w or w > CHAR_RATIO_MAX * h):
                continue  # no character found
            # sprawdź, czy nie ma powtarzającego się konturu (kontur w konturze)
            if char_hierarchy[0, i, 3] != -1:
                # i jeśli kontur nadrzędny nie jest konturem tablicy
                if cv2.contourArea(char_contours[char_hierarchy[0, i, 3]]) < 0.4 * plate_area:
                    continue
            # dodaj ROI potencjalnego znaku
            potential_chars_ROI.append([x, y, w, h])
            cv2.rectangle(plate, (x, y), (x + w, y + h), 100)
        chars_potential_plate.append(potential_chars_ROI)
        if SHOW_STEPS:
            cv2.imshow(str(idx) + "plate with char boundings", plate)
            cv2.imshow(str(idx) + "plate with contours", cntr_img)

    return chars_potential_plate


def three_chars_in_first_part(chars_ROI):
    """
     Funkcja sprawdzająca, czy tablica rejestracyjna ma 3 znaki w pierwszej części tablicy rejestracyjnej czy 2.

    :param chars_ROI: list of [x, y, w, h] for each character
    :return: TRUE if license plate has 3 chars in first part
    """
    distance_between_chars = []
    for i, ROI in enumerate(chars_ROI):
        if i < LICENSE_PLATE_LENGTH - 1:
            # calculate distance between neighbours
            distance = chars_ROI[i + 1][0] - (chars_ROI[i][0] + chars_ROI[i][2])
            distance_between_chars.append(distance)

    if SHOW_STEPS:
        print(distance_between_chars)
     # jeśli największa odległość jest między 3. a 4. znakiem, to tablica ma 3 znaki w pierwszej części
    if np.argmax(distance_between_chars) == 2:
        if SHOW_STEPS:
            print("3 CHARS")
        return True
    else:
        if SHOW_STEPS:
            print("2 CHARS")
        return False


def recognize_license_plate(image: np.ndarray) -> str:
    """
    Funkcja rozpoznająca tablicę rejestracyjną na podanym obrazie.

    :param image: image containing license plate
    :return: string of characters found on license plate
    """
    # print(f'image.shape: {image.shape}')

    if SHOW_STEPS:
        print("\n \n \n \n \n \n")

     # przetwarzanie wstępne obrazu w celu uzyskania użytecznych danych
    gray_blur, gray_edges, width = preprocess(image)

     # znajdowanie wierzchołków potencjalnych tablic
    potential_plates_vertices = find_potential_plates_vertices(gray_edges, width)

    # uzyskiwanie widoku z lotu ptaka potencjalnych tablic na podstawie znalezionych wierzchołków
    warped_plates_edges, warped_plates_gray = get_birds_eye_view(potential_plates_vertices, gray_edges, gray_blur)

    # znajdowanie potencjalnych znaków na potencjalnych tablicach
    chars_potential_plate = find_potential_chars_on_plates(warped_plates_edges)

    # jeśli nie znaleziono potencjalnych znaków na tablicach, uzyskaj widok z lotu ptaka jeszcze raz, ale z innymi parametrami
    if not any(chars_potential_plate):
        if SHOW_STEPS:
            print(f"No chars found in first try")

         # uzyskaj widok z lotu ptaka jeszcze raz, ale tym razem pomiń sprawdzanie stosunku wymiarów
        warped_plates_edges, warped_plates_gray = get_birds_eye_view(potential_plates_vertices, gray_edges,
                                                                     gray_blur, True)

        # znajdowanie potencjalnych znaków na potencjalnych tablicach
        chars_potential_plate = find_potential_chars_on_plates(warped_plates_edges)

        # jeśli nadal nie znaleziono potencjalnych znaków po pominięciu sprawdzania stosunku wymiarów
        # przetwórz obraz jeszcze raz z innymi parametrami
        if not any(chars_potential_plate):
            if SHOW_STEPS:
                print(f"No chars found after skipping ratio checking")
                print("Trying with different preprocessing parameters...")
            # lista parametrów w tupli dla przetwarzania wstępnego
            # index 0 -> jeśli True wybiera drugie parametry filtrowania obrazu
            # index 1 -> jeśli True wybiera drugie parametry do wykrywania krawędzi
            preprocess_parameters = [(True, False), (False, True), (True, True)]

            for params in preprocess_parameters:
                gray_blur, gray_edges, width = preprocess(image, params)
                # znajdź wierzchołki potencjalnych tablic
                potential_plates_vertices = find_potential_plates_vertices(gray_edges, width)
                # uzyskaj widok z lotu ptaka potencjalnych tablic na podstawie znalezionych wierzchołków
                warped_plates_edges, warped_plates_gray = get_birds_eye_view(potential_plates_vertices, gray_edges,
                                                                             gray_blur, True)
                 # znajdź potencjalne znaki na potencjalnych tablicach
                chars_potential_plate = find_potential_chars_on_plates(warped_plates_edges)
                # jeśli nie znaleziono potencjalnych znaków w tej próbie, spróbuj z innymi parametrami przetwarzania wstępnego
                if not any(chars_potential_plate):
                    continue
                else:
                    break

             # jeśli nie znaleziono potencjalnych znaków na obrazie przy wszystkich kombinacjach, zwróć pustą tablicę rejestracyjną
            if not any(chars_potential_plate):
                if SHOW_STEPS:
                    print("NO LICENSE PLATE FOUND ON IMAGE")
                return '???????'  # return ?

    if SHOW_STEPS:
        for idx, potential_chars_ROI in enumerate(chars_potential_plate):
            print(f"Potential plate index: {idx} -> potential chars {len(potential_chars_ROI)}")

    # Wybierz potencjalną tablicę rejestracyjną z 7 potencjalnymi znakami. Jeśli żadna z potencjalnych tablic rejestracyjnych nie ma 7 potencjalnych znaków,
    # wybierz tablicę z liczbą znaków najbliższą 7. Następnie uzyskaj ROI potencjalnych znaków i szary obraz tej tablicy.
    potential_chars_ROI_idx = get_potential_chars_ROI(chars_potential_plate)
    potential_chars_ROI = chars_potential_plate[potential_chars_ROI_idx]
    potential_chars_gray_img = warped_plates_gray[potential_chars_ROI_idx]

    # rozpoznaj znaki na tablicy rejestracyjnej
    license_plate, potential_chars_ROI = recognize_chars_in_plate(potential_chars_ROI, potential_chars_gray_img)

    # jeśli na tablicy jest mniej znaków niż powinno być, wypełnij puste miejsca na podstawie pozycji znaków
    if len(potential_chars_ROI) < LICENSE_PLATE_LENGTH:
        license_plate, potential_chars_ROI = fill_empty_chars(license_plate, potential_chars_ROI)

    # sprawdź, czy tablica rejestracyjna ma 3 lub 2 znaki w pierwszej części 
    three_chars = three_chars_in_first_part(potential_chars_ROI)

    # sprawdź, czy zwrócona tablica rejestracyjna pasuje do zasad dotyczących tablic rejestracyjnych w Polsce. Jeśli nie, zmień znak na podstawie podobieństwa znaków
    license_plate = license_plate_rules(license_plate, three_chars)

    if SHOW_STEPS:
        cv2.waitKey()
        cv2.destroyAllWindows()
    return license_plate
