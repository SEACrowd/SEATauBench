from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from tau2.domains.mock.utils import MOCK_DB_PATH
from tau2.environment.db import DB

TaskStatus = Literal["pending", "completed"]


class Task(BaseModel):
    task_id: str = Field(description="ตัวระบุเฉพาะสำหรับงาน")
    title: str = Field(description="หัวข้อของงาน")
    description: Optional[str] = Field(None, description="คำอธิบายของงาน")
    status: TaskStatus = Field(description="สถานะของงาน")


class User(BaseModel):
    user_id: str = Field(description="รหัสประจำตัวที่ไม่ซ้ำสำหรับ user")
    name: str = Field(description="ชื่อผู้ใช้")
    tasks: List[str] = Field(description="รายการรหัสงานที่มอบหมายให้ user")


class MockDB(DB):
    """ฐานข้อมูลเรียบง่ายที่มี users และงานของพวกเขา."""

    tasks: Dict[str, Task] = Field(
        description="พจนานุกรมของงานทั้งหมดที่จัดทำดัชนีโดยรหัสงาน"
    )
    users: Dict[str, User] = Field(
        description="พจนานุกรมของ users ทั้งหมดที่จัดทำดัชนีโดยรหัส user"
    )


def get_db():
    return MockDB.load(MOCK_DB_PATH)
