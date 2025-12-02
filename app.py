from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import json

app = Flask(__name__)
CORS(app)

class TaskScheduler:
    def __init__(self):
        self.tasks = {}
        self.schedule = []
    
    def calculate_priority_score(self, task):
        """Calculate dynamic priority score"""
        base_priority = task.get('priority', 5)
        deadline = datetime.fromisoformat(task.get('deadline', datetime.now().isoformat()))
        estimated_duration = task.get('estimated_duration', 60)
        
        # Time urgency factor
        time_until_deadline = (deadline - datetime.now()).total_seconds() / 3600
        urgency_factor = max(0, 10 - (time_until_deadline / 24))
        
        # Duration factor (longer tasks get slight boost)
        duration_factor = min(estimated_duration / 120, 2)
        
        # Calculate final score
        priority_score = (base_priority * 2) + urgency_factor + duration_factor
        
        return round(priority_score, 2)
    
    def detect_conflicts(self, new_task):
        """Detect scheduling conflicts"""
        conflicts = []
        new_start = datetime.fromisoformat(new_task.get('scheduled_time', datetime.now().isoformat()))
        new_end = new_start + timedelta(minutes=new_task.get('estimated_duration', 60))
        
        for task_id, task in self.tasks.items():
            if task.get('status') == 'completed':
                continue
            
            task_start = datetime.fromisoformat(task.get('scheduled_time', datetime.now().isoformat()))
            task_end = task_start + timedelta(minutes=task.get('estimated_duration', 60))
            
            # Check for overlap
            if (new_start < task_end and new_end > task_start):
                conflicts.append({
                    'task_id': task_id,
                    'title': task.get('title'),
                    'time': task.get('scheduled_time')
                })
        
        return conflicts
    
    def suggest_optimal_time(self, task):
        """Suggest optimal scheduling time"""
        duration = task.get('estimated_duration', 60)
        deadline = datetime.fromisoformat(task.get('deadline', (datetime.now() + timedelta(days=7)).isoformat()))
        
        # Start from current time
        current_time = datetime.now()
        
        # Try to find free slot
        while current_time < deadline:
            test_task = task.copy()
            test_task['scheduled_time'] = current_time.isoformat()
            
            conflicts = self.detect_conflicts(test_task)
            
            if not conflicts:
                return {
                    'suggested_time': current_time.isoformat(),
                    'reason': 'No conflicts detected',
                    'confidence': 95
                }
            
            # Move to next hour
            current_time += timedelta(hours=1)
        
        return {
            'suggested_time': current_time.isoformat(),
            'reason': 'Best available slot near deadline',
            'confidence': 60
        }
    
    def create_task(self, task_data):
        """Create new task"""
        task_id = str(uuid.uuid4())[:8]
        
        # Set defaults
        task = {
            'id': task_id,
            'title': task_data.get('title', 'Untitled Task'),
            'description': task_data.get('description', ''),
            'priority': task_data.get('priority', 5),
            'estimated_duration': task_data.get('estimated_duration', 60),
            'deadline': task_data.get('deadline', (datetime.now() + timedelta(days=7)).isoformat()),
            'scheduled_time': task_data.get('scheduled_time', datetime.now().isoformat()),
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'tags': task_data.get('tags', [])
        }
        
        # Calculate priority score
        task['priority_score'] = self.calculate_priority_score(task)
        
        # Check for conflicts
        conflicts = self.detect_conflicts(task)
        
        # Store task
        self.tasks[task_id] = task
        
        result = {
            'task': task,
            'conflicts': conflicts,
            'has_conflicts': len(conflicts) > 0
        }
        
        # Suggest alternative if conflicts exist
        if conflicts:
            result['suggestion'] = self.suggest_optimal_time(task)
        
        return result
    
    def get_schedule(self, filters=None):
        """Get optimized schedule"""
        tasks_list = list(self.tasks.values())
        
        # Apply filters
        if filters:
            if filters.get('status'):
                tasks_list = [t for t in tasks_list if t['status'] == filters['status']]
            if filters.get('priority_min'):
                tasks_list = [t for t in tasks_list if t['priority'] >= filters['priority_min']]
        
        # Sort by priority score
        tasks_list.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return {
            'total_tasks': len(tasks_list),
            'tasks': tasks_list,
            'summary': {
                'high_priority': len([t for t in tasks_list if t['priority'] >= 8]),
                'medium_priority': len([t for t in tasks_list if 4 <= t['priority'] < 8]),
                'low_priority': len([t for t in tasks_list if t['priority'] < 4]),
                'pending': len([t for t in tasks_list if t['status'] == 'pending']),
                'in_progress': len([t for t in tasks_list if t['status'] == 'in_progress']),
                'completed': len([t for t in tasks_list if t['status'] == 'completed'])
            }
        }
    
    def update_task(self, task_id, updates):
        """Update existing task"""
        if task_id not in self.tasks:
            return {'error': 'Task not found'}
        
        task = self.tasks[task_id]
        task.update(updates)
        
        # Recalculate priority score
        task['priority_score'] = self.calculate_priority_score(task)
        task['updated_at'] = datetime.now().isoformat()
        
        return {'task': task, 'message': 'Task updated successfully'}
    
    def delete_task(self, task_id):
        """Delete task"""
        if task_id not in self.tasks:
            return {'error': 'Task not found'}
        
        deleted_task = self.tasks.pop(task_id)
        return {'message': 'Task deleted successfully', 'task': deleted_task}

scheduler = TaskScheduler()

@app.route('/')
def home():
    return jsonify({
        'service': 'Intelligent Task Scheduler API',
        'version': '1.0.0',
        'endpoints': {
            '/tasks': 'POST - Create task, GET - List tasks',
            '/tasks/<id>': 'GET - Get task, PUT - Update task, DELETE - Delete task',
            '/schedule': 'GET - Get optimized schedule',
            '/suggest': 'POST - Get scheduling suggestions',
            '/health': 'GET - Health check'
        }
    })

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create new task"""
    try:
        data = request.get_json()
        result = scheduler.create_task(data)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """List all tasks"""
    try:
        filters = {
            'status': request.args.get('status'),
            'priority_min': int(request.args.get('priority_min', 0))
        }
        result = scheduler.get_schedule(filters)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get specific task"""
    try:
        if task_id not in scheduler.tasks:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify({'task': scheduler.tasks[task_id]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update task"""
    try:
        data = request.get_json()
        result = scheduler.update_task(task_id, data)
        if 'error' in result:
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete task"""
    try:
        result = scheduler.delete_task(task_id)
        if 'error' in result:
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedule', methods=['GET'])
def get_schedule():
    """Get optimized schedule"""
    try:
        result = scheduler.get_schedule()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/suggest', methods=['POST'])
def suggest_time():
    """Suggest optimal scheduling time"""
    try:
        data = request.get_json()
        suggestion = scheduler.suggest_optimal_time(data)
        return jsonify(suggestion), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'task-scheduler'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
