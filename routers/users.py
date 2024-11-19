from fastapi import BackgroundTasks,APIRouter,Depends,status, Request,HTTPException,Form,status,File,UploadFile
from sqlalchemy.orm import session
from fastapi import FastAPI,Depends,status,HTTPException,Query
from sqlalchemy.orm import session
from pydantic import BaseModel
from fastapi.responses import JSONResponse,StreamingResponse
from pydantic import BaseModel

#models impors
from models.users import  User
from  models import Session

#single imports
import os,pytz,logging,io
from typing import List,Optional,Annotated
from datetime import datetime

#other imports
from .auth  import get_current_user
import utilities.logger as Logger
from routers.auth import get_password_hash,get_current_username

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

error_logger = Logger.get_logger('error', logging.ERROR)
info_logger = Logger.get_logger('info', logging.INFO)

# models.Base.metadata.create_all(bind=engine)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={401: {"user": "Not authorized"}}
)

def get_db():
    try:
        db = Session()
        yield db
    finally:
        db.close()

@router.get("/")
async def logined_user(db: session = Depends(get_db),user: dict = Depends(get_current_user)):

    try:

        if user is None:
            return {"message":"user not found", "status":status.HTTP_404_NOT_FOUND }

        info_logger.info(f"user with email {user.get('email')} has accessed the get_logined_user API")
        db_user = db.query(User).filter(User.is_active == True, User.id == user.get("user_id")).first()

        info_logger.info(f'Successfully fetched user details from database')
        return {"message": "successful",
                "data":{
                "user_details":db_user
                },
                "status":status.HTTP_200_OK }

    except Exception as error:
        error_logger.exception(f"Error occurred in get_logined_user API.Error:{error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(error))

    finally:
        if db:
            db.close()
