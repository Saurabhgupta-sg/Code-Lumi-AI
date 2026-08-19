Code Lumi AI

Code Lumi AI is a fullscreen desktop coding environment built with Python and
CustomTkinter. It combines a multi-language editor, local AI explanations,
text-to-speech, Python execution visualization, secure user authentication, and
administrator account management.

Features

Authentication and security

Fullscreen login and sign-up interface

SQLite user database created automatically

Passwords protected with PBKDF2-HMAC-SHA256 and individual random salts

Login using either username or email

Username, email, and password validation

Automatic close when the application loses focus

Local database files excluded from Git through .gitignore

Administrator controls

The first account in a new database becomes the administrator

Existing installations automatically promote the earliest account to admin

Fullscreen Manage Users page for administrators

Add standard users or additional administrators

Change the password of any user

Delete user accounts

Protection against deleting the currently signed-in administrator

Normal users cannot access administrator database operations

Coding tools

Editors for Python, C, C++, Java, JavaScript, HTML/CSS, and C# files

Jupyter-style Python notebook cells

Open, edit, and save source files

Run supported code from inside the application

HTML preview in the default browser

Python line-by-line execution animation with variable visualization

Dark and light themes

AI and accessibility

Local code explanations through Ollama

Beginner-friendly error explanations

Text-to-speech output using pyttsx3

Optional animated mascot.gif

Uses the qwen2.5-coder:1.5b Ollama model by default

Requirements

Python 3.10 or newer

pip

Ollama for AI explanations

Node.js for JavaScript execution

GCC/G++ for C and C++ execution

JDK for Java execution

The extra language tools are optional if you only plan to use Python.

Installation in VS Code

Clone or open the Code-Lumi-AI repository in VS Code.

Open Terminal > New Terminal.

Create a virtual environment.

Windows PowerShell

py -m venv .venv
.venv\Scripts\Activate.ps1

macOS or Linux

python3 -m venv .venv
source .venv/bin/activate

Install the Python dependencies.

pip install -r requirements.txt

Install the Ollama model used by the application.

ollama pull qwen2.5-coder:1.5b

Start Code Lumi AI.

python vizardPy.py

First login and administrator access

On a fresh installation, select Sign up and create the first account. That
account automatically receives the admin role.

For an existing database created before administrator support was added, the
earliest registered account is promoted automatically. Its username and
password do not change.

After signing in as an administrator, click Manage Users in the top bar to:

Add a user or another administrator.

Change a user's password.

Delete an account.

Review all registered accounts and roles.

Database

The SQLite database is created automatically at:

data/code_lumi.db

The table definitions are stored in schema.sql. Database upgrades, including
the administrator role, are applied automatically by auth_database.py.

Do not commit the database file to GitHub because it contains account records.
The supplied .gitignore excludes it by default.

Keyboard shortcuts

Shortcut

Action

F2

Save the current file

F3

Open a file

Alt+F9

Run the current code

Project structure

Code-Lumi-AI/
├── vizardPy.py                 # Main fullscreen desktop application
├── login_signup.py             # Login and sign-up frontend
├── auth_database.py            # Authentication and administrator SQL logic
├── schema.sql                  # SQLite schema
├── requirements.txt            # Python dependencies
├── tests/
│   └── test_auth_database.py   # Authentication and admin tests
├── data/                       # Runtime database location
└── mascot.gif                  # Optional animated mascot

Run the tests

From the project root, run:

python -m unittest discover -s tests -v

The tests verify:

Sign-up and login

Duplicate-account rejection

Incorrect-password rejection

Administrator user creation

Administrator password changes and deletion

Permission denial for standard users

Self-deletion protection

Push updates to GitHub

After replacing the updated project files, run:

git add .
git commit -m "Update authentication, admin controls and documentation"
git pull --rebase
git push

Important security note

Code entered in the editor is executed locally on your computer. Only run code
you trust. The application's execution environment is not a security boundary
for untrusted programs.