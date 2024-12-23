# Task Management FastAPI Application

This is a simple task management API built using FastAPI. Users can create tasks, set due dates, and manage their task statuses. The project includes input validation, user authentication, and database integration.

# Features
    1.Create tasks with title, description, and due date.
    2.User-based task ownership.
    3.Validations for input fields like title, description, and due date.
    4.SQLAlchemy integration with PostgreSQL.

# Requirements

Ensure the following software is installed on your machine:
    -> Python (>=3.8)
    -> PostgreSQL
    -> Pip (Python package installer)
    -> Git (for cloning the repository)

# Setup Instructions
1. Clone the Repository:
    git clone <repository-url>
    cd TASK-MANAGEMENT

2. Set Up a Virtual Environment
Create and activate a virtual environment for Python dependencies.

    On Linux/Mac:
        python3 -m venv env
        source env/bin/activate

    On Windows:
        python -m venv env
        env\Scripts\activate

3. Install Dependencies
Use pip to install the required Python packages.
    pip install -r requirements.txt

4. Start the Application
Run the FastAPI application:
    uvicorn main:app --reload
By default, the server will start on http://127.0.0.1:8000.
Go to This route : Swagger UI: http://127.0.0.1:8000/docs
You will have all APIs Here


# API Documentation
FastAPI automatically generates interactive API documentation at the following endpoints:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

# How to Test
1. Create a User
Authenticate yourself by creating a user. You can use any pre-configured method or database entry for testing authentication.


2. Test Endpoints
Use tools like Postman, cURL, or the Swagger UI to test the API.

Example 1 : Create a Task
    Endpoint: POST /tasks

    Sample Request Body:
    {
        "title": "Complete Documentation",
        "description": "Prepare and finalize the documentation for the task management API.",
        "due_date": "2024-12-31"
    }

    Sample Response:
    {
        "detail": "USER SUCCESSFULLY CREATED NEW TASK"
    }

Example2: Update task status
    Request: PATCH /tasks/1
    {
        "status": 1  // 0 for in-progress, 1 for completed
    }

    Response (success):
    {
        "detail": "USER SUCCESSFULLY UPDATED STATUS OF THE TASK"
    }

Example 3: Deletes a task for a specific task ID.
    Endpoint:DELETE /tasks/1
    Request:
        DELETE /tasks/1

    Response (success):
    {
        "detail": "USER SUCCESSFULLY DELETED THE TASK"
    }




