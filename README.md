Facial Recognition Multi Factor Authentication Web Application
This project is a web application built using Python and Flask for the backend, and HTML, CSS, and JavaScript for the frontend. The application provides multi-factor authentication using facial recognition, similar to Microsoft Authenticator. Users can register their email, password, and verify their identity via email. Additionally, they can register their face for authentication and login to third-party applications.

Cloning the Repository
To clone the GitHub repository and install the necessary libraries, follow these steps:

Open a terminal or command prompt.
Run the following command to clone the repository:
Copy
git clone <repository_url>
Change your directory to the project's root directory:
Copy
cd Facial-Recognition-MFA-Web-App
Install the required libraries by running the following command:
basic
Copy
pip install -r requirements.txt
Make sure you have Python and pip installed on your system before proceeding with the above steps.

Available Routes
The web application provides the following routes:

Homepage:

Route: /home
Description: Displays the home page of the application.
Login Page:

Route: /login (supports GET and POST methods)
Description: Allows users to log in to the application.
Face ID Authentication:

Route: /faceID (supports GET and POST methods)
Description: Enables users to authenticate using facial recognition.
Forget Password by Authenticating with Face ID:

Route: /recoveryFaceID (supports GET and POST methods)
Description: Allows users to recover their password by authenticating with facial recognition.
Authentication when Changing Email:

Route: /changeEmailFaceID (supports GET and POST methods)
Description: Provides authentication when changing the user's email.
Change Email Page:

Route: /changeEmail (supports GET and POST methods)
Description: Allows users to change their registered email.
Logout:

Route: /logout
Description: Logs out the user from the application.
Register Page:

Route: /register (supports GET and POST methods)
Description: Allows users to register an account.
Reset Password Page:

Route: /reset (supports GET and POST methods)
Description: Allows users to reset their password.
User Confirmation to Register Account Page:

Route: /setup
Description: Displays a page for user confirmation to register an account.
Email Verification Page:

Route: /verification (supports GET and POST methods)
Description: Displays a page for email verification.
Please note that the routes are ordered chronologically and logically to provide a smooth user experience.

Running the Application
To run the application, follow these steps:

Make sure you are in the project's root directory.
Run the following command:
Copy
python app.py
Open your web browser and navigate to http://127.0.0.1:5000 to access the application.
Ensure that you have installed all the required libraries mentioned in the previous section before running the application.
