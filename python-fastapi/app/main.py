from datetime import timedelta
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import EmailStr
from secrets import token_urlsafe
from starlette.middleware.sessions import SessionMiddleware
from typing import Annotated

from . import config, csrf, database, util
from .database import User, MagicLink

util.enable_stack_traces()

APP_DIR = Path(__file__).parent
CONFIG = config.load_generate(APP_DIR.parent / "data/config.json")
SESSION_LIFETIME = timedelta(days=CONFIG.session_days)
MAGIC_LINK_LIFETIME = timedelta(minutes=CONFIG.magic_link_minutes)
database.initialize(APP_DIR.parent / "data/database.sqlite")
csrf.initialize(CONFIG.csrf_secret_key)

templates = Jinja2Templates(directory=APP_DIR / "templates")

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=CONFIG.session_secret_key,
    max_age=int(SESSION_LIFETIME.total_seconds()),
    session_cookie="__Host-Http-session",
    https_only=True,
)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse, name="home_page")
def home_page(request: Request):
    user = User.get(request.session.get("email"))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,  # Can be None, if not logged in
        },
    )


@app.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={
        "csrf_token": csrf.get_token(request),
    })


@app.post("/login", response_class=HTMLResponse)
async def login_page_form(
    request: Request,
    email: Annotated[EmailStr, Form()],
    csrf_token: Annotated[str, Form()],
):
    csrf.validate_token(request, csrf_token)  # TODO: Consider using a Python package for CSRF tokens, instead of building it
    magic_link = MagicLink.create(email, MAGIC_LINK_LIFETIME)

    # TODO: Send email with magic link instead of logging it
    print(f"Generated magic link  {request.url_for("login_page")}/{magic_link.token}  for user  {email}")


    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/login/{magic_token}")
async def login_magic_link(request: Request, magic_token: str):
    if magic_link := MagicLink.get(magic_token):
        user = User.get_or_create(magic_link)
        MagicLink.delete(magic_link)
        request.session["email"] = user.email
        return RedirectResponse(request.url_for("user_page"), status_code=303)
    return RedirectResponse(request.url_for("login_page"), status_code=303)


async def logged_in_user(request: Request):
    result = User.get(request.session.get("email"))
    if not result:
        redirect = RedirectResponse(request.url_for("login_page"), status_code=303)
        raise HTTPException(redirect.status_code, "Not logged in!", redirect.headers)
    return result


@app.get("/user", response_class=HTMLResponse, name="user_page")
def user_page(request: Request, user: Annotated[User, Depends(logged_in_user)]):
    return templates.TemplateResponse(
        request=request,
        name="user.html",
        context={
            "user": user,
        },
    )
