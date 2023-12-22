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
import graphene
from graphene import ObjectType,  List, Schema
from graphene import String as GString
from graphene import Float as GFloat

FOOD_LOOKUP_DB = {
    "apple": {"unit_calorie_g": 0.37},  # 37 kcal per 100g
    "banana": {"unit_calorie_g": 0.51},  # 51 kcal per 100g
    "orange": {"unit_calorie_g": 0.39},  # Approximate value
    "rice_brown": {"unit_calorie_g": 1.32},  # 132 kcal per 100g (cooked)
    "chicken_breast": {"unit_calorie_g": 1.48},  # 148 kcal per 100g
    "broccoli": {"unit_calorie_g": 0.35},  # 35 kcal per 100g
    "carrot": {"unit_calorie_g": 0.10},  # 10 kcal per 100g
    "cheddar_cheese": {"unit_calorie_g": 4.03},  # 403 kcal per 100g
    "salmon_raw": {"unit_calorie_g": 1.83},  # 183 kcal per 100g
    "egg_whole": {"unit_calorie_g": 1.55},  # 155 kcal per 100g
    "almonds": {"unit_calorie_g": 5.75},  # 575 kcal per 100g
    "pasta_cooked": {"unit_calorie_g": 1.58},
    "spinach": {"unit_calorie_g": 0.24},  # 24 kcal per 100g
    "avocado": {"unit_calorie_g": 1.34},  # 134 kcal per 100g
    "tofu": {"unit_calorie_g": 0.76},  # 76 kcal per 100g
    "potato": {"unit_calorie_g": 0.97},  # 97 kcal per 100g
    "beef_steak": {"unit_calorie_g": 2.52},  # 252 kcal per 100g
    "whole_milk": {"unit_calorie_g": 0.62},  # 62 kcal per 100mL
    "oats": {"unit_calorie_g": 3.81},  # 381 kcal per 100g (rolled oats)
    "peanut_butter": {"unit_calorie_g": 5.94},
    "quinoa": {"unit_calorie_g": 1.11},  # 111 kcal per 100g (cooked)
    "lentils": {"unit_calorie_g": 1.16},  # 116 kcal per 100g (cooked)
    "chickpeas": {"unit_calorie_g": 1.64},  # 164 kcal per 100g (cooked)
    "turkey_breast": {"unit_calorie_g": 1.04},  # 104 kcal per 100g
    "salmon": {"unit_calorie_g": 2.08},  # 208 kcal per 100g
    "sweet_potato": {"unit_calorie_g": 0.86},  # 86 kcal per 100g
    "blueberries": {"unit_calorie_g": 0.57},  # 57 kcal per 100g
    "almond_milk": {"unit_calorie_g": 0.17},
    "blackberries": {"unit_calorie_g": 0.21},  # 21 kcal per 100g
    "cucumber": {"unit_calorie_g": 0.15},  # 15 kcal per 100g
    "tomato": {"unit_calorie_g": 0.18},  # 18 kcal per 100g
    "mushroom": {"unit_calorie_g": 0.08},  # 8 kcal per 100g
    "cauliflower": {"unit_calorie_g": 0.30},  # 30 kcal per 100g
    "green_peas": {"unit_calorie_g": 0.70},  # 70 kcal per 100g
    "pumpkin": {"unit_calorie_g": 0.13},
    "strawberries": {"unit_calorie_g": 0.32},  # 32 kcal per 100g
    "spinach": {"unit_calorie_g": 0.23},  # 23 kcal per 100g
    "walnuts": {"unit_calorie_g": 6.54},  # 654 kcal per 100g
    "cod": {"unit_calorie_g": 0.82},  # 82 kcal per 100g
    "shrimp": {"unit_calorie_g": 0.99},  # 99 kcal per 100g
    "beef": {"unit_calorie_g": 2.50},  # 250 kcal per 100g
    "pork": {"unit_calorie_g": 2.42},
    "olive_oil": {"unit_calorie_g": 8.80},  # 880 kcal per 100g
    "bread_whole_grain": {"unit_calorie_g": 2.66},  # 266 kcal per 100g
    "yogurt_plain": {"unit_calorie_g": 0.59},  # 59 kcal per 100g
    "lamb": {"unit_calorie_g": 2.94},  # 294 kcal per 100g
    "honey": {"unit_calorie_g": 3.04},  # 304 kcal per 100g
    "cheddar_cheese": {"unit_calorie_g": 4.03}
}

