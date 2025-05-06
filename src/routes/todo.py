from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel
from src.database import get_todo_collection
from src.profile.token_jwt import get_current_user  # Dependency to get user from JWT
from src.profile.form import TaskCreate, TaskUpdate
from collections import defaultdict
from bson import ObjectId

todo_router = APIRouter(prefix="/todo", tags=["To-Do"])

def serialize_task(task):
    return {
        "_id": str(task["_id"]),
        "task": task["task"],
        "group": task.get("group", "General"),
        "status": task.get("status", "pending"),
        "user_id": str(task["user_id"]),
    }


@todo_router.get("/")
async def get_tasks(todo_collection=Depends(get_todo_collection), user=Depends(get_current_user)):
    query = {"user_id": ObjectId(user["_id"])}
    tasks = await todo_collection.find(query).to_list(length=None)

    grouped_tasks = defaultdict(list)
    for task in tasks:
        group_name = task.get("group", "General")
        grouped_tasks[group_name].append(serialize_task(task))

    return {"tasks_grouped": grouped_tasks}

# Add a new task
@todo_router.post("/add")
async def add_task(task_data: TaskCreate, todo_collection=Depends(get_todo_collection), user=Depends(get_current_user)):
    task = task_data.dict()
    task["status"] = "pending"
    task["user_id"] = ObjectId(user["_id"])

    result = await todo_collection.insert_one(task)
    return {"message": "Task added", "task_id": str(result.inserted_id)}

# Edit a task
@todo_router.put("/edit/{task_id}")
async def edit_task(task_id: str, updated_task: TaskUpdate, todo_collection=Depends(get_todo_collection), user=Depends(get_current_user)):
    task_obj_id = ObjectId(task_id)
    task = await todo_collection.find_one({"_id": task_obj_id, "user_id": ObjectId(user["_id"])})

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await todo_collection.update_one({"_id": task_obj_id}, {"$set": updated_task.dict()})
    return {"message": "Task updated"}

# Delete a task
@todo_router.delete("/delete/{task_id}")
async def delete_task(task_id: str, todo_collection=Depends(get_todo_collection), user=Depends(get_current_user)):
    task_obj_id = ObjectId(task_id)
    result = await todo_collection.delete_one({"_id": task_obj_id, "user_id": ObjectId(user["_id"])})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted"}

# Mark task as completed
@todo_router.put("/complete/{task_id}")
async def complete_task(task_id: str, todo_collection=Depends(get_todo_collection), user=Depends(get_current_user)):
    task_obj_id = ObjectId(task_id)
    result = await todo_collection.update_one({"_id": task_obj_id, "user_id": ObjectId(user["_id"])}, {"$set": {"status": "completed"}})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task marked as completed"}