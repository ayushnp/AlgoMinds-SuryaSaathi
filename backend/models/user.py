from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


# --- MongoDB ObjectId Custom Type ---

# Custom class to handle mapping between MongoDB's ObjectId and Pydantic string
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        field_schema.update(type="string")


# --- User Base Models ---

class UserModel(BaseModel):
    """Base model for a user in the database."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    hashed_password: str
    full_name: str
    phone_number: str
    is_active: bool = True

    class Config:
        # Allows for field population using the MongoDB _id alias
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        # Use str() for ObjectId to handle serialization to JSON


class UserCreate(BaseModel):
    """Model for user registration input."""
    email: EmailStr
    password: str
    full_name: str
    phone_number: str


class UserLogin(BaseModel):
    """Model for user login input."""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Model for user output (excludes sensitive info like password hash)."""
    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str

    class Config:
        json_encoders = {ObjectId: str}
        orm_mode = True  # Use orm_mode for reading data from the DB