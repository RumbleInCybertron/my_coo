import json
import time
from datetime import datetime, timedelta
import threading
from plyer import notification

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

    def add_task(self, name, deadline_input, category="General", priority="Medium", recurrence=None):
        deadline = self.parse_deadline(deadline_input)
        if not deadline:
            print("Invalid deadline format. Please try again.")
            return

        self.tasks.append({
            "name": name,
            "deadline": deadline,
            "category": category,
            "priority": priority,
            "recurrence": recurrence,  # e.g., "daily", "weekly", "monthly"
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        })
        self.save_tasks()
        print(f"Task '{name}' added with deadline: {deadline} and recurrence: {recurrence}")

    def parse_deadline(self, deadline_input):
        try:
            if " " in deadline_input:
                return datetime.strptime(deadline_input, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            elif deadline_input.endswith("m"):
                minutes = int(deadline_input[:-1])
                return (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
            elif deadline_input.endswith("h"):
                hours = int(deadline_input[:-1])
                return (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                return datetime.strptime(deadline_input, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def complete_task(self, name):
        for task in self.tasks:
            if task["name"].lower() == name.lower():
                if task["recurrence"]:
                    self.schedule_next_occurrence(task)
                task["status"] = "completed"
                self.save_tasks()
                print(f"Task '{name}' marked as completed.")
                return
        print(f"Task '{name}' not found.")

    def schedule_next_occurrence(self, task):
        recurrence = task["recurrence"]
        next_deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S")
        if recurrence == "daily":
            next_deadline += timedelta(days=1)
        elif recurrence == "weekly":
            next_deadline += timedelta(weeks=1)
        elif recurrence == "monthly":
            next_deadline = next_deadline.replace(month=next_deadline.month % 12 + 1)
        else:
            print(f"Unknown recurrence type: {recurrence}")
            return

        self.tasks.append({
            "name": task["name"],
            "deadline": next_deadline.strftime("%Y-%m-%d %H:%M:%S"),
            "category": task["category"],
            "priority": task["priority"],
            "recurrence": task["recurrence"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        })
        self.save_tasks()
        print(f"Next occurrence of '{task['name']}' scheduled for {next_deadline.strftime('%Y-%m-%d %H:%M:%S')}.")

    def list_tasks(self):
        if not self.tasks:
            print("No tasks available.")
        else:
            print("\nCurrent Tasks:")
            for i, task in enumerate(self.tasks, start=1):
                status = "✅" if task["status"] == "completed" else "❌"
                overdue = " (Overdue)" if self.is_overdue(task["deadline"]) else ""
                recurrence = f" (Recurring: {task['recurrence']})" if task["recurrence"] else ""
                print(f"{i}. {task['name']} [Category: {task.get('category', 'General')}, Priority: {task.get('priority', 'Medium')}] "
                      f"(Deadline: {task['deadline']}) - Status: {status}{overdue}{recurrence}")

    def update_task(self, name, field, value):
        for task in self.tasks:
            if task["name"].lower() == name.lower():
                if field in task:
                    if field == "deadline":
                        parsed_deadline = self.parse_deadline(value)
                        if parsed_deadline:
                            task[field] = parsed_deadline
                        else:
                            print("Invalid deadline format.")
                            return
                    elif field == "recurrence":
                        if value in ["daily", "weekly", "monthly", None]:
                            task[field] = value
                        else:
                            print("Invalid recurrence. Choose 'daily', 'weekly', 'monthly', or leave blank.")
                            return
                    else:
                        task[field] = value
                    self.save_tasks()
                    print(f"Task '{name}' updated: {field} = {value}")
                    return
                else:
                    print(f"Field '{field}' does not exist in tasks.")
                    return
        print(f"Task '{name}' not found.")


    def is_overdue(self, deadline):
        return datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S") < datetime.now()

    def check_deadlines(self):
        now = datetime.now()
        for task in self.tasks:
            if task["status"] == "pending":
                deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S")
                time_left = (deadline - now).total_seconds()
                if time_left < 0:
                    print(f"⏰ Task '{task['name']}' is overdue!")
                    self.notify(f"Overdue Task: {task['name']}", f"Deadline was {task['deadline']}")
                elif time_left <= 300:
                    print(f"⏰ Task '{task['name']}' is due soon!")
                    self.notify(f"Upcoming Deadline: {task['name']}", f"Due by {task['deadline']}")

    def notify(self, title, message):
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
            time.sleep(60)

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
        print("3. Update- Task")
        print("4. View Tasks")
        print("5. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Enter task name: ")
            deadline = input("Enter task deadline (e.g., '5m', '2h', '2025-01-05 14:30'): ")
            category = input("Enter task category (e.g., Work, Personal): ")
            priority = input("Enter task priority (High, Medium, Low): ")
            recurrence = input("Enter recurrence (daily, weekly, monthly, or leave blank): ")
            planner.add_task(name, deadline, category, priority, recurrence)

        elif choice == "2":
            name = input("Enter task name to mark as complete: ")
            planner.complete_task(name)

        elif choice == "3":
            name = input("Enter task name to update: ")
            field = input("Enter the field to update (e.g., name, deadline, category, priority, recurrence): ")
            value = input(f"Enter new value for {field}: ")
            planner.update_task(name, field, value)

        elif choice == "4":
            planner.list_tasks()

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")
