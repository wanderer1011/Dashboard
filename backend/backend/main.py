from Routes.Auth.cookie import set_cookie
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from Routes.TimeTable.timetable import router as timetable_router
from Routes.TimeTable.cr import router as cr_router
from Routes.TimeTable.custom import router as custom_router
from Routes.TimeTable.changes import router as changes_router
from Routes.Auth.controller import router as auth_router
from Routes.CabSharing.controller import app as cab_router
from Routes.User.controller import router as user_router
from Routes.Auth.tokens import verify_token
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI()

# TODO: change for prod
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(timetable_router)
app.include_router(auth_router)
app.include_router(cr_router)
app.include_router(custom_router)
app.include_router(changes_router)
app.include_router(cab_router)
app.include_router(user_router)


async def cookie_verification_middleware(request: Request, call_next):
    token = request.cookies.get("session")
    if token:
        status, data = verify_token(token)
        if not status:
            resp = JSONResponse(status_code=401, content={"detail": data})
            set_cookie(value="", days_expire=0, key="session", response=resp)
            return resp
        request.state.user_id = data["sub"]  # Store user_id in request state
    else:
        return JSONResponse(status_code=401, content={"detail": "Session cookie is missing"})
    
    response = await call_next(request)
    
    #updating the cookie
    set_cookie(response=response, key="session", value=token, days_expire=15)
    return response


@app.middleware("http")
async def apply_middleware(request: Request, call_next):
    excluded_routes = ["/auth/login", "/auth/access_token"]  # Add routes to exclude guard here

    if request.url.path not in excluded_routes:
        return await cookie_verification_middleware(request, call_next)
    else:
        response = await call_next(request)
        return response

@app.get("/")
async def root():
    return {"message": f"hello dashboard"}

@app.get("/protected-data")
def get_protected_data():
    return {"user": "verified"}