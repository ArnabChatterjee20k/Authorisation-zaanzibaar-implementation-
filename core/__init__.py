from fastapi import FastAPI, Depends
from core.aclserver import acl_router
from core.tenants import tenant_router


def zanzibar():
    app = FastAPI()
    app.include_router(acl_router, prefix="/acl")
    app.include_router(tenant_router, prefix="/tenants")
    return app
