# 📅 Intelligent Task Scheduler API

AI-powered task scheduling API with dynamic priority optimization, conflict detection, and smart time suggestions.

## Features

- **Dynamic Priority Scoring**: Automatically calculates task priority based on deadline, duration, and importance
- **Conflict Detection**: Identifies scheduling conflicts in real-time
- **Smart Suggestions**: Recommends optimal scheduling times
- **Task Management**: Full CRUD operations for tasks
- **Optimized Scheduling**: Generates priority-based schedules
- **Filtering & Search**: Filter tasks by status, priority, and tags

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

## API Endpoints

### POST /tasks
Create a new task

**Request:**
```json
{
  "title": "Complete project proposal",
  "description": "Finish and submit Q4 proposal",
  "priority": 8,
  "estimated_duration": 120,
  "deadline": "2025-12-10T17:00:00",
  "scheduled_time": "2025-12-03T14:00:00",
  "tags": ["work", "urgent"]
}
```

**Response:**
```json
{
  "task": {
    "id": "a3f5d8c9",
    "title": "Complete project proposal",
    "priority_score": 18.5,
    "status": "pending",
    "created_at": "2025-12-02T18:30:00"
  },
  "conflicts": [],
  "has_conflicts": false
}
```

### GET /tasks
List all tasks with optional filters

**Query Parameters:**
- `status`: Filter by status (pending/in_progress/completed)
- `priority_min`: Minimum priority level

### GET /tasks/:id
Get specific task details

### PUT /tasks/:id
Update task

### DELETE /tasks/:id
Delete task

### GET /schedule
Get optimized schedule sorted by priority

### POST /suggest
Get optimal time suggestions for a task

## Priority Scoring Algorithm

Priority score is calculated using:
- Base priority (1-10)
- Time urgency (deadline proximity)
- Task duration
- Conflict penalties

## Tech Stack

- Flask
- Python 3.8+
- Intelligent Scheduling Algorithms

## Author

Shivansh Dubey
