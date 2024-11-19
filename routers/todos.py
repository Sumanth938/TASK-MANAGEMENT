from fastapi import BackgroundTasks,APIRouter,Depends,status, Request,HTTPException,Form,status,File,UploadFile
from sqlalchemy.orm import session
from fastapi import FastAPI,Depends,status,HTTPException,Query
from sqlalchemy.orm import session
from pydantic import BaseModel,Field, ValidationError
from fastapi.responses import JSONResponse,StreamingResponse
from pydantic import BaseModel

#models impors
from models.users import  User
from models.todos import Todos
from  models import Session

#single imports
import os,pytz,logging,io
from typing import List,Optional,Annotated
from datetime import datetime,date

#other imports
from .auth  import get_current_user
import utilities.logger as Logger
from routers.auth import get_password_hash,get_current_username

class TaskRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=100, description="The title of the task")
    description: str = Field(..., min_length=10, max_length=500, description="The description of the task")
    due_date: date = Field(..., description="The due date of the task; must be in the future")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete Documentation",
                "description": "Finalize and submit the project documentation for review.",
                "due_date": "2024-12-15"
            }
        }

error_logger = Logger.get_logger('error', logging.ERROR)
info_logger = Logger.get_logger('info', logging.INFO)

# models.Base.metadata.create_all(bind=engine)


router = APIRouter(
    prefix="/todos",
    tags=["Todos"],
    responses={401: {"user": "Not authorized"}}
)

def get_db():
    try:
        db = Session()
        yield db
    finally:
        db.close()

