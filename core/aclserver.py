from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute
from typing import Callable
from pydantic import BaseModel

class Tuple(BaseModel):
    object: str
    relation: str
    resource: str

class WriteRequestModel(BaseModel):
    tuples:list[Tuple]

class WriteRequestResponse(BaseModel):
    zookie: str


class CustomRouteHandler(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # Before request processing
            print(f"Before request to {request.url.path}")
            api_key = request.headers.get("api-key")
            if not api_key:
                return Response(status_code=400)

            response = await original_route_handler(request)

            print(f"After request to {request.url.path}")

            return response

        return custom_route_handler


# using a route class for middleware purpose
# as we can't directly add middleware to APIRouter
# and dependencies cant return response
acl_router = APIRouter(route_class=CustomRouteHandler)


@acl_router.post("/write")
async def write(relations:WriteRequestModel):
    return "hello"


@acl_router.post("/check")
async def write(relations:WriteRequestModel):
    return "hello"