# from typing import Annotated
from fastapi import Header, HTTPException

# from fastapi import Depends, FastAPI
# from fastapi.security import OAuth2PasswordBearer
from typing_extensions import Annotated


# 平台端登陆信息保存（admin）
async def get_sys_token_header(x_token: Annotated[str, Header()]):
    if x_token != "admins":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def get_sys_query_token(token: str):
    if token != "admin":
        raise HTTPException(status_code=400, detail="No system token provided")


# 客户端登陆信息
async def get_client_token_header(x_token: Annotated[str, Header()]):
    # if x_token != "admin-secret-token":
    if x_token != "admin-s":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def get_client_query_token(token: str):
    if token != "admin":
        raise HTTPException(status_code=400, detail="No client token provided")