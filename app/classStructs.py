from dataclasses import dataclass, field
from typing import TypedDict,Dict,Any,List,Optional
from pydantic import BaseModel,Field

class Mail(BaseModel):

    subject: str = ""
    sender: str = ""
    summary: str = ""

class MailList(BaseModel):
    mails: List[Mail]
@dataclass
class Calendar:
    Event_id: str = ""
    event: str = ""
    start: str = ""
    end: str = ""
    view:str = ""
    location:str = ""


class CalendarResponse(BaseModel):
    Event_id: str = ""
    summary: str = ""
    start: str = ""
    end: str = ""
    view:str = ""
    location:str = ""

class CalendarList(BaseModel):
    events: List[CalendarResponse]

class Transportation(BaseModel):
    info: str = ""
class WeatherInfo(BaseModel):
    hour: str = Field(description="Time of day (e.g., '09:00', '10:00')")
    temperature: str = Field(description="Temperature in Celsius")
    precipitation: str = Field(description="Precipitation in mm")

class Weather(BaseModel):
    hourly_weather: List[WeatherInfo]

class LocationCoordinates(BaseModel):
    latitude: float = 0
    longitude: float = 0

class MDdata(TypedDict):
    name:str
    location:str 
    work_location: List[Dict[str,Optional[str]]] 
    home_location: List[Dict[str,Optional[str]]] 
    dentist_location: List[Dict[str,Optional[str]]] 
    calendar_events: List[CalendarResponse]
    transportation_list: List[Transportation] 
    new_email: List[Mail]
    weather = List[WeatherInfo]


class BooleanResponse(BaseModel):
    is_valid: bool = Field(description="True if the answer is valid public transport directions, False otherwise")

