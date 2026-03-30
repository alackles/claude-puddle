from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.db.connection import open_db, close_db, get_db
from app.db.migrations import init_schema
from app.auth.router import router as auth_router
from app.conversations.router import router as conversations_router
from app.conversations.sharing import router as sharing_router
from app.chat.router import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_db()
    db = await get_db()
    await init_schema(db)
    yield
    await close_db()


app = FastAPI(title="Claude Puddle", lifespan=lifespan)


# CSRF protection: reject mutation requests that aren't JSON
@app.middleware("http")
async def csrf_content_type_check(request: Request, call_next):
    mutation_methods = {"POST", "PUT", "PATCH", "DELETE"}
    if request.method in mutation_methods:
        # Allow form-encoded only for routes that explicitly need it (none currently)
        content_type = request.headers.get("content-type", "")
        if content_type and not content_type.startswith("application/json"):
            # Static assets and non-API paths are fine
            if request.url.path.startswith("/auth") or request.url.path.startswith("/conversations") or request.url.path.startswith("/shared"):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Content-Type must be application/json"},
                )
    return await call_next(request)


# API routers
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(sharing_router)
app.include_router(chat_router)

# Serve static front-end; must come after API routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")
