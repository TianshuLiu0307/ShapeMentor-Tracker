from fastapi import FastAPI, Request, Depends, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, func, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
import uvicorn

# Database configuration
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://admin:shapementor@shapementor-rds.cuorsbapmndf.us-east-2.rds.amazonaws.com/ShapeMentor"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy User model
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hashed_password = Column(String(255), nullable=False)
    activated = Column(Boolean, nullable=False)
    user_name = Column(String(255))
    dob = Column(Date)
    gender = Column(String(50))
    race = Column(String(50))
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    body_metrics = relationship("BodyMetrics", back_populates="user")

# Pydantic models
class UserCreateModel(BaseModel):
    user_id: int
    user_name: str
    dob: Optional[date]
    gender: Optional[str]
    race: Optional[str]
    email: str
    phone_number: Optional[str]
    class Config:
        orm_mode = True

class UserUpdateModel(BaseModel):
    user_id: int
    user_name: str
    dob: Optional[date]
    gender: Optional[str]
    race: Optional[str]
    email: str
    phone_number: Optional[str]
    class Config:
        orm_mode = True

class UserResponseModel(BaseModel):
    user_id: int
    user_name: str
    dob: Optional[date]
    gender: Optional[str]
    race: Optional[str]
    email: str
    phone_number: Optional[str]
    class Config:
        orm_mode = True

class BodyMetrics(Base):
    __tablename__ = "body_metrics"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), primary_key=True, index=True)
    metric_index = Column(String(50), ForeignKey("body_metrics_lookup.metric_index"), primary_key=True, index=True)
    value = Column(Float, nullable=False)
    user = relationship("User", back_populates="body_metrics")
    metric = relationship("BodyMetricsLookup", back_populates="body_metrics")

class BodyMetricsLookup(Base):
    __tablename__ = "body_metrics_lookup"
    metric_index = Column(String(50), primary_key=True)
    metric_name = Column(String(255), nullable=False)
    metric_unit = Column(String(50), nullable=False)
    body_metrics = relationship("BodyMetrics", back_populates="metric")

class BodyMetricsResponseModel(BaseModel):
    user_id: int
    timestamp: datetime
    metric_index: str
    value: float

class BodyMetricsCreateModel(BaseModel):
    metric_index: str
    value: float

# FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        print("request middleware!")
        response = await call_next(request)
    finally:
        request.state.db.close()
        print("close middleware!")
    return response

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return "Hello Tracker"

