<?php 
ob_start();
require 'auth_check.php';
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    // Pobierz identyfikator rekordu z żądania POST
     if (isset($_POST['recordId'])) {
     $recordId = $_POST['recordId'];
     echo "Record ID received: " . htmlspecialchars($recordId); // For demonstration purposes    

    // Parametry połączenia z bazą danych
    $host = '192.168.10.150'; // lub inny adres serwera bazy danych
    $username = 'sa';
    $password = '1234';
    $dbname = 'radar';

    // Tworzenie połączenia
    $conn = new mysqli($host, $username, $password, $dbname);

    // Sprawdzenie połączenia
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // Zapytanie SQL do pobrania danych z tabeli plates na podstawie recordId
    $sql = "SELECT * FROM plates WHERE id = $recordId";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();

        // Pobierz dane z rekordu plates
        $timestampIn = strtotime($row['timestamp_in']);
        $timestampOut = strtotime($row['timestamp_out']);
        $timeDiff = ($timestampOut - $timestampIn) / 3600; // Różnica czasu w godzinach
        $speed = 55 / $timeDiff; // Oblicz prędkość

        // Pobierz resztę danych z tabeli plates
        $plateInfo = [
            'timestamp_in' => $row['timestamp_in'],
            'location_in' => $row['location_in'],
            'plate_number_in' => $row['plate_number_in'],
            'timestamp_out' => $row['timestamp_out'],
            'location_out' => $row['location_out'],
            'plate_number_out' => $row['plate_number_out'],
            'plates_id' => $row['id']
        ];

        $ownerSql = "SELECT * FROM cars WHERE plate_number = '{$plateInfo['plate_number_in']}'";
		$ownerResult = $conn->query($ownerSql);

		if ($ownerResult->num_rows > 0) {
        $ownerRow = $ownerResult->fetch_assoc();

        // Now you can use the $ownerRow data just like you did with $row
            $carInfo = [
            'brand' => $ownerRow['brand'],
            'model' => $ownerRow['model'],
            'owner_name' => $ownerRow['owner_name'],
            'owner_address' => $ownerRow['owner_address'],
            'owner_contact_number' => $ownerRow['owner_contact_number'],
        ];
        $ticketPrice = 0; // default if not in any specified range
	if ($speed >= 120 && $speed < 130) {
    		$ticketPrice = 200; // 200 zł for speeds between 120 and 130
	} elseif ($speed >= 130 && $speed < 140) {
    		$ticketPrice = 400; // 400 zł for speeds between 130 and 140
	} elseif ($speed >= 140 && $speed < 150) {
    		$ticketPrice = 500; // 500 zł for speeds between 140 and 150
	} elseif ($speed >= 150 && $speed <= 200) {
    		$ticketPrice = 1000; // 1000 zł for speeds between 150 and 200
	} elseif ($speed > 200) {
        	$ticketPrice = 2500; // 2500 zł for speeds over 200
	}
	$currentDate = date('m/d/Y h:i:s a', time());
	// Prepare SQL statement with current timestamp, speed, and calculated ticket price
	$insert = "INSERT INTO raport (timestamp, speed, ticket, plates_id) VALUES (NOW(), ?, ?, '{$plateInfo['plates_id']}')";

	// Prepare and bind
	$stmt = $conn->prepare($insert);
	$stmt->bind_param("ii", $speed, $ticketPrice); // "ii" denotes all are integers

	// Execute the query
	if ($stmt->execute()) {
    		echo "New record created successfully";
	} else {
    		echo "Error: " . $stmt->error;
	}


        
        // Utwórz raport
		$report = <<<HTML
		<html lang="pl">
		<head>
			<style>
				body { font-family: Helvetica, sans-serif; }
				h1 { color: #333; }
				table { width: 100%; border-collapse: collapse; }
				th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
				th { background-color: #f2f2f2; }
			</style>
		</head>
		<body>
			<h1>Raport Pomiaru Prędkości</h1>
			<table>
				<tr><th colspan="2">Informacje o przejezdzie</th></tr>
				<tr><td>Czas wjazdu:</td><td>{$plateInfo['timestamp_in']}</td></tr>
				<tr><td>Miejsce wjazdu:</td><td>{$plateInfo['location_in']}</td></tr>
				<tr><td>Numer rejestracyjny na wjezdzie:</td><td>{$plateInfo['plate_number_in']}</td></tr>
				<tr><td>Czas wyjazdu:</td><td>{$plateInfo['timestamp_out']}</td></tr>
				<tr><td>Miejsce wyjazdu:</td><td>{$plateInfo['location_out']}</td></tr>
				<tr><td>Numer rejestracyjny na wyjezdzie:</td><td>{$plateInfo['plate_number_out']}</td></tr>
				<tr><td>Obliczona predkosc:</td><td>$speed km/h</td></tr>
				<tr><td>Mandat:</td><td>$ticketPrice zlotych</td></tr>
			</table>
			<h2>Informacje o pojezdzie i włascicielu</h2>
			<table>
				<tr><th colspan="2">Dane pojazdu</th></tr>
				<tr><td>Marka:</td><td>{$carInfo['brand']}</td></tr>
				<tr><td>Model:</td><td>{$carInfo['model']}</td></tr>
				<tr><td>Właściciel:</td><td>{$carInfo['owner_name']}</td></tr>
				<tr><td>Adres:</td><td>{$carInfo['owner_address']}</td></tr>
			</table>
			<p>Czas wygenerowania raportu: $currentDate</p>
		</body>
		</html>
		HTML;

        // Generuj PDF przy użyciu TCPDF
        require('/var/www/html/tcpdf/tcpdf.php');

        $pdf = new TCPDF();
        $pdf->AddPage();
        $pdf->SetFont('helvetica', '', 12);
        $pdf->writeHTML($report, true, false, true, false, '');

        // Wyślij dane PDF do przeglądarki
        ob_end_clean();
        $pdfData = $pdf->Output('raport.pdf', 'D'); // Pobierz dane PDF jako string
        header('Content-Type: application/pdf');
        header('Content-Disposition: attachment; filename="raport.pdf"');

        echo $pdfData;

        // Zamknięcie połączenia
        $conn->close();
    } else {
        echo "Plate record not found with ID: " . $recordId;
    }
} else {
    echo "Invalid request method";
}
}
}


?>


