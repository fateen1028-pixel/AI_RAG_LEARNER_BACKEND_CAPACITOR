from bson import ObjectId
from datetime import datetime
from app.utils.helpers import get_db

class TodoService:
    @staticmethod
    def get_todos_for_plan(user_id, plan_id):
        try:
            plans_col = get_db().learning_plans
            todos_col = get_db().todos
            
            # Verify plan belongs to user
            plan = plans_col.find_one({"_id": ObjectId(plan_id), "userId": user_id})
            if not plan:
                return {"status": "error", "message": "Plan not found"}, 404
            
            # **FIX: Use the plan's currentDay field**
            current_day = plan.get('currentDay', 1)
            total_days = plan.get('days', 1)
            plan_status = plan.get('status', "ONGOING")

            # Fallback to date-based calculation if currentDay is not set
            if current_day == 1:
                start_date_str = plan.get("startDate")
                if start_date_str:
                    start_date = datetime.fromisoformat(start_date_str).date()
                    today = datetime.now().date()
                    days_passed = (today - start_date).days
                    current_day = max(1, min(days_passed + 1, total_days))
            
            all_todos = list(todos_col.find({
                "planId": plan_id,
                "userId": user_id,
                "day": current_day
            }, {"_id": 1, "day": 1, "task": 1, "parent_task_title": 1, "duration_minutes": 1, "description": 1, "completed": 1}))

            for todo in all_todos:
                todo['_id'] = str(todo['_id'])

            return {
                "status": "success",
                "currentDay": current_day,
                "totalDays": total_days,
                "planStatus": plan_status,
                "todos": all_todos,
            }
        except Exception as e:
            print(f"Error fetching todos: {e}")
            return {"status": "error", "message": "Failed to retrieve todos"}, 500

    @staticmethod
    def toggle_todo(user_id, todo_id):
        try:
            todos_col = get_db().todos
            plans_col = get_db().learning_plans
            
            # Verify todo belongs to user
            todo = todos_col.find_one({"_id": ObjectId(todo_id), "userId": user_id})
            if not todo:
                return {"status": "error", "message": "Todo not found"}, 404        
            plan_id = todo["planId"]
            new_completed_status = not todo.get("completed", False)

            todos_col.update_one(
                {"_id": ObjectId(todo_id), "userId": user_id},
                {"$set": {"completed": new_completed_status, "updatedAt": datetime.now()}}
            )

            total = todos_col.count_documents({"planId": plan_id, "userId": user_id})
            completed = todos_col.count_documents({"planId": plan_id, "userId": user_id, "completed": True})

            progress = 0
            status = "ONGOING"

            if total > 0:
                progress = int((completed / total) * 100)
                if progress >= 100:
                    status = "COMPLETED"
            else:
                progress = 100
                status = "COMPLETED"

            plans_col.update_one({"_id": ObjectId(plan_id), "userId": user_id}, {"$set": {"progress": progress, "status": status}})

            return {
                "status": "success",
                "message": "Todo toggled successfully",
                "planStatus": status,
                "planProgress": progress
            }

        except Exception as e:
            print(f"Error toggling todo: {e}")
            return {"status": "error", "message": "Failed to toggle todo"}, 500

    @staticmethod
    def delete_todo(user_id, todo_id):
        try:
            todos_col = get_db().todos
            plans_col = get_db().learning_plans
            
            # Verify todo belongs to user
            todo = todos_col.find_one({"_id": ObjectId(todo_id), "userId": user_id})
            if not todo:
                return {"status": "error", "message": "Todo not found"}, 404
            
            plan_id = todo["planId"]

            result = todos_col.delete_one({"_id": ObjectId(todo_id), "userId": user_id})
            if result.deleted_count == 0:
                return {"status": "error", "message": "Todo not found"}, 404
            
            total = todos_col.count_documents({"planId": plan_id, "userId": user_id})
            completed = todos_col.count_documents({"planId": plan_id, "userId": user_id, "completed": True})
            
            progress = 0
            status = "ONGOING"
            
            if total > 0:
                progress = int((completed / total) * 100)
                if progress >= 100:
                    status = "COMPLETED"
            else:
                progress = 100
                status = "COMPLETED"

            plans_col.update_one({"_id": ObjectId(plan_id), "userId": user_id}, {"$set": {"progress": progress, "status": status}})

            return {
                "status": "success", 
                "message": "Todo deleted...",
                "planStatus": status,
                "planProgress": progress
            }
        except Exception as e:
            print(f"Error deleting todo: {e}")
            return {"status": "error", "message": "Failed to delete todo"}, 500

    @staticmethod
    def move_todo(user_id, todo_id, new_day):
        if new_day is None or not isinstance(new_day, int) or new_day <= 0:
            return {"status": "error", "message": "Invalid new day provided"}, 400

        try:
            todos_col = get_db().todos
            
            result = todos_col.update_one(
                {"_id": ObjectId(todo_id), "userId": user_id},
                {"$set": {"day": new_day, "updatedAt": datetime.now()}}
            )

            if result.matched_count == 0:
                return {"status": "error", "message": "Todo not found"}, 404
                
            return {"status": "success", "message": f"Todo moved to Day {new_day}"}

        except Exception as e:
            print(f"Error moving todo: {e}")
            return {"status": "error", "message": "Failed to move todo"}, 500

    @staticmethod
    def edit_todo(user_id, todo_id, data):
        todos_col = get_db().todos
        
        # Extract editable fields from request
        task = data.get("task")
        duration_minutes = data.get("duration_minutes")
        description = data.get("description")
        
        # Validate that at least one field is provided
        if not any([task, duration_minutes is not None, description]):
            return {
                "status": "error", 
                "message": "No fields provided to update"
            }, 400
        
        try:
            # Check if todo exists and belongs to user
            todo = todos_col.find_one({"_id": ObjectId(todo_id), "userId": user_id})
            if not todo:
                return {"status": "error", "message": "Todo not found"}, 404
            
            # Build update document
            update_doc = {"updatedAt": datetime.now()}
            
            if task:
                update_doc["task"] = task
            if duration_minutes is not None:
                if not isinstance(duration_minutes, (int, float)) or duration_minutes <= 0:
                    return {
                        "status": "error", 
                        "message": "Invalid duration_minutes"
                    }, 400
                update_doc["duration_minutes"] = duration_minutes
            if description:
                update_doc["description"] = description
            
            # Update the todo
            result = todos_col.update_one(
                {"_id": ObjectId(todo_id), "userId": user_id},
                {"$set": update_doc}
            )
            
            if result.matched_count == 0:
                return {"status": "error", "message": "Todo not found"}, 404
            
            # Fetch the updated todo to return
            updated_todo = todos_col.find_one({"_id": ObjectId(todo_id), "userId": user_id})
            updated_todo['_id'] = str(updated_todo['_id'])
            
            return {
                "status": "success",
                "message": "Todo updated successfully",
                "todo": updated_todo
            }
        
        except Exception as e:
            print(f"Error editing todo: {e}")
            return {"status": "error", "message": "Failed to edit todo"}, 500