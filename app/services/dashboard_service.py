from datetime import datetime
from bson import ObjectId
from app.utils.helpers import get_db

class DashboardService:
    @staticmethod
    def get_dashboard_data(user_id):
        try:
            plans_col = get_db().learning_plans
            todos_col = get_db().todos
            
            # Get all plans for the user
            all_plans = list(plans_col.find({"userId": user_id}))
            
            plans_progress = []
            total_completed_todos = 0
            total_todos = 0
            completed_plans = 0
            active_plans = 0
            
            # Calculate progress for each plan
            for plan in all_plans:
                plan_id = str(plan['_id'])
                
                # Get todos for this plan
                todos = list(todos_col.find({"planId": plan_id, "userId": user_id}))
                total_plan_todos = len(todos)
                completed_plan_todos = len([t for t in todos if t.get('completed', False)])
                
                # Calculate completion rate
                completion_rate = 0
                if total_plan_todos > 0:
                    completion_rate = round((completed_plan_todos / total_plan_todos) * 100)
                
                # Calculate completed days
                completed_days = len(set([t['day'] for t in todos if t.get('completed', False)]))
                
                total_completed_todos += completed_plan_todos
                total_todos += total_plan_todos
                
                if plan.get('status') == 'COMPLETED':
                    completed_plans += 1
                else:
                    active_plans += 1
                
                plans_progress.append({
                    "planId": plan_id,
                    "topic": plan.get('topic', 'Unknown Topic'),
                    "totalDays": plan.get('days', 0),
                    "completedDays": completed_days,
                    "totalTodos": total_plan_todos,
                    "completedTodos": completed_plan_todos,
                    "completionRate": completion_rate,
                    "status": plan.get('status', 'ONGOING'),
                    "startDate": plan.get('startDate')
                })
            
            # Calculate overall statistics
            overall_completion_rate = 0
            if total_todos > 0:
                overall_completion_rate = round((total_completed_todos / total_todos) * 100)
            
            # Calculate consistency
            total_active_days = sum([p['completedDays'] for p in plans_progress])
            total_possible_days = sum([p['totalDays'] for p in plans_progress])
            
            consistency = 0
            if total_possible_days > 0:
                consistency = round((total_active_days / total_possible_days) * 100)
            
            # Calculate total study hours (estimate)
            total_study_hours = sum([plan.get('hours', 0) * plan.get('days', 0) for plan in all_plans])
            
            # Get user's first plan date for "learning since"
            first_plan = plans_col.find_one({"userId": user_id}, sort=[("createdAt", 1)])
            learning_since = "Recently"
            if first_plan and first_plan.get('createdAt'):
                learning_since = first_plan['createdAt'].strftime("%b %d, %Y")
            
            # Generate recent activity
            recent_activity = []
            for plan in all_plans[:3]:
                recent_todos = list(todos_col.find(
                    {"planId": str(plan['_id']), "userId": user_id, "completed": True}
                ).sort("updatedAt", -1).limit(2))
                
                for todo in recent_todos:
                    recent_activity.append({
                        "type": "completed",
                        "description": f"Completed: {todo.get('task', 'Task')}",
                        "timestamp": todo.get('updatedAt', datetime.now()).strftime("%b %d, %H:%M")
                    })
            
            # Add some created plan activities
            for plan in all_plans[:2]:
                recent_activity.append({
                    "type": "created",
                    "description": f"Started: {plan.get('topic', 'New Plan')}",
                    "timestamp": plan.get('createdAt', datetime.now()).strftime("%b %d, %H:%M")
                })
            
            # Sort activities by timestamp
            recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
            
            dashboard_data = {
                "plansProgress": plans_progress,
                "overallStats": {
                    "totalPlans": len(all_plans),
                    "activePlans": active_plans,
                    "completedPlans": completed_plans,
                    "totalCompletedTodos": total_completed_todos,
                    "totalTodos": total_todos,
                    "completionRate": overall_completion_rate,
                    "consistency": consistency,
                    "totalStudyHours": total_study_hours,
                    "activeDays": total_active_days,
                    "currentStreak": min(7, total_active_days),
                    "avgDailyProgress": round(overall_completion_rate / max(1, len(all_plans))),
                    "learningSince": learning_since
                },
                "recentActivity": recent_activity
            }
            
            return {
                "status": "success",
                "dashboard": dashboard_data
            }
            
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            return {
                "status": "error",
                "message": "Failed to load dashboard data"
            }, 500