EXERCISE_LOOKUP_DB = {
    "running": {"calories_burned_per_minute": 606 / 60},  # 10.1 calories per minute
    "cycling": {"calories_burned_per_minute": 292 / 60},  # 4.87 calories per minute
    "swimming": {"calories_burned_per_minute": 423 / 60},  # 7.05 calories per minute
    "yoga": {"calories_burned_per_minute": 183 / 60},  # 3.05 calories per minute (moderate effort)
    "weightlifting": {"calories_burned_per_minute": 108 / 60},  # 1.8 calories per minute
    "aerobics_low_impact": {"calories_burned_per_minute": 365 / 60},  # 6.08 calories per minute
    "aerobics_water": {"calories_burned_per_minute": 402 / 60},  # 6.7 calories per minute
    "dancing_ballroom": {"calories_burned_per_minute": 219 / 60},  # 3.65 calories per minute
    "elliptical_trainer": {"calories_burned_per_minute": 365 / 60},  # 6.08 calories per minute
    "golfing": {"calories_burned_per_minute": 314 / 60},  # 5.23 calories per minute
    "hiking": {"calories_burned_per_minute": 438 / 60},  # 7.3 calories per minute
    "skiing_downhill": {"calories_burned_per_minute": 314 / 60},  # 5.23 calories per minute
    "walking": {"calories_burned_per_minute": 314 / 60} ,
    "jogging": {"calories_burned_per_minute": 450 / 60},  # 7.5 calories per minute
    "tennis": {"calories_burned_per_minute": 480 / 60},  # 8.0 calories per minute
    "basketball": {"calories_burned_per_minute": 584 / 60},  # 9.73 calories per minute
    "soccer": {"calories_burned_per_minute": 504 / 60},  # 8.4 calories per minute
    "zumba": {"calories_burned_per_minute": 350 / 60},  # 5.83 calories per minute
    "crossfit": {"calories_burned_per_minute": 500 / 60},  # 8.33 calories per minute
    "rock_climbing": {"calories_burned_per_minute": 550 / 60}
    # 5.23 calories per minute (3.5 mph)
}

class FoodItem(ObjectType):
    food_type = GString()
    unit_calorie_g = GFloat()

# Query Class
class Query(ObjectType):
    list_all_foods = List(GString)
    get_unit_calories = graphene.Field(GFloat, food_type=graphene.Argument(GString))

    def resolve_list_all_foods(root, info):
        return list(FOOD_LOOKUP_DB.keys())

    def resolve_get_unit_calories(root, info, food_type):
        food_data = FOOD_LOOKUP_DB.get(food_type)
        if food_data:
            return food_data['unit_calorie_g']
        return None

# Mutation Class
class CreateFoodItem(graphene.Mutation):
    class Arguments:
        food_type = GString(required=True)
        unit_calorie_g = GFloat(required=True)

    food_item = graphene.Field(FoodItem)

    def mutate(self, info, food_type, unit_calorie_g):
        FOOD_LOOKUP_DB[food_type] = {"unit_calorie_g": unit_calorie_g}
        return CreateFoodItem(food_item=FoodItem(food_type=food_type, unit_calorie_g=unit_calorie_g))

# Mutation ObjectType
class Mutation(ObjectType):
    create_food_item = CreateFoodItem.Field()

# Schema
schema = Schema(query=Query, mutation=Mutation)


# ExerciseItem Type
class ExerciseItem(ObjectType):
    exercise_type = GString()
    calories_burned_per_minute = GFloat()

