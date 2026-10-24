from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select

from app.routers import users, tweets, medias
from app.database import async_session
from app.models import User


async def create_initial_users():
    """Создает тестовых пользователей при пустой базе данных"""
    async with async_session() as session:
        result = await session.execute(select(User))
        if not result.scalars().first():
            user1 = User(name="Тест1", api_key="test")
            user2 = User(name="Тест2", api_key="admin")
            session.add_all([user1, user2])
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется при старте приложения"""
    await create_initial_users()
    yield


app = FastAPI(
    title="Сервис микроблогов",
    description="Корпоративный сервис микроблогов",
    version="1.0.0",
    lifespan=lifespan
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Перехватывает ошибки и возвращает их"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": False,
            "error_type": "ClientError",
            "error_message": exc.detail
        }
    )


app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/img", StaticFiles(directory="static/img"), name="img")

app.include_router(users.router)
app.include_router(tweets.router)
app.include_router(medias.router)


@app.get("/", response_class=FileResponse, tags=["Интерфейс"], summary="Главная страница")
async def root() -> FileResponse:
    """Возвращает главную страницу"""
    return FileResponse("static/index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    """Отдает иконку сайта"""
    return FileResponse("static/img/favicon.ico")
