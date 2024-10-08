#!/usr/bin/python3
"""Weather Model to handle users"""
from models.base import BaseModel, Base
from sqlalchemy import Column, String, Float


class Weather(BaseModel, Base):
    """Weather model

    Args:
            BaseModel (class): the base model of class
            Base (declarative base): the table model
    """

    __tablename__ = "weathers"
    temperature = Column(Float, nullable=False)
    weather_condition = Column(String(128), nullable=False)
    wind_speed = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs:
            for key, value in kwargs.items():
                if key != "__class__" and hasattr(self, key):
                    setattr(self, key, value)
