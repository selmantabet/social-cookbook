# The Social Cookbook

The Social Cookbook is a web application that allows users to share their recipes with the world. Users can create an account, log in, and post their recipes. They can also view other users' recipes, bookmark, comment and upvote/downvote them. The application is built using Flask, a Python web framework, and SQLite, a lightweight database engine.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

You may opt to use a virtual environment as follows:

On Windows (NT)

```bash
python -m venv venv
.\venv\Scripts\activate
```

On Linux/MacOS (POSIX)

```bash
python -m venv venv
source venv/bin/activate
```

Install the required packages using pip.

```bash
pip install -r requirements.txt
```

## Usage

Run the Flask application once the installation is complete. The application will be hosted on `localhost:5000` by default. To run the application, execute the following command in the terminal

```
flask run
```