@router.get("/tasks")
async def get_all_tasks(sort_by: Optional[int] = None,page: Optional[int] = 1, size: Optional[int] = 20):
    """
    Retrieve all active tasks with optional sorting and pagination.

    Parameters:
    ----------
    sort_by : Optional[int] - Sort tasks by ID (1 for ascending, 2 for descending). Defaults to None.\n
    page : Optional[int] - The page number to retrieve. Defaults to 1.\n
    size : Optional[int]- Number of tasks per page. Defaults to 20.\n

    Returns:
    -------
    JSONResponse - A JSON response containing task data, status, and pagination details.
    """
    session = None
    try:
        session = Session()

        page = page - 1

        query = session.query(Todos).filter(Todos.is_active == True)

        if sort_by:
            if sort_by != 1 and sort_by != 2:
                return JSONResponse({"detail":"SORT BY MUST EITHER 1 OR 2"},status_code=403)

        if sort_by:
            if sort_by == 1:
                query = query.order_by(Todos.id.asc())
            elif sort_by == 2:
                query = query.order_by(Todos.id.desc())

        # Get total number of items
        total_items = query.count()

        # Calculate total pages
        total_pages = (total_items + size - 1) // size

        tasks = query.offset(page*size).limit(size).all()
        
        response = {
            "message": "SUCCESSFUL",
            "data": tasks,
            "status": 200,
            "pagination": {
                "current_page": page + 1,
                "items_per_page": size,
                "total_pages": total_pages,
                "total_items": total_items
            }
        }

        info_logger.info("Successfully fetched all tasks data  from database")
        return response
    except Exception as error:
        error_logger.exception(f"Error occurred in /GET_tasks/ API.Error:{error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(error))

    finally:
        if session:
            session.close()

@router.get("/tasks/{id}")
def get_task_by_id(id):
    """
    Retrieve a specific task by its ID if it is active.

    Parameters:
    ----------
    id : int - The ID of the task to retrieve.\n

    Returns:
    -------
    dict -  A dictionary containing the task details if found, along with a success message and status code.\n
    JSONResponse - A JSON response with an error message and a 404 status code if the task is not found.
    """
    session = None
    try:
        session = Session()
        task = session.query(Todos).filter(Todos.is_active == True,Todos.id == id).first()

        if task:
            info_logger.info("Sucessfully fetched task details sucessfully")
            return {"message": "SUCCESSFUL","data":task,"status_code":200}
        
        return JSONResponse({"detail": "INVALID ID,TASK NOT FOUND"}, status_code=404)
    except Exception as error:
        error_logger.exception(f"Error occurred in /GET_tasks_id/ API.Error:{error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(error))
    finally:
        if session:
            session.close()

@router.post("/tasks")
def create_new_task(request:TaskRequest,user: dict = Depends(get_current_user)):
    """
    Creates a new task in the system for the authenticated user.

    Validates the `due_date` to ensure it is in the future and associates the task with the authenticated user.
    If successful, returns a 201 response with a success message. If validation fails, appropriate error responses are returned.

    Parameters:
    - request (TaskRequest): The task details (title, description, due_date).\n
    - user (dict, optional): The authenticated user, injected by `Depends(get_current_user)`.\n

    Returns:
    - JSONResponse: A JSON response with a success or error message and an HTTP status code:
        - HTTP 201 if the task is successfully created.\n
        - HTTP 400 if the `due_date` is in the past.\n
        - HTTP 404 if the user is not found.\n
        - HTTP 500 if an internal error occurs.\n
    """
    session = None
    try:
        session = Session()
        task = session.query(Todos).filter(Todos.is_active == True).first()

        if not user:
            return {"message":"USER NOT FOUND", "status":status.HTTP_404_NOT_FOUND }
        
        info_logger.info(f"user with email {user.get('email')} has accessed the /POST_create_new_task_status API")

        # Validate due_date
        if request.due_date < date.today():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Due date must be in the future")

        task =Todos(
            title = request.title,
            description = request.description,
            due_date = request.due_date,
            created_by = user.get("email"),
            owner_id = user.get("user_id"),
        )

        session.add(task)
        session.commit()

        info_logger.info(f"User sucessfulyy created a new task ID:{task.id}")
        return JSONResponse({"detail":"USER SUCESSFULLY CREATED NEW TASK"},status_code=201)
    
    except Exception as error:
        error_logger.exception(f"Error occurred in /POST_create_new_task_status API.Error:{error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(error))
    finally:
        if session:
            session.close()

@router.put("/tasks/{task_id}", response_model=dict)
def update_task(task_id: int, request: TaskRequest, user: dict = Depends(get_current_user)):
    """
    Updates an existing task for the authenticated user.\n

    Validates if the task exists, is owned by the user, and is not already marked as "completed".
    Updates the task's title, description, and due date, then returns a success response.
    If any validation fails, appropriate error responses are returned.

    Parameters:
    - task_id (int): The ID of the task to be updated.\n
    - request (TaskRequest): The updated task details (title, description, due_date).\n
    - user (dict, optional): The authenticated user, injected by `Depends(get_current_user)`.\n

    Returns:
    - JSONResponse: A JSON response with a success or error message and an HTTP status code:\n
        - HTTP 200 if the task is successfully updated.\n
        - HTTP 400 if the task is already marked as "completed".\n
        - HTTP 404 if the task is not found or the user does not own it.\n
        - HTTP 500 if an internal error occurs.
    """
    session = None
    try:
        session = Session()

        # Check if user exists
        if not user:
            return {"message": "USER NOT FOUND", "status": status.HTTP_404_NOT_FOUND}

        info_logger.info(f"user with email {user.get('email')} is accessing the /PUT_update_task API for task ID {task_id}")

        # Find the task by ID and ownership
        task = session.query(Todos).filter(Todos.id == task_id, Todos.owner_id == user.get("user_id"), Todos.is_active == True).first()

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        if task.status == "completed":
            return JSONResponse({"detail","USER CANNOT UPDATED THIS TASK , TASK IS ALREADY COMPLETED"},status_code=400)

        # Update task fields
        task.title = request.title
        task.description = request.description
        task.due_date = request.due_date
        task.modified_by = user.get("email")

        session.commit()

        info_logger.info(f"User successfully updated task ID: {task_id}")
        return JSONResponse({"detail": "TASK SUCCESSFULLY UPDATED"}, status_code=200)

    except Exception as exc:
        error_logger.exception(f"Error occurred in /PUT_update_task API. Error: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    finally:
        if session:
            session.close()

@router.patch("/tasks/{id}")
def update_task_status(id,status:int,user: dict = Depends(get_current_user)):
    """
    Updates the status of a task for the authenticated user.\n

    Validates if the task exists, is owned by the user, and updates its status to either "in_progress" or "completed".\n
    Returns a success message if the task status is updated, or an error message if validation fails.\n

    Parameters:
    - id (int): The ID of the task to update.\n
    - status (int): The new status of the task (0 for "in_progress", 1 for "completed").\n
    - user (dict, optional): The authenticated user, injected by `Depends(get_current_user)`.\n

    Returns:
    - JSONResponse: A JSON response with a success or error message and an HTTP status code:\n
        - HTTP 200 if the task status is successfully updated.\n
        - HTTP 400 if the status is not 0 or 1.\n
        - HTTP 404 if the task is not found.\n
        - HTTP 403 if the user does not own the task.\n
        - HTTP 500 if an internal error occurs.\n
    """
    session = None
    try:
        session = Session()
        task = session.query(Todos).filter(Todos.is_active == True,Todos.id == id).first()

        if status !=0 and status !=1:
            return JSONResponse({"detail":"STATUS MUST BE 0 OR 1 "},status_code=400) 

        if not user:
            return {"message":"USER NOT FOUND", "status":status.HTTP_404_NOT_FOUND }
        
        if not task:
            return JSONResponse({"detail": "INVALID ID,TASK NOT FOUND"}, status_code=404)
        
        info_logger.info(f"user with email {user.get('email')} has accessed the /PATCH_task_update_task_status API")

        if task.owner_id != user.get("user_id"):
            return JSONResponse({"detail":"YOU CANNOT UPDATE STATUS OF THIS TASK,YOUR NOT OWNER OF THIS TASK"},status_code=403)
        
        task.status = "in_progress" if status == 0 else "completed"
        session.commit()

        info_logger.info(f"User Sucessfully deleted the task ID:{id}")
        return JSONResponse({"detail": "USER SUCCESSFULY UPDATED STATUS OF THE TASK"},status_code=200)
        
        
    except Exception as exc:
        error_logger.exception(f"Error occurred in /PATCH_task_update_task_status API.Error:{exc}")
        raise HTTPException(status_code=500,detail=str(exc))
    finally:
        if session:
            session.close()

@router.delete("/tasks/{id}")
def delete_task_by_id(id,user: dict = Depends(get_current_user)):
    """
    Delete a specific task by ID if the user is the owner.

    Parameters:
    ----------
    id : int\n
        The ID of the task to delete.
    user : dict
        The current user (retrieved from authentication).

    Returns:
    -------
    JSONResponse\n
        A success or error message based on the result.
    """
    session = None
    try:
        session = Session()
        task = session.query(Todos).filter(Todos.is_active == True).first()

        if not user:
            return {"message":"user not found", "status":status.HTTP_404_NOT_FOUND }
        
        if not task:
            return JSONResponse({"detail": "INVALID ID,TASK NOT FOUND"}, status_code=404)
        
        info_logger.info(f"user with email {user.get('email')} has accessed the /DELETE_task_by_id API")

        if task.owner_id != user.get("user_id"):
            return JSONResponse({"detail":"YOU CANNOT DELETE THIS TASK,YOUR NOT OWNER OF THIS TASK"},status_code=403)
        
        task.is_active = False
        session.commit()

        info_logger.info(f"User Sucessfully deleted the task ID:{id}")
        return JSONResponse({"detail": "USER SUCCESSFULY DELTED THE TASK"},status_code=204)
        
        
    except Exception as error:
        error_logger.exception(f"Error occurred in /GET_tasks_id/ API.Error:{error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(error))
    finally:
        if session:
            session.close()