# Query Class
class ExerciseQuery(ObjectType):
    list_all_exercises = List(GString)
    get_calories_burned = graphene.Field(GFloat, exercise_type=GString())

    def resolve_list_all_exercises(root, info):
        return list(EXERCISE_LOOKUP_DB.keys())

    def resolve_get_calories_burned(root, info, exercise_type):
        exercise_data = EXERCISE_LOOKUP_DB.get(exercise_type)
        if exercise_data:
            return exercise_data['calories_burned_per_minute']
        return None

# Mutation Class
class CreateExerciseItem(graphene.Mutation):
    class Arguments:
        exercise_type = GString(required=True)
        calories_burned_per_minute = GFloat(required=True)

    exercise_item = graphene.Field(ExerciseItem)

    def mutate(self, info, exercise_type, calories_burned_per_minute):
        EXERCISE_LOOKUP_DB[exercise_type] = {"calories_burned_per_minute": calories_burned_per_minute}
        return CreateExerciseItem(exercise_item=ExerciseItem(exercise_type=exercise_type, calories_burned_per_minute=calories_burned_per_minute))

# Mutation ObjectType
class ExerciseMutation(ObjectType):
    create_exercise_item = CreateExerciseItem.Field()

# Schema
exercise_schema = Schema(query=ExerciseQuery, mutation=ExerciseMutation)


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
    food_calories = relationship("FoodCalories", back_populates="user")
    exercise_calories = relationship("ExerciseCalories", back_populates="user")


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

class FoodCalories(Base):
    __tablename__ = 'food_calories'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)
    food = Column(String(50), primary_key=True, index=True)
    gram = Column(Float, nullable=False)
    calories = Column(Float, primary_key=True, index=True)

    user = relationship("User", back_populates="food_calories")


class ExerciseCalories(Base):
    __tablename__ = 'exercise_calories'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)
    exercise = Column(String(50), primary_key=True, index=True)
    minute = Column(Float, nullable=False)
    calories = Column(Float, primary_key=True, index=True)

    user = relationship("User", back_populates="exercise_calories")

class FoodCaloriesBase(BaseModel):
    user_id: int
    timestamp: datetime
    food: str
    gram: float
    calories: float

    class Config:
        orm_mode = True


