from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.routing import BaseRoute

from app.auth import controller as authController
from app.middleware.auth import AuthMiddleware
from app.middleware.process_time import ProcessTimeMiddleware
from app.module import controller as moduleController
from app.password_reset_token import controller as passwordResetTokenController
from app.platform_invite import controller as platformInviteController
from app.platform_privilege import controller as platformPrivilegeController
from app.platform_privilege_set import controller as platformPrivilegeSetController
from app.platform_privilege_set_privilege import (
    controller as platformPrivilegeSetPrivilegeController,
)
from app.platform_user import controller as platformUserController
from app.utility.postgres import dispose_postgres_engine

from .author import controller as authorController
from .book import controller as bookController
from .book_author import controller as bookAuthorController
from .book_genre import controller as bookGenreController
from .book_rating import controller as bookRatingController
from .business import controller as businessController
from .business_book import controller as businessBookController
from .business_rating import controller as businessRatingController
from .business_user import controller as businessUserController
from .genre import controller as genreController
from .order import controller as orderController
from .order_item import controller as orderItemController
from .privilege import controller as privilegeController
from .role import controller as roleController
from .role_privilege import controller as rolePrivilegeController
from .user import controller as userController
from .variant import controller as variantController
from .variant_config import controller as variantConfigController
from .variant_option import controller as variantOptionController
from .variant_type import controller as variantTypeController

HIDDEN_TAGS = {"client", "platform"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await dispose_postgres_engine()


app = FastAPI(
    title="Print",
    description="Swagger UI for print doc",
    version="1.0.0",
    lifespan=lifespan,
)


def custom_openapi(title: str, version: str, description: str, routes: list[BaseRoute]):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=title,
        version=version,
        description=description,
        routes=routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Remove only client/platform from operations
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            tags = operation.get("tags")
            if not tags:
                continue

            # Filter out client/platform
            new_tags = [t for t in tags if t not in HIDDEN_TAGS]

            if new_tags:
                operation["tags"] = new_tags
            else:
                operation.pop("tags", None)

    # Also clean top-level tag declarations
    if "tags" in openapi_schema:
        openapi_schema["tags"] = [
            tag for tag in openapi_schema["tags"] if tag.get("name") not in HIDDEN_TAGS
        ]
        if not openapi_schema["tags"]:
            openapi_schema.pop("tags")

    app.openapi_schema = openapi_schema
    return app.openapi_schema


@app.get("/openapi.json", include_in_schema=False)
def client_openapi():
    routes = [
        route
        for route in app.routes
        if "client" in getattr(route, "tags", []) or "platform" not in getattr(route, "tags", [])
    ]
    return custom_openapi(
        title="Print",
        version="1.0.0",
        description="Swagger UI for print doc",
        routes=routes,
    )


@app.get("/openapi-platform.json", include_in_schema=False)
def platform_openapi():
    routes = [route for route in app.routes if "platform" in getattr(route, "tags", [])]
    return custom_openapi(
        title="Print Admin",
        version="1.0.0",
        description="Swagger UI for print admin doc",
        routes=routes,
    )


@app.get("/docs", include_in_schema=False)
def client_docs():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Print Docs",
    )


@app.get("/platform-docs", include_in_schema=False)
def platform_docs():
    return get_swagger_ui_html(
        openapi_url="/openapi-platform.json",
        title="Print Admin Docs",
    )


origins = ["http://localhost:3000", "http://localhost:3001"]
app.openapi = client_openapi

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProcessTimeMiddleware)

app.include_router(authController.router)
app.include_router(authorController.router)
app.include_router(bookController.router)
app.include_router(genreController.router)
app.include_router(bookGenreController.router)
app.include_router(bookAuthorController.router)
app.include_router(bookAuthorController.author_router)
app.include_router(userController.router)
app.include_router(roleController.router)
app.include_router(privilegeController.router)
app.include_router(rolePrivilegeController.router)
app.include_router(rolePrivilegeController.privilege_router)
app.include_router(bookRatingController.router)
app.include_router(businessController.router)
app.include_router(businessBookController.router)
app.include_router(businessUserController.router)
app.include_router(businessRatingController.customer_router)
app.include_router(businessRatingController.business_router)
app.include_router(variantController.router)
app.include_router(orderController.router)
app.include_router(orderController.business_router)
app.include_router(orderItemController.router)
app.include_router(variantTypeController.router)
app.include_router(variantOptionController.router)
app.include_router(variantConfigController.router)
app.include_router(moduleController.router)
app.include_router(platformPrivilegeSetController.router)
app.include_router(platformPrivilegeController.router)
app.include_router(platformPrivilegeSetPrivilegeController.router)
app.include_router(platformUserController.router)
app.include_router(platformInviteController.router)
app.include_router(passwordResetTokenController.router)
