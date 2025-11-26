from datetime import datetime

class Plan:
    @staticmethod
    def create_plan_doc(user_id, topic, days, hours, roadmap=None):
        return {
            "userId": user_id,
            "topic": topic,
            "days": days,
            "hours": hours,
            "roadmap": roadmap,
            "progress": 0,
            "status": "ONGOING",
            "startDate": datetime.now().isoformat(),
            "createdAt": datetime.now(),
            "updatedAt": datetime.now()
        }
    
    @staticmethod
    def get_plan_response(plan):
        return {
            "id": str(plan['_id']),
            "topic": plan.get('topic'),
            "days": plan.get('days'),
            "hours": plan.get('hours'),
            "progress": plan.get('progress'),
            "status": plan.get('status'),
            "startDate": plan.get('startDate')
        }