# user profile api
@app.get("/user_email/{email}/profile")
async def find_user1(email:str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        await add_new_user(email, db)
        user = db.query(User).filter(User.email == email).first()

    return RedirectResponse(url=f"/users/{user.user_id}/profile", status_code=303)

@app.get("/user/profile")
async def user_profile(request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == current_user_id).first()
    return templates.TemplateResponse("user_profile.html", {"request": request, "user": user})


@app.get("/users/{user_id}/profile")
async def get_user_id1(user_id:int):
    global current_user_id
    current_user_id = user_id
    return RedirectResponse(url=f"/user/profile", status_code=303)

@app.post("/users/{user_id}/profile/add")
async def add_new_user(email:str, db: Session = Depends(get_db)):
    max_id = db.query(func.max(User.user_id)).scalar()
    user_id = (max_id or 0) + 1
    user_name = email.split("@")[0]
    new_user = User(
        user_id=user_id,
        user_name=user_name,
        email=email,
        hashed_password="password",  # Replace with real hash
        activated=True,  # Assuming default activation status
        dob=None,
        gender=None,
        race=None,
        phone_number=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print("new user created")
    return "new user created"

@app.post("/users/{user_id}/profile/request_edit")
async def request_to_update_user(user_id:int,
    new_user_name: str = Form(...),
    new_email: str = Form(...),
    new_dob: date = Form(None),
    new_gender: str = Form(None),
    new_race: str = Form(None),
    new_phone_number: str = Form(None),
    db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == current_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_user = UserUpdateModel(
        user_id=current_user_id,
        user_name=new_user_name,
        email=new_email,
        dob=new_dob,
        gender=new_gender,
        race=new_race,
        phone_number=new_phone_number
    )
    await update_user(new_user, db)
    return RedirectResponse(url=f"/users/{user_id}/profile", status_code=303)

@app.put("/users/{user_id}/profile/edit")
async def update_user(user_data: UserUpdateModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    print("updated!")
    return "updated"

# metrics api
@app.get("/user_email/{email}/metrics")
async def find_user2(email:str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        await add_new_user(email, db)
        user = db.query(User).filter(User.email == email).first()

    return RedirectResponse(url=f"/users/{user.user_id}/metrics", status_code=303)

@app.get("/user/metrics")
async def user_metrics(request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == current_user_id).first()
    body_metrics_records = (
        db.query(BodyMetrics)
        .filter(BodyMetrics.user_id == user.user_id)
        .options(joinedload(BodyMetrics.metric))
        .all()
    )

    if not body_metrics_records:
        raise HTTPException(status_code=404, detail="No body metrics records found for this user")

    result = []
    for record in body_metrics_records:
        result.append({
            "timestamp": record.timestamp,
            "metric_index": record.metric_index,
            "value": record.value,
            "metric_name": record.metric.metric_name,  # Access metric_name through the relationship
            "metric_unit": record.metric.metric_unit,  # Access metric_unit through the relationship
        })

    return templates.TemplateResponse("user_body_metrics.html", {"request": request, "user": user, "body_metrics": result})


@app.get("/users/{user_id}/metrics")
async def get_user_id2(user_id:int):
    global current_user_id
    current_user_id = user_id
    return RedirectResponse(url=f"/user/metrics", status_code=303)

@app.post("/users/{user_id}/metrics/add")
async def add_body_metric(user_id: int,
                    metric_index: int = Form(...),
                    value: float = Form(...),
                    db: Session = Depends(get_db)):
    timestamp = datetime.now()
    new_metric = BodyMetrics(
        user_id = user_id,
        timestamp = timestamp,
        metric_index = metric_index,
        value = value
    )
    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)
    print("metric added")
    return RedirectResponse(url=f"/users/{user_id}/metrics", status_code=303)


@app.post("/users/{user_id}/metrics/request_delete")
async def request_to_delete_metric(user_id: int,
                      delete_timestamp: str = Form(...),
                      delete_metric_index: str = Form(...),
                      db: Session = Depends(get_db)):

    await delete_body_metric(user_id, delete_timestamp, delete_metric_index, db)
    return RedirectResponse(url=f"/users/{user_id}/metrics", status_code=303)

@app.delete("/users/{user_id}/metrics/delete")
async def delete_body_metric(user_id: int, timestamp: str, metric_index: str, db: Session = Depends(get_db)):

    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    metric_record = db.query(BodyMetrics).filter(
        BodyMetrics.user_id == user_id,
        BodyMetrics.timestamp == timestamp,
        BodyMetrics.metric_index == metric_index
    ).first()

    if not metric_record:
        raise HTTPException(status_code=404, detail="Body metric record not found")

    db.delete(metric_record)
    db.commit()
    print("deleted!")
    return "metric deleted"


# calories api
# @app.get("/user_email/{email}/calories")
# async def find_user3(email:str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         await add_new_user(email, db)
#         user = db.query(User).filter(User.email == email).first()
#
#     return RedirectResponse(url=f"/users/{user.user_id}/calories", status_code=303)

# @app.get("/user/calories")
#
# @app.get("/users/{user_id}/calories")
#
# @app.post("/users/{user_id}/calories/add")
#
# @app.post("/users/{user_id}/calories/request_delete")
#
# @app.delete("/users/{user_id}/calories/delete")


if __name__ == "__main__":
    # uvicorn.run(app, host="localhost", port=8012)
    uvicorn.run(app, host="0.0.0.0", port=8012)