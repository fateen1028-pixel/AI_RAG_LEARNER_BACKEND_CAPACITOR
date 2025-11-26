from datetime import datetime

class Todo:
    @staticmethod
    def create_todo_doc(user_id, plan_id, day, parent_task_title, task, duration_minutes, description):
        return {
            "userId": user_id,
            "planId": plan_id,
            "day": day,
            "parent_task_title": parent_task_title,
            "task": task,
            "duration_minutes": duration_minutes,
            "description": description,
            "completed": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now()
        }
    
    @staticmethod
    def get_todo_response(todo):
        return {
            "id": str(todo['_id']),
            "day": todo.get('day'),
            "task": todo.get('task'),
            "parent_task_title": todo.get('parent_task_title'),
            "duration_minutes": todo.get('duration_minutes'),
            "description": todo.get('description'),
            "completed": todo.get('completed', False)
        }