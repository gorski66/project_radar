<!DOCTYPE html>
<html lang="pl">
<head>
    <title>Zdarzenia przekroczenia prędkości</title>
    <style>
        /* Reset some default styles */
        body, h2, table, th, td, div {
            margin: 0;
            padding: 0;
        }
         h2 {text-align: center;}
        /* Basic styling */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f4f4;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 20px auto;
            overflow: hidden;
            padding: 20px;
            background: #fff;
            box-shadow: 0 0 10px 0 #ccc;
        }
        table {
            width: 100%;
            margin-top: 20px;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: center;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #007bff;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
        .btn-cell {
            text-align: center;
         
        }
        .action-btn {
            padding: 5px 10px;
            margin: 0 5px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            width: 150px;      /* Adjust the width as needed */
            height: 40px;      /* Adjust the height as needed */
            padding: 1px;     /* Provide padding if needed */
        }
        .report-btn {
            background-color: #28a745;
            color: white;
        }
        .delete-btn {
            background-color: #dc3545;
            color: white;
        }
        .report-btn:hover, .delete-btn:hover {
            opacity: 0.9;
        }
        /* User Info and Logout Styling */
        .user-info {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #007bff;
            color: white;
            padding: 10px;
            border-radius: 5px;
        }
        .user-info a {
            color: #f4f4f4;
            text-decoration: none;
            padding-left: 5px;
        }
    </style>
    <script>
     function generateReport(recordId) {
    // Wyślij identyfikator rekordu do serwera za pomocą żądania POST
    fetch('generate_report.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'recordId=' + encodeURIComponent(recordId)
    })
    .then(function(response) {
        if (response.ok) {
            return response.blob(); // Pobierz dane jako blob
        } else {
            throw new Error('Error: ' + response.statusText);
        }
    })
    .then(function(blobData) {
        // Utwórz link do pobrania raportu
        var url = window.URL.createObjectURL(blobData);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'raport.pdf'; // Nazwa pliku do pobrania
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url); // Zwolnij zasoby

        // Opcjonalnie można usunąć link po pobraniu raportu
        a.remove();
    })
    .catch(function(error) {
        // Obsłuż błąd (np. wyświetl komunikat o błędzie)
        console.error(error);
    });
}

    </script>
</head>
<body>
    <div class="container">
                <h2>Speeding incidents</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Timestamp In</th>
                <th>Timestamp Out</th>
                <th>Location In</th>
                <th>Location Out</th>
                <th>Plate Number</th>
                <th>Action</th>
            </tr>
        <?php
	
		require 'auth_check.php';
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

		// Zapytanie SQL do pobrania danych
		$sql = "SELECT * FROM plates WHERE timestamp_out IS NOT NULL and isDeleted is FALSE";
		$result = $conn->query($sql);
		
		// Sprawdzenie, czy zapytanie zostało wykonane poprawnie
                if ($result === false) {
                // Obsługa błędu zapytania
                echo "Error: " . $conn->error;
                } else {
               // Zapisanie wyników zapytania do zmiennej $results
                $results = $result->fetch_all(MYSQLI_ASSOC);

		if (isset($_SESSION['username'])) {
    			echo "<div class='user-info'>"
    			. "Logged in as: " . htmlspecialchars($_SESSION['username'])
    			. " | <a href='logout.php' style='color:red;'>Logout</a></div>";
		}




		foreach ($results as $row):
		?>
			<tr>
    			<td><?php echo htmlspecialchars($row["id"]); ?></td>
   		 	<td><?php echo htmlspecialchars($row["timestamp_in"]); ?></td>
                        <td><?php echo htmlspecialchars($row["timestamp_out"]); ?></td>
  			<td><?php echo htmlspecialchars($row["location_in"]); ?></td>
   			<td><?php echo htmlspecialchars($row["location_out"]); ?></td>
                        <td><?php echo htmlspecialchars($row["plate_number_in"]); ?></td>
    			<td class='btn-cell'>
        			<button class='action-btn report-btn' onclick='generateReport(<?php echo htmlspecialchars($row['id']); ?>)'>Generate Report</button>
        			<form method="POST" action="delete_record.php" onsubmit="return confirm('Are you sure you want to delete this record?');">
            				<input type="hidden" name="id" value="<?php echo htmlspecialchars($row['id']); ?>">
            				<input type="submit" class="action-btn delete-btn" value="Delete Record">
        			</form>    
    			</td>
			</tr>
			
			
			
			
			
			<?php
			// Koniec pętli foreach
			endforeach;
			
                	
            	}	

		// Zamknięcie połączenia
		$conn->close();
		
		?>
	   </table>

    </div>
</body>
</html>


