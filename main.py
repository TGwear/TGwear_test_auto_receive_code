
import os
import json
import re
import threading

from fastapi import FastAPI, HTTPException, Query
import uvicorn
from pyrogram import Client, filters
from pyrogram.types import Message

# —— 1. 读取配置 —— #
with open('config.json', 'r', encoding='utf-8') as f:
    DATA = json.load(f)

def getenv(key: str):
    return os.environ.get(key) or DATA.get(key)

api_id = int(getenv("ID"))
api_hash = getenv("HASH")
session_string = getenv("STRING")
API_KEY = getenv("API_KEY")  # 在 config.json 中配置你的 API_KEY

# —— 2. 初始化 Pyrogram 客户端 —— #
if session_string:
    app = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=session_string)
else:
    app = Client("myacc", api_id=api_id, api_hash=api_hash)

# —— 3. 全局状态 —— #
last_code = None
PHONE_NUMBER = "+1xxxxxxxxxx"

# —— 4. FastAPI 应用 —— #
api = FastAPI()

def check_key(key: str):
    """校验 GET 参数中的 api_key"""
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@api.get("/code")
def get_code(api_key: str = Query(..., alias="api_key")):
    """
    返回最近一次收到的登录验证码。
    调用示例： GET /code?api_key=supersecretkey
    """
    check_key(api_key)
    return {"code": last_code}

@api.get("/phone")
def get_phone(api_key: str = Query(..., alias="api_key")):
    """
    返回固定的手机号。
    调用示例： GET /phone?api_key=supersecretkey
    """
    check_key(api_key)
    return {"phone": PHONE_NUMBER}

# —— 5. Pyrogram 消息处理 —— #
LOGIN_BOT_ID = 777000
CODE_PATTERN = re.compile(r"Login code: (\d{4,6})")

@app.on_message(
    filters.user(LOGIN_BOT_ID) &
    filters.text &
    filters.regex(CODE_PATTERN)
)
def auto_receive_code(client: Client, message: Message):
    global last_code
    text = message.text or ""
    m = CODE_PATTERN.search(text)
    if not m:
        return
    last_code = m.group(1)
    print(f"[自动接收] Telegram 登录验证码：{last_code}")

# —— 6. 并行启动 FastAPI 和 Pyrogram —— #
def run_api():
    uvicorn.run(api, host="127.0.0.1", port=37941)

if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()
    print("FastAPI 服务已启动：http://127.0.0.1:37941")
    print("请通过 GET 参数 api_key 调用 /code 和 /phone 接口，例如：")
    print("  http://127.0.0.1:37941/code?api_key=<你的API_KEY>")
    app.run()
