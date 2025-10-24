"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import json
import uuid
from typing import Optional

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Session storage (in-memory for simplicity)
sessions = {}

# Load teacher credentials
current_dir = Path(__file__).parent
teachers_file = current_dir / "teachers.json"
with open(teachers_file, "r") as f:
    teachers_data = json.load(f)
    teachers = {t["username"]: t["password"] for t in teachers_data["teachers"]}

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    },
    "GitHub Skills": {
        "description": "Learn practical coding and collaboration skills with GitHub. Part of the GitHub Certifications program.",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 25,
        "participants": []
    }
}


# Helper function to get session from cookie
def get_session(request: Request) -> Optional[str]:
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return session_id
    return None


# Helper function to verify if user is authenticated
def is_authenticated(request: Request) -> bool:
    session_id = get_session(request)
    return session_id is not None


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/login")
def login(username: str, password: str, response: Response):
    """Login endpoint for teachers"""
    if username in teachers and teachers[username] == password:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"username": username}
        # Note: In production with HTTPS, add secure=True to the cookie
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return {"message": "Login successful", "username": username}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/logout")
def logout(request: Request, response: Response):
    """Logout endpoint"""
    session_id = get_session(request)
    if session_id:
        sessions.pop(session_id, None)
        response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}


@app.get("/auth/status")
def auth_status(request: Request):
    """Check if user is authenticated"""
    session_id = get_session(request)
    if session_id:
        return {"authenticated": True, "username": sessions[session_id]["username"]}
    return {"authenticated": False}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity (requires authentication)"""
    # Check if user is authenticated
    if not is_authenticated(request):
        raise HTTPException(status_code=403, detail="Authentication required")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity (requires authentication)"""
    # Check if user is authenticated
    if not is_authenticated(request):
        raise HTTPException(status_code=403, detail="Authentication required")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
