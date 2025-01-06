import json
import time
from datetime import datetime, timedelta
import threading  # For running periodic checks
from plyer import notification  # For desktop notifications (optional)

class TaskPlanner:
    def __init__(self, file_path="tasks.json"):
        self.file_path = file_path
        self.tasks = self.load_tasks()

    def load_tasks(self):
        try:
            with open(self.file_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def save_tasks(self):
        with open(self.file_path, "w") as file:
            json.dump(self.tasks, file, indent=4)

    def add_task(self, name, deadline, category="General", priority="Medium"):
        self.tasks.append({
            "name": name,
            "deadline": deadline,
            "category": category,
            "priority": priority,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        })
        self.save_tasks()

    def complete_task(self, name):
        for task in self.tasks:
            if task["name"].lower() == name.lower():
                task["status"] = "completed"
                self.save_tasks()
                print(f"Task '{name}' marked as completed.")
                return
        print(f"Task '{name}' not found.")

    def list_tasks(self):
        if not self.tasks:
            print("No tasks available.")
        else:
            print("\nCurrent Tasks:")
            for i, task in enumerate(self.tasks, start=1):
                status = "✅" if task["status"] == "completed" else "❌"
                overdue = " (Overdue)" if self.is_overdue(task["deadline"]) else ""
                print(f"{i}. {task['name']} [Category: {task['category']}, Priority: {task['priority']}] "
                      f"(Deadline: {task['deadline']}) - Status: {status}{overdue}")

    def is_overdue(self, deadline):
        return datetime.strptime(deadline, "%Y-%m-%d") < datetime.now()

    def check_deadlines(self):
        now = datetime.now()
        for task in self.tasks:
            if task["status"] == "pending":
                deadline = datetime.strptime(task["deadline"], "%Y-%m-%d")
                days_left = (deadline - now).days
                if days_left < 0:
                    print(f"⏰ Task '{task['name']}' is overdue!")
                    self.notify(f"Overdue Task: {task['name']}", f"Deadline was {task['deadline']}")
                elif days_left <= 1:
                    print(f"⏰ Task '{task['name']}' is due soon!")
                    self.notify(f"Upcoming Deadline: {task['name']}", f"Due by {task['deadline']}")

    def notify(self, title, message):
        """Send a desktop notification."""
        notification.notify(
            title=title,
            message=message,
            timeout=10
        )

# Background thread to periodically check deadlines
def start_deadline_checker(planner):
    def periodic_check():
        while True:
            planner.check_deadlines()
            time.sleep(60)  # Check every 60 seconds

    thread = threading.Thread(target=periodic_check, daemon=True)
    thread.start()

# Example Usage
if __name__ == "__main__":
    planner = TaskPlanner()
    start_deadline_checker(planner)

    while True:
        print("\nTask Planner Options:")
        print("1. Add Task")
        print("2. Complete Task")
        print("3. View Tasks")
        print("4. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Enter task name: ")
            deadline = input("Enter task deadline (YYYY-MM-DD): ")
            category = input("Enter task category (e.g., Work, Personal): ")
            priority = input("Enter task priority (High, Medium, Low): ")
            planner.add_task(name, deadline, category, priority)
            print(f"Task '{name}' added.")

        elif choice == "2":
            name = input("Enter task name to mark as complete: ")
            planner.complete_task(name)

        elif choice == "3":
            planner.list_tasks()

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")
