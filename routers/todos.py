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