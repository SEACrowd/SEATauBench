from tau2.domains.mock.data_model import MockDB, Task, TaskStatus, User
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class MockTools(ToolKitBase):
    """tools อย่างง่ายสำหรับโดเมนจำลอง."""

    db: MockDB

    def __init__(self, db: MockDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.WRITE)
    def create_task(self, user_id: str, title: str, description: str = None) -> Task:
        """
        สร้างงานใหม่สำหรับ user.

        อาร์กิวเมนต์:
            user_id: รหัสของ user ที่สร้างงาน
            title: ชื่อเรื่องของงาน
            description: คำอธิบายของงาน (ไม่บังคับ)

        คืนค่า:
            งานที่ถูกสร้าง

        ข้อยกเว้น:
            ValueError: หากไม่พบ user
        """
        if user_id not in self.db.users:
            raise ValueError(f"User {user_id} not found")

        task_id = f"task_{len(self.db.tasks) + 1}"
        task = Task(
            task_id=task_id, title=title, description=description, status="pending"
        )

        self.db.tasks[task_id] = task
        self.db.users[user_id].tasks.append(task_id)

        return task

    @is_tool(ToolType.READ)
    def get_users(self) -> list[User]:
        """
        ดึง users ทั้งหมดจากฐานข้อมูล.
        """
        return list(self.db.users.values())

    @is_tool(ToolType.WRITE)
    def update_task_status(self, task_id: str, status: TaskStatus) -> Task:
        """
        อัปเดตสถานะของงาน.

        พารามิเตอร์:
            task_id: ไอดีของงานที่จะอัปเดต
            status: สถานะใหม่ของงาน

        คืนค่า:
            งานที่ได้รับการอัปเดต

        ข้อยกเว้น:
            ValueError: หากไม่พบงานดังกล่าว
        """
        if task_id not in self.db.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.db.tasks[task_id]
        task.status = status
        return task

    def assert_number_of_tasks(self, user_id: str, expected_number: int) -> bool:
        """
        ตรวจสอบว่าจำนวนงานสำหรับ user เป็นไปตามที่คาดไว้หรือไม่.

        พารามิเตอร์:
            user_id: ไอดีของ user
            expected_number: จำนวนงานที่คาดไว้

        คืนค่า:
            True หากจำนวนงานเป็นไปตามที่คาดไว้, False ในกรณีอื่น
        """
        if user_id not in self.db.users:
            raise ValueError(f"User {user_id} not found")
        return len(self.db.users[user_id].tasks) == expected_number

    def assert_task_status(self, task_id: str, expected_status: TaskStatus) -> bool:
        """
        ตรวจสอบว่าสถานะของงานเป็นไปตามที่คาดไว้หรือไม่.
        """
        if task_id not in self.db.tasks:
            raise ValueError(f"Task {task_id} not found")
        return self.db.tasks[task_id].status == expected_status

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agents(self, summary: str) -> str:
        """
        โอน user ไปยังเจ้าหน้าที่มนุษย์ พร้อมสรุปปัญหาของ user.
        ให้โอนเฉพาะเมื่อ
         -  user ระบุอย่างชัดเจนว่าขอเจ้าหน้าที่มนุษย์
         -  เมื่อพิจารณาตามนโยบายและ tool ที่มีอยู่ คุณไม่สามารถแก้ปัญหาของ user ได้

        อาร์กิวเมนต์:
            summary: สรุปปัญหาของ user

        คืนค่า:
            ข้อความที่ระบุว่า user ได้ถูกโอนไปยังเจ้าหน้าที่มนุษย์แล้ว
        """
        return "Transfer successful"

    # @is_tool(ToolType.THINK)
    # def think(self, thought: str) -> str:
    #     """
    #     Use the tool to think about something.
    #     It will not obtain new information or change the database, but just append the thought to the log.
    #     Use it when complex reasoning or some cache memory is needed.

    #     Args:
    #         thought: A thought to think about.

    #     Returns:
    #         Empty string
    #     """
    #     return ""
