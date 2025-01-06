import os
import json
import time
from datetime import datetime, timedelta
import threading
from plyer import notification

class TaskPlanner:
    def __init__(self, file_path="tasks.json"):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            self.create_empty_tasks_file()
        self.tasks = self.load_tasks()
        
    def create_empty_tasks_file(self):
        """Creates an empty tasks file if it doesn't exist."""
        with open(self.file_path, "w") as file:
            json.dump([], file)  # Assuming an empty list for tasks

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

    def list_tasks(self, filter_priority=None):
        if not self.tasks:
            print("No tasks available.")
        else:
            # Filter tasks by priority if specified
            tasks_to_display = (
                [task for task in self.tasks if task["priority"].lower() == filter_priority.lower()]
                if filter_priority else self.tasks
            )
            
            # Sort tasks by priority and then by deadline
            priority_order = {"High": 1, "Medium": 2, "Low": 3}
            tasks_to_display.sort(
                key=lambda x: (priority_order.get(x["priority"], 4), x["deadline"])
            )
            
            print("\nCurrent Tasks:")
            for i, task in enumerate(tasks_to_display, start=1):
                status = "✅" if task["status"] == "completed" else "❌"
                overdue = " (Overdue)" if self.is_overdue(task["deadline"]) else ""
                recurrence = f" (Recurring: {task['recurrence']})" if task["recurrence"] else ""
                print(
                    f"{i}. {task['name']} [Category: {task.get('category', 'General')}, Priority: {task.get('priority', 'Medium')}] "
                    f"(Deadline: {task['deadline']}) - Status: {status}{overdue}{recurrence}"
                )

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

    def list_overdue_tasks(self):
        overdue_tasks = [task for task in self.tasks if self.is_overdue(task["deadline"]) and task["status"] == "pending"]

        if not overdue_tasks:
            print("No overdue tasks found.")
        else:
            print("\nOverdue Tasks:")
            for i, task in enumerate(overdue_tasks, start=1):
                print(
                    f"{i}. {task['name']} [Category: {task.get('category', 'General')}, Priority: {task.get('priority', 'Medium')}] "
                    f"(Deadline: {task['deadline']})"
                )
                
    def reset_deadline(self, name, new_deadline):
        for task in self.tasks:
            if task["name"].lower() == name.lower() and self.is_overdue(task["deadline"]):
                parsed_deadline = self.parse_deadline(new_deadline)
                if parsed_deadline:
                    task["deadline"] = parsed_deadline
                    self.save_tasks()
                    print(f"Deadline for '{name}' reset to {new_deadline}.")
                    return
                else:
                    print("Invalid deadline format. Please try again.")
                    return
        print(f"Overdue task '{name}' not found or is not overdue.")

    def show_statistics(self):
        total_tasks = len(self.tasks)
        completed_tasks = len([task for task in self.tasks if task["status"] == "completed"])
        pending_tasks = len([task for task in self.tasks if task["status"] == "pending"])
        overdue_tasks = len([task for task in self.tasks if self.is_overdue(task["deadline"]) and task["status"] == "pending"])

        # Category Breakdown
        category_counts = {}
        for task in self.tasks:
            category = task.get("category", "General")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Priority Breakdown
        priority_counts = {"High": 0, "Medium": 0, "Low": 0}
        for task in self.tasks:
            priority = task.get("priority", "Medium")
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Display Statistics
        print("\nTask Statistics:")
        print(f"Total Tasks: {total_tasks}")
        print(f"Completed Tasks: {completed_tasks}")
        print(f"Pending Tasks: {pending_tasks}")
        print(f"Overdue Tasks: {overdue_tasks}")
        print("\nCategory Breakdown:")
        for category, count in category_counts.items():
            print(f"- {category}: {count}")
        print("\nPriority Breakdown:")
        for priority, count in priority_counts.items():
            print(f"- {priority}: {count}")

    def filter_tasks(self, by="priority", value=None):
        filtered_tasks = []
        if by == "priority":
            filtered_tasks = [task for task in self.tasks if task["priority"].lower() == value.lower()]
        elif by == "category":
            filtered_tasks = [task for task in self.tasks if task.get("category", "General").lower() == value.lower()]
        elif by == "due_date":
            now = datetime.now()
            if value == "today":
                filtered_tasks = [
                    task for task in self.tasks if datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").date() == now.date()
                ]
            elif value == "this_week":
                week_start = now - timedelta(days=now.weekday())
                week_end = week_start + timedelta(days=6)
                filtered_tasks = [
                    task for task in self.tasks
                    if week_start.date()
                    <= datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").date()
                    <= week_end.date()
                ]
            elif value == "this_month":
                filtered_tasks = [
                    task for task in self.tasks
                    if datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").month == now.month
                ]

        if not filtered_tasks:
            print("No tasks found matching the filter criteria.")
        else:
            print("\nFiltered Tasks:")
            for i, task in enumerate(filtered_tasks, start=1):
                status = "✅" if task["status"] == "completed" else "❌"
                overdue = " (Overdue)" if self.is_overdue(task["deadline"]) else ""
                print(
                    f"{i}. {task['name']} [Category: {task.get('category', 'General')}, Priority: {task.get('priority', 'Medium')}] "
                    f"(Deadline: {task['deadline']}) - Status: {status}{overdue}"
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
        print("3. Update Task")
        print("4. View Tasks")
        print("5. Filter Tasks")
        print("6. Overdue Task Management")
        print("7. View Task Statistics")
        print("8. Exit")
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
            print("\nFilter Tasks Options:")
            print("1. Filter by Priority")
            print("2. Filter by Category")
            print("3. Filter by Due Date (Today, This Week, This Month)")
            filter_choice = input("Choose an option: ")

            if filter_choice == "1":
                priority = input("Enter priority to filter by (High, Medium, Low): ")
                planner.filter_tasks(by="priority", value=priority)

            elif filter_choice == "2":
                category = input("Enter category to filter by (e.g., Work, Personal): ")
                planner.filter_tasks(by="category", value=category)

            elif filter_choice == "3":
                print("1. Due Today")
                print("2. Due This Week")
                print("3. Due This Month")
                date_filter = input("Choose an option: ")
                if date_filter == "1":
                    planner.filter_tasks(by="due_date", value="today")
                elif date_filter == "2":
                    planner.filter_tasks(by="due_date", value="this_week")
                elif date_filter == "3":
                    planner.filter_tasks(by="due_date", value="this_month")
                else:
                    print("Invalid choice. Returning to main menu.")

            else:
                print("Invalid choice. Returning to main menu.")


        elif choice == "6":
            print("\nManaging Overdue Tasks...")
            planner.list_overdue_tasks()

        elif choice == "7":
            planner.show_statistics()

        elif choice == "8":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")
