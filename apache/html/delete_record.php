<?php
// delete_record.php
require 'auth_check.php';
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
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

    // Pobranie ID rekordu do usunięcia
    $id = $conn->real_escape_string($_POST['id']);

    // Zapytanie SQL do zmiany flagi isDeleted
    $sql = "UPDATE plates SET isDeleted = 1 WHERE id = $id";

    // Wykonanie zapytania
    if ($conn->query($sql) === TRUE) {
        // Przekierowanie do strony głównej po pomyślnym zaktualizowaniu rekordu
        header('Location: index.php');
        exit;
    } else {
        echo "Error updating record: " . $conn->error;
    }

    // Zamknięcie połączenia
    $conn->close();
} else {
    echo "Invalid request method";
}
?>

