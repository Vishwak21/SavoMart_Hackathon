from typing import Literal

from pydantic import BaseModel

DemoRole = Literal[
    "bd_manager",
    "bd_executive",
    "survey_manager",
    "survey_executive",
]

DEMO_USERS = [
    {
        "id": "bd-manager",
        "name": "Arjun Raman",
        "email": "arjun.raman@savomart.demo",
        "role": "bd_manager",
        "title": "BD Manager",
    },
    {
        "id": "bd-executive",
        "name": "Meera Kumar",
        "email": "meera.kumar@savomart.demo",
        "role": "bd_executive",
        "title": "BD Executive",
    },
    {
        "id": "survey-manager",
        "name": "Nila Shankar",
        "email": "nila.shankar@savomart.demo",
        "role": "survey_manager",
        "title": "Survey Manager",
    },
    {
        "id": "survey-executive",
        "name": "Kavin Raj",
        "email": "kavin.raj@savomart.demo",
        "role": "survey_executive",
        "title": "Survey Executive",
    },
]


class DemoUser(BaseModel):
    id: str
    name: str
    email: str
    role: DemoRole
    title: str