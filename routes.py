import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder

load_dotenv()

app = FastAPI()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MongoDB URI is not set in the environment variables.")

client = AsyncIOMotorClient(MONGO_URI)
db = client.student_db
students_collection = db.students

class Address(BaseModel):
    city: str
    country: str

class Student(BaseModel):
    name: str
    age: int
    address: Address

class UpdateStudent(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    address: Optional[Address] = None

def student_helper(student) -> dict:
    return {
        "id": str(student["_id"]),
        "name": student["name"],
        "age": student["age"],
        "address": student["address"]
    }

@app.post("/students", status_code=201)
async def create_student(student: Student):
    student_data = jsonable_encoder(student)
    result = await students_collection.insert_one(student_data)
    return {"id": str(result.inserted_id)}

@app.get("/students", response_model=dict)
async def list_students(country: Optional[str] = None, age: Optional[int] = None):
    filter = {}
    if country:
        filter["address.country"] = country
    if age:
        filter["age"] = {"$gte": age}
    
    students = []
    async for student in students_collection.find(filter):
        students.append(student_helper(student))
    return {"data": students}

@app.get("/students/{id}", response_model=Student)
async def get_student(id: str):
    student = await students_collection.find_one({"_id": ObjectId(id)})
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_helper(student)

@app.patch("/students/{id}", status_code=204)
async def update_student(id: str, update_data: UpdateStudent):
    update_dict = jsonable_encoder(update_data, exclude_unset=True)
    result = await students_collection.update_one({"_id": ObjectId(id)}, {"$set": update_dict})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {}

@app.delete("/students/{id}", status_code=200)
async def delete_student(id: str):
    result = await students_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return {"message": "Student deleted successfully"}
