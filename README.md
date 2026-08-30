# ElderlyCare & Emergency Alert System

A database-driven web application designed to enhance the safety, health management, and well-being of senior citizens — connecting elderly residents with caregivers, doctors, and family members through real-time monitoring and emergency alerts.

## Features

### User Roles

- **Admin** — Oversees the entire system: manages all users (residents, caregivers, doctors, family), monitors real-time alerts, reviews activity reports, and maintains data integrity.
- **Elderly Person** — Views health readings, appointments, and medications; schedules appointments; triggers emergency help directly through the portal.
- **Family Member** — Monitors the elderly person's health remotely, receives real-time alerts, communicates with the care team, and tracks appointments.
- **Caregiver** — Supports daily care, records vital signs, manages tasks and appointments, responds to alerts, and communicates with doctors and family.
- **Doctor** — Reviews vitals and alerts, manages prescriptions and treatment plans, and schedules appointments for assigned patients.

### Core Functionality

- **Public Pages** — Home, Services, About Us, and Contact pages introducing the platform and its care offerings.
- **Authentication** — Secure login and role-based sign-up (Doctor, Caregiver, Family Member, Patient).
- **Admin Dashboard** — System-wide statistics, user distribution charts, 7-day alert trend graphs, and live emergency alert management.
- **Elderly Dashboard** — Personal health snapshot (heart rate, blood pressure, blood sugar, temperature), upcoming appointments, active medications, assigned care team, and an emergency help button.
- **Doctor Dashboard** — Patient list with alert counts, vital sign review, prescription management, appointment scheduling, and a centralized alert response panel.
- **Caregiver Dashboard** — Patient selector, real-time vitals with 7-day trend graphs, task management, appointment scheduling, alert monitoring, and direct communication with doctors/family.
- **Family Dashboard** — Real-time health stats, alert history, health trend charts, care team contact options, and secure messaging with the care team.
- **Emergency Alerts** — System-wide alert types including falls, missed medication, abnormal heart rate, and high blood pressure — trackable by status (Pending, Acknowledged, Resolved).

## Technologies Used

- Python
- Flask
- MySQL
- HTML5 / CSS3
- JavaScript

## Project Structure

```
ElderlyCareSystem/
├── static/
├── templates/
├── app.py
├── requirements.txt
├── Project-Report.pdf
└── screenshots/
```

## Documentation

The full project report (system design, database schema, and detailed functionality walkthrough) is available here:

📄 [**Project Report (PDF)**](Project-Report.pdf)

## How to Run

1. Clone the repository:
   ```
   git clone https://github.com/ayesha27mimi/Elderly-Care-and-Emergency-Alert-System.git
   cd Elderly-Care-and-Emergency-Alert-System
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate      # On Windows
   pip install -r requirements.txt
   ```

3. Set up the MySQL database:
   - Create a new database in MySQL (e.g. `elderlycare_db`).
   - Import the provided `.sql` schema file (if included in the repo) using MySQL Workbench or the command line:
     ```
     mysql -u root -p elderlycare_db < schema.sql
     ```
   - Update the database connection details (host, username, password, database name) inside `app.py` or your config/`.env` file to match your local MySQL setup.

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and visit:
   ```
   http://localhost:5000
   ```

## Screenshots

### Public Pages

**Home Page**
![Home Page](screenshots/home-page.png)

**Services Page**
![Services Page](screenshots/services-page.png)

**About Us Page**
![About Us Page](screenshots/about-page.png)

### Authentication

**Login Page**
![Login Page](screenshots/login-page.png)

**Sign Up Page**
![Sign Up Page](screenshots/signup-page.png)

### Admin Dashboard

**Dashboard Overview**
![Admin Dashboard](screenshots/admin-dashboard.png)

**User Management**
![User Management](screenshots/user-management.png)

**Elderly Residents**
![Elderly Residents](screenshots/elderly-residents.png)

**Emergency Alerts**
![Emergency Alerts](screenshots/emergency-alerts.png)

### Elderly Dashboard

**Welcome & Health Status**
![Elderly Dashboard - Health Status](screenshots/elderly-dashboard-health.png)

**Appointments & Medications**
![Elderly Dashboard - Appointments](screenshots/elderly-dashboard-appointments.png)

**My Care Team**
![Elderly Dashboard - Care Team](screenshots/elderly-dashboard-careteam.png)

### Doctor Dashboard

**Dashboard Overview**
![Doctor Dashboard](screenshots/doctor-dashboard.png)