class ExerciseCaloriesBase(BaseModel):
    user_id: int
    timestamp: datetime
    exercise: str
    minute: float
    calories: float


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
@app.get("/user_email/{email}/calories")
async def find_user3(email:str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        await add_new_user(email, db)
        user = db.query(User).filter(User.email == email).first()

    return RedirectResponse(url=f"/users/{user.user_id}/calories", status_code=303)

@app.get("/user/calories")
async def user_calories(request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == current_user_id).first()

    food_records = (
        db.query(FoodCalories)
        .filter(FoodCalories.user_id == user.user_id)
        .all()
    )

    # if not food_records:
    #     raise HTTPException(status_code=404, detail="No food records found for this user")

    food_result = []
    for record in food_records:
        food_result.append({
            "timestamp": record.timestamp,
            "food": record.food,
            "gram": record.gram,
            "calories": record.calories,
        })

    exercise_records = (
        db.query(ExerciseCalories)
        .filter(ExerciseCalories.user_id == user.user_id)
        .all()
    )

    # if not exercise_records:
    #     raise HTTPException(status_code=404, detail="No exercise records found for this user")

    exercise_result = []
    for record in exercise_records:
        exercise_result.append({
            "timestamp": record.timestamp,
            "exercise": record.exercise,
            "minute": record.minute,
            "calories": record.calories,
        })

    query_all_foods = '{ listAllFoods }'
    all_food = schema.execute(query_all_foods)

    query_all_exercises = '{ listAllExercises }'
    all_exercise = exercise_schema.execute(query_all_exercises)

    food_options = all_food.data['listAllFoods']
    exercise_options = all_exercise.data['listAllExercises']  # Add or fetch from DB as needed

    return templates.TemplateResponse("user_calories.html", {
            "request": request,
            "user": user,
            "food_records": food_records,
            "exercise_records": exercise_records,
            "food_options": food_options,  # passing the food options to the template
            "exercise_options": exercise_options  # passing the exercise options to the template
        })

@app.get("/users/{user_id}/calories")
async def get_user_id3(user_id:int):
    global current_user_id
    current_user_id = user_id
    return RedirectResponse(url=f"/user/calories", status_code=303)

@app.post("/users/{user_id}/calories/food/add")
async def add_food_record(user_id: int,
                    food: str = Form(...),
                    gram: float = Form(...),
                    db: Session = Depends(get_db)):

    timestamp = datetime.now()

    query_calories = '{{ getUnitCalories(foodType: "{}") }}'.format(food)
    result = schema.execute(query_calories)
    unit_calories = result.data['getUnitCalories']

    cal = unit_calories*gram

    new_food_record = FoodCalories(
        user_id = user_id,
        timestamp = timestamp,
        food = food,
        gram = gram,
        calories = cal
    )
    print(new_food_record)
    db.add(new_food_record)
    db.commit()
    # db.refresh(new_food_record)
    print("food record added")
    return RedirectResponse(url=f"/users/{user_id}/calories", status_code=303)


@app.post("/users/{user_id}/calories/exercise/add")
async def add_exercise_record(user_id: int,
                    exercise: str = Form(...),
                    minute: float = Form(...),
                    db: Session = Depends(get_db)):
    timestamp = datetime.now()

    query_exercise_calories = '{{ getCaloriesBurned(exerciseType: "{}") }}'.format("cycling")
    result = exercise_schema.execute(query_exercise_calories)
    unit_calories = result.data['getCaloriesBurned']

    new_exercise_record = ExerciseCalories(
        user_id = user_id,
        timestamp = timestamp,
        exercise = exercise,
        minute = minute,
        calories = unit_calories*minute
    )
    db.add(new_exercise_record)
    db.commit()
    # db.refresh(new_exercise_record)
    print("exercise record added")
    return RedirectResponse(url=f"/users/{user_id}/calories", status_code=303)

@app.post("/users/{user_id}/calories/food/request_delete")
async def request_to_delete_food(user_id: int,
                      delete_timestamp: str = Form(...),
                      delete_food: str = Form(...),
                      db: Session = Depends(get_db)):

    await delete_food_record(user_id, delete_timestamp, delete_food, db)
    return RedirectResponse(url=f"/users/{user_id}/calories", status_code=303)


@app.delete("/users/{user_id}/calories/food/delete")
async def delete_food_record(user_id: int, timestamp: str, food: str, db: Session = Depends(get_db)):

    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    food_record = db.query(FoodCalories).filter(
        FoodCalories.user_id == user_id,
        FoodCalories.timestamp == timestamp,
        FoodCalories.food == food
    ).first()

    if not food_record:
        raise HTTPException(status_code=404, detail="Body metric record not found")

    db.delete(food_record)
    db.commit()
    print("deleted!")
    return "food record deleted"

@app.post("/users/{user_id}/calories/exercise/request_delete")
async def request_to_delete_exercise(user_id: int,
                      delete_timestamp: str = Form(...),
                      delete_exercise: str = Form(...),
                      db: Session = Depends(get_db)):

    await delete_exercise_record(user_id, delete_timestamp, delete_exercise, db)
    return RedirectResponse(url=f"/users/{user_id}/calories", status_code=303)


@app.delete("/users/{user_id}/calories/exercise/delete")
async def delete_exercise_record(user_id: int, timestamp: str, exercise: str, db: Session = Depends(get_db)):

    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

    exercise_record = db.query(ExerciseCalories).filter(
        ExerciseCalories.user_id == user_id,
        ExerciseCalories.timestamp == timestamp,
        ExerciseCalories.exercise == exercise
    ).first()

    if not exercise_record:
        raise HTTPException(status_code=404, detail="Body metric record not found")

    db.delete(exercise_record)
    db.commit()
    print("deleted!")
    return "exercise record deleted"

if __name__ == "__main__":
    # uvicorn.run(app, host="localhost", port=8012)
    uvicorn.run(app, host="0.0.0.0", port=8012)