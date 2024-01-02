<?php
session_start();

// Database credentials
$host = '192.168.10.150'; // or your server address
$username = 'sa'; // your database username
$password = '1234'; // your database password
$dbname = 'radar'; // your database name

// Create database connection
$conn = new mysqli($host, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$message = ""; // Message to display to the user

// Check if form data is submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Get username and passwords from form and sanitize them
    $newUsername = $conn->real_escape_string(trim($_POST['username']));
    $plainTextPassword = trim($_POST['password']);
    $confirmPassword = trim($_POST['confirm_password']);

    // First, check if the username is already taken
    $userCheck = $conn->prepare("SELECT username FROM users WHERE username = ?");
    $userCheck->bind_param("s", $newUsername);
    $userCheck->execute();
    $userCheckResult = $userCheck->get_result();

    if ($userCheckResult->num_rows > 0) {
        $message = "Username already taken. Please choose a different one.";
    } elseif ($plainTextPassword !== $confirmPassword) {
        $message = "Passwords do not match!";
    } else {
        // Hash the password
        $hashedPassword = password_hash($plainTextPassword, PASSWORD_DEFAULT);

        // Prepare and execute SQL query
        $stmt = $conn->prepare("INSERT INTO users (username, password) VALUES (?, ?)");
        $stmt->bind_param("ss", $newUsername, $hashedPassword);

        if ($stmt->execute()) {
            $message = "Registered successfully. You can now <a href='login.php'>login</a>.";
        } else {
            // Handle other errors such as database errors
            $message = "Error: " . $stmt->error;
        }

        $stmt->close();
    }
    $userCheck->close();
    $conn->close();
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f7f7f7;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .register-container {
            background-color: white;
            padding: 40px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 300px;
            width: 100%;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        input[type=text], input[type=password] {
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        input[type=submit] {
            padding: 10px;
            border: none;
            border-radius: 4px;
            color: white;
            background-color: #007bff;
            cursor: pointer;
            font-size: 16px;
        }
        input[type=submit]:hover {
            background-color: #0056b3;
        }
        .message {
            color: red;
        }
    </style>
</head>
<body>

<div class="register-container">
    <h2>Register</h2>
    <p class="message"><?php echo $message; ?></p>
    <form method="POST">
        Username: <input type="text" name="username" required><br>
        Password: <input type="password" name="password" required><br>
        Confirm Password: <input type="password" name="confirm_password" required><br>
        <input type="submit" value="Register">
    </form>
</div>

</body>
</html>

