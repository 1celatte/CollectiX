# CollectiX

## Project Description

CollectiX is a web-based illustrated collection management system and marketplace platform. It was developed for users who want to organise and manage their collections while also being able to buy, sell, and trade collectible items.

Users can browse approved collections and items, manage their saved collections and owned items, submit new collections and items for review, and list items for sale or trade. Administrators can review submissions and manage users, collections, items, and other system activities through the admin dashboard.

---

## Main Features

* User Authentication
* Collection Management
* My Collection
* Marketplace
* Trading
* Submission System
* Admin System

---

## Technologies Used

* Python
* Flask
* Flask-SQLAlchemy
* Flask-Migrate
* Flask-Login
* SQLite
* HTML
* CSS
* Bootstrap
* Git
* GitHub

---

## Project Structure

The project uses Flask's application factory pattern and separates different parts of the application using Flask Blueprints.

A simplified structure is:

```text
CollectiX/
├── app/
│   ├── admin/
│   │   ├── templates/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── auth/
│   │   ├── static/
│   │   │   ├── images/
│   │   │   │   └── default_avatar.jpg
│   │   │   └── uploads/avatars/       # uploaded avatars
│   │   ├── templates/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── browse/
│   │   ├── template/                  
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── collection/
│   │   ├── static/uploads/            # uploaded collection and item images
│   │   ├── template/                  
│   │   ├── __init__.py
│   │   └── feature.py
│   ├── marketplace/
│   │   ├── static/
│   │   │   └── seed_images/
│   │   ├── template/                  
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── mycollection/
│   │   ├── templates/
│   │   ├── __init__.py
│   │   └── feature.py
│   ├── static/
│   │   └── images/
│   │       └── collectix-home.png
│   ├── templates/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   └── utils.py
├── instance/
│   └── collectix.db                  # created at runtime; not tracked in main
├── migrations/
│   ├── versions/
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── .env                              # local/server settings; not tracked
├── .gitignore
├── README.md
├── config.py
├── requirements.txt
├── run.py
└── seed.py                           # development data; don't run on production
```

The actual project structure may contain additional files and templates used by individual features.

---

## Installation

### 1. Clone the Repository

Clone the CollectiX repository from GitHub:

```bash
git clone https://github.com/1celatte/CollectiX.git
```

Enter the project folder:

```bash
cd CollectiX
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

## Configuration

CollectiX uses environment variables for configuration values such as email credentials.

Create a `.env` file in the root project directory.

Example:

```env
SECRET_KEY=your-secret-key

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

Do not commit real passwords, email credentials, or other secrets to GitHub.

---

## Database Setup

CollectiX uses SQLite as its database.

The database is located under:

```text
instance/collectix.db
```

The project uses **Flask-Migrate** to manage database schema changes.

To apply the database migrations, run:

```bash
python -m flask db upgrade
```

---

## Seed Data

The project includes seed data for testing the application.

Run:

```bash
python seed.py
```

The seed process creates sample users, payment QR information, tags, collections, items, user collections, owned items, listings, and submissions for testing.

The seed file also creates administrator accounts for testing the admin functionality.

Administrator credentials are provided separately for demonstration and testing purposes.

---

## Running the Application

After completing the installation and configuration steps, start the Flask application using:

```bash
python run.py
```

The application will start locally.

Open the local address shown in the terminal in a web browser.

For example:

```text
http://127.0.0.1:5000
```

---

## User Workflow

A typical user workflow is:

1. Register / Login
2. Browse Collections
3. View Collection
4. View Items
5. Save Collection
6. Manage Owned Items
7. List Items for Sale / Trade
8. Complete a Transaction / Trade

Users can also submit new collections or items for review:

1. User Submission
2. Pending
3. Admin Review
4. Approve / Reject
5. Approved Content Available to Users

---

## Admin Workflow

Administrators can access the admin dashboard after logging in with an account whose role is `admin`.

The admin workflow includes:

1. Admin Login
2. Admin Dashboard
3. Review Pending Submissions
4. Approve / Reject
5. Manage Users
6. View User Details
7. Manage User Activity

The admin system uses role-based access control rather than relying on a specific hard-coded administrator account.

---

## Database Models

The main database models used by CollectiX include:

| Model            | Purpose                                      |
| ---------------- | -------------------------------------------- |
| `User`           | Stores user accounts, roles, and user status |
| `Tag`            | Stores collection tags                       |
| `Collection`     | Stores collectible collections               |
| `Item`           | Stores items belonging to collections        |
| `UserCollection` | Stores collections saved by users            |
| `OwnedItem`      | Stores items owned by users                  |
| `Submission`     | Stores collection and item submissions       |
| `Listing`        | Stores items listed for sale or trade        |
| `PaymentQR`      | Stores seller payment QR code information    |
| `Transaction`    | Stores marketplace transactions              |
| `Trade`          | Stores item trade information                |

These models are connected through relationships to allow CollectiX to manage users, collections, ownership, submissions, marketplace activities, payments, and trades.

---

## Git and GitHub

Git and GitHub are used for version control throughout the project.

The project is developed using separate branches for different features and changes before merging them into the main project.

Example:

* `main`
* Feature branches
* Admin development
* Other feature development

Development progress is committed regularly so that project progress and individual contributions can be tracked.

---

## External Resources and AI Usage

External resources and AI tools were used as learning and development references during the project.

AI tools were used to help understand programming concepts, troubleshoot errors, and improve project documentation. All suggested solutions were reviewed and tested by the project members before being used in the project.

---

## Testing

The application was tested to ensure that:

* Required dependencies can be installed
* The database can be created or upgraded
* The application starts successfully
* User registration and login work
* Collection and item functions work
* Submission workflows work
* Admin functions work
* Marketplace functions work
* Invalid inputs are handled correctly
* The application does not contain critical runtime errors

The final source code and required assets were also tested after extracting the submitted ZIP file.

---

## Deployment

A deployed version of CollectiX is available at:

**Application:** https://collectix.pythonanywhere.com/

The deployed version provides the version of CollectiX submitted for the Mini IT Project.

---

## Project Team

**Project:** CollectiX
**Course:** CSP1123 Mini IT Project
**Trimester:** TRI 2620

### Team Members

* Loo Xue JIng
* Chan Zi Jian
* Coco Ng Chi Fei
