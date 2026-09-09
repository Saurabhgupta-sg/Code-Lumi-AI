# Code Lumi AI

Code Lumi AI is a fullscreen desktop coding environment designed to help students write, run, visualize, and understand code. It combines a multi-language editor, local AI explanations, Python execution tracing, text-to-speech, secure user authentication, and administrator account management.

This project is currently in an early development phase.

## Current Features

### Authentication and Security

* Fullscreen login and signup interface
* SQLite user database created automatically
* Password hashing using PBKDF2-HMAC-SHA256
* Unique random salt for every password
* Login using either username or email
* Username, email, and password validation
* Automatic application closure when focus is lost
* Local database files excluded from Git
* Student and administrator roles

### Administrator Controls

* The first account created becomes an administrator
* Existing installations promote the earliest account if no administrator exists
* Fullscreen user-management page
* Create standard or administrator accounts
* Change user passwords
* Delete user accounts
* Prevent deletion of the currently signed-in administrator
* Prevent deletion of the final administrator
* Database-level administrator permission checks

### Coding Tools

* Standard code editor
* Python notebook-style cells
* Open and save source files
* Run code from inside the application
* HTML preview in the default browser
* Python line-by-line execution tracing
* Variable-name, value, and type visualization
* Dark and light interface themes

The editor currently includes language options for:

* Python
* Python notebook mode
* JavaScript
* C
* C++
* Java
* HTML/CSS
* C#

C# appears in the interface but its execution runner has not yet been implemented.

### AI and Accessibility

* Local code explanations through Ollama
* Beginner-friendly runtime and compilation error explanations
* Structured error responses containing:

  * The likely offending line
  * A plain-language explanation
  * A helpful hint
* Error-line highlighting in the editor
* General code explanations through **Ask Code Lumi**
* Text-to-speech output using `pyttsx3`
* Optional animated mascot support
* `qwen2.5-coder:1.5b` used as the default Ollama model

## Requirements

* Python 3.10 or newer
* pip
* Ollama for AI explanations
* Node.js for JavaScript execution
* GCC for C execution
* G++ for C++ execution
* JDK for Java execution

Node.js, GCC, G++, and the JDK are optional if only Python will be used.

## Installation

### 1. Clone or open the repository

Open the `Code-Lumi-AI` project folder in Visual Studio Code.

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Ollama model

Install Ollama, then download the model used by Code Lumi AI:

```bash
ollama pull qwen2.5-coder:1.5b
```

Ensure the Ollama service is running before using the AI features.

### 5. Start Code Lumi AI

Run this command from the project root:

```bash
python main.py
```

## First Account and Administrator Access

On a new installation:

1. Open the signup page.
2. Create the first account.
3. The first account automatically receives the `admin` role.
4. Sign in using the new account.
5. Select **Manage Users** to open the administrator interface.

An administrator can:

* Review registered accounts
* Create new users
* Create additional administrators
* Change user passwords
* Delete eligible accounts

## Database

The SQLite database is stored at:

```text
data/code_lumi.db
```

The database schema is defined in:

```text
schema.sql
```

Database initialization and migrations are handled by:

```text
code_lumi/auth/database.py
```

The runtime database must not be committed because it contains account information and password hashes.

The following database files are excluded through `.gitignore`:

```text
data/*.db
data/*.db-shm
data/*.db-wal
```

## Keyboard Shortcuts

| Shortcut        | Action                        |
| --------------- | ----------------------------- |
| `F2`            | Save the current file         |
| `F3`            | Open a file                   |
| `Alt + F9`      | Run the current code          |
| `Shift + Enter` | Run the current notebook cell |

## Project Structure

```text
Code-Lumi-AI/
├── main.py
├── code_lumi/
│   ├── __init__.py
│   ├── analyzer/
│   │   ├── __init__.py
│   │   └── ollama_analyzer.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── tracer.py
│   └── ui/
│       ├── __init__.py
│       ├── admin_page.py
│       ├── animation_page.py
│       ├── login_window.py
│       └── main_window.py
├── data/
│   └── code_lumi.db
├── tests/
│   └── test_auth_database.py
├── schema.sql
├── requirements.txt
├── README.md
├── .gitignore
└── .gitattributes
```

## Component Responsibilities

| Component                     | Responsibility                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------ |
| `main.py`                     | Starts the application                                                         |
| `ui/main_window.py`           | Main editor, notebook, navigation, file handling, speech, and session behavior |
| `ui/login_window.py`          | Login and signup interface                                                     |
| `ui/admin_page.py`            | Administrator-page widgets                                                     |
| `ui/animation_page.py`        | Execution-animation widgets                                                    |
| `auth/database.py`            | Authentication, password hashing, roles, and user persistence                  |
| `execution/runner.py`         | Multi-language code execution                                                  |
| `execution/tracer.py`         | Python line and variable tracing                                               |
| `analyzer/ollama_analyzer.py` | Ollama prompts and structured AI responses                                     |
| `schema.sql`                  | SQLite user-table definition                                                   |

## Running Tests

Run the test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

The current tests verify:

* Account creation and login
* Duplicate-account rejection
* Incorrect-password rejection

## Current Limitations

Code Lumi AI is still under development.

Current limitations include:

* Student code is executed locally without a secure operating-system sandbox
* Execution does not currently enforce time or memory limits
* Long-running programs can make the interface unresponsive
* Python tracing currently focuses on executed lines and local variables
* Notebook cells do not share a persistent Python session
* C# execution is not implemented
* Tutorials, assignments, scoring, and rankings are not implemented
* Fullscreen and focus monitoring do not provide complete examination security

## Important Security Notice

Code entered in the editor is executed locally on the computer running Code Lumi AI.

Only run code from trusted sources. The current execution environment is not a security boundary for untrusted programs.
