import os
import json
import time
from datetime import datetime, timedelta
import threading
from plyer import notification
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from collections import Counter
import sqlite3

class TaskPlanner:
    def __init__(self, master):
        self.master = master
        self.master.title("Task Planner")
        self.master.geometry("600x400")
        
        self.db = TaskDatabase()
        
        # Main Buttons
        self.add_task_button = tk.Button(master, text="Add Task", command=self.add_task_window)
        self.add_task_button.pack(pady=10)
        
        self.filter_tasks_button = tk.Button(master, text="Filter Tasks", command=self.filter_tasks_window)
        self.filter_tasks_button.pack(pady=10)
        
        self.stats_button = tk.Button(master, text="View Statistics", command=self.show_statistics_window)
        self.stats_button.pack(pady=10)
        
        self.edit_task_button = tk.Button(master, text="Edit Task", command=self.edit_task_window)
        self.edit_task_button.pack(pady=10)
        
        self.start_notification_checker()

        self.view_tasks_button = tk.Button(master, text="View Tasks", command=self.view_tasks_window)
        self.view_tasks_button.pack(pady=10)

        self.complete_task_button = tk.Button(master, text="Complete Task", command=self.complete_task_window)
        self.complete_task_button.pack(pady=10)

        self.exit_button = tk.Button(master, text="Exit", command=master.quit)
        self.exit_button.pack(pady=10)
        
    def create_empty_tasks_file(self):
        """Creates an empty tasks file if it doesn't exist."""
        with open(self.file_path, "w") as file:
            json.dump([], file)  # Assuming an empty list for tasks

    # def load_tasks(self):
    #     try:
    #         with open(self.file_path, "r") as file:
    #             return json.load(file)
    #     except FileNotFoundError:
    #         return []

    def save_tasks(self):
        with open(self.file_path, "w") as file:
            json.dump(self.db, file, indent=4)
            
    def add_task_window(self):
        add_window = tk.Toplevel(self.master)
        add_window.title("Add Task")
        add_window.geometry("500x400")

        tk.Label(add_window, text="Task Name").pack(pady=5)
        task_name_entry = tk.Entry(add_window, width=40)
        task_name_entry.pack(pady=5)

        tk.Label(add_window, text="Deadline (e.g., '5m', '2h', '2025-01-05 14:30')").pack(pady=5)
        deadline_entry = tk.Entry(add_window)
        deadline_entry.pack(pady=5)

        tk.Label(add_window, text="Category").pack(pady=5)
        category_combo = ttk.Combobox(add_window, values=["Work", "Personal", "Learning", "Health", "Other"])
        category_combo.pack(pady=5)


        tk.Label(add_window, text="Priority").pack(pady=5)
        priority_combo = ttk.Combobox(add_window, values=["High", "Medium", "Low"])
        priority_combo.pack(pady=5)

        def save_task():
            task_name = task_name_entry.get()
            deadline = deadline_entry.get()
            category = category_combo.get() or "General"
            priority = priority_combo.get() or "Medium"

            if task_name and deadline:
                self.db.add_task(task_name, deadline, category, priority)
                tk.Label(add_window, text="Task added successfully!", fg="green").pack(pady=5)
                add_window.after(1000, add_window.destroy)
            else:
                tk.Label(add_window, text="Please fill in all required fields.", fg="red").pack(pady=5)

        tk.Button(add_window, text="Save Task", command=save_task).pack(pady=20)

    def view_tasks_window(self):
        view_window = tk.Toplevel(self.master)
        view_window.title("View Tasks")
        view_window.geometry("600x400")

        task_list = tk.Listbox(view_window, width=80, height=20)
        task_list.pack(pady=10)

        tasks = self.db.get_tasks()
        for task in tasks:
            status = "✅" if task[5] == "completed" else "❌"
            task_list.insert(tk.END, f"{task[1]} (Priority: {task[3]}, Deadline: {task[2]}) - Status: {status}")

    def complete_task_window(self):
        complete_window = tk.Toplevel(self.master)
        complete_window.title("Complete Task")
        complete_window.geometry("400x300")

        tk.Label(complete_window, text="Task Name to Complete").pack(pady=5)
        task_name_entry = tk.Entry(complete_window)
        task_name_entry.pack(pady=5)

        def mark_complete():
            task_name = task_name_entry.get()
            for task in self.db.get_tasks():
                task_id, name, deadline, category, priority, status, created_at = task
                if name.lower() == task_name.lower() and status == "pending":
                    self.db.update_task(task_id, "status", "completed")
                    tk.Label(complete_window, text=f"Task '{task_name}' marked as completed!", fg="green").pack(pady=5)
                    return
            tk.Label(complete_window, text=f"Task '{task_name}' not found or already completed.", fg="red").pack(pady=5)

        tk.Button(complete_window, text="Mark Complete", command=mark_complete).pack(pady=10)

    def filter_tasks_window(self):
        filter_window = tk.Toplevel(self.master)
        filter_window.title("Filter Tasks")
        filter_window.geometry("500x500")

        tk.Label(filter_window, text="Filter by Priority").pack(pady=5)
        priority_combo = ttk.Combobox(filter_window, values=["High", "Medium", "Low"])
        priority_combo.pack(pady=5)

        tk.Label(filter_window, text="Filter by Category").pack(pady=5)
        category_combo = ttk.Combobox(filter_window, values=["Work", "Personal", "Learning", "Health", "Other"])
        category_combo.pack(pady=5)

        tk.Label(filter_window, text="Filter by Due Date").pack(pady=5)
        due_date_combo = ttk.Combobox(filter_window, values=["Today", "This Week", "This Month"])
        due_date_combo.pack(pady=5)

        task_list = tk.Listbox(filter_window, width=80, height=15)
        task_list.pack(pady=10)

        def apply_filters():
            filtered_tasks = self.db
            priority = priority_combo.get()
            category = category_combo.get()
            due_date = due_date_combo.get()

            # Filter by Priority
            if priority:
                filtered_tasks = [task for task in filtered_tasks if task["priority"].lower() == priority.lower()]

            # Filter by Category
            if category:
                filtered_tasks = [task for task in filtered_tasks if task.get("category", "General").lower() == category.lower()]

            # Filter by Due Date
            if due_date:
                now = datetime.now()
                if due_date == "Today":
                    filtered_tasks = [
                        task for task in filtered_tasks
                        if self.is_valid_deadline(task["deadline"]) and datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").date() == now.date()
                    ]
                elif due_date == "This Week":
                    week_start = now - timedelta(days=now.weekday())
                    week_end = week_start + timedelta(days=6)
                    filtered_tasks = [
                        task for task in filtered_tasks
                        if self.is_valid_deadline(task["deadline"]) and
                        week_start.date() <= datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").date() <= week_end.date()
                    ]
                elif due_date == "This Month":
                    filtered_tasks = [
                        task for task in filtered_tasks
                        if self.is_valid_deadline(task["deadline"]) and
                        datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").month == now.month
                    ]

            # Display Filtered Tasks
            task_list.delete(0, tk.END)
            if not filtered_tasks:
                task_list.insert(tk.END, "No tasks match the selected filters.")
            else:
                for task in filtered_tasks:
                    status = "✅" if task["status"] == "completed" else "❌"
                    overdue = " (Overdue)" if self.is_overdue(task["deadline"]) else ""
                    task_list.insert(
                        tk.END,
                        f"{task['name']} [Priority: {task['priority']}, Category: {task.get('category', 'General')}] - {status}{overdue}"
                    )

        tk.Button(filter_window, text="Apply Filters", command=apply_filters).pack(pady=10)

    def show_statistics_window(self):
        stats_window = tk.Toplevel(self.master)
        stats_window.title("Task Statistics")
        stats_window.geometry("500x300")

        tasks = self.db.get_tasks()
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task[5] == "completed")
        pending_tasks = sum(1 for task in tasks if task[5] == "pending")
        category_counts = Counter(task[3] for task in tasks)  # task[3] is category
        priority_counts = Counter(task[4] for task in tasks)  # task[4] is priority

        tk.Label(stats_window, text=f"Total Tasks: {total_tasks}").pack(pady=5)
        tk.Label(stats_window, text=f"Completed Tasks: {completed_tasks}").pack(pady=5)
        tk.Label(stats_window, text=f"Pending Tasks: {pending_tasks}").pack(pady=5)

        def show_category_chart():
            categories, counts = zip(*category_counts.items())
            plt.figure(figsize=(6, 4))
            plt.bar(categories, counts, color='skyblue')
            plt.title("Tasks by Category")
            plt.xlabel("Category")
            plt.ylabel("Count")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

        def show_priority_chart():
            priorities, counts = zip(*priority_counts.items())
            plt.figure(figsize=(6, 4))
            plt.pie(counts, labels=priorities, autopct='%1.1f%%', startangle=140)
            plt.title("Tasks by Priority")
            plt.tight_layout()
            plt.show()

        tk.Button(stats_window, text="Show Category Chart", command=show_category_chart).pack(pady=10)
        tk.Button(stats_window, text="Show Priority Chart", command=show_priority_chart).pack(pady=10)


    def edit_task_window(self):
        # Create a new window to edit tasks
        edit_window = tk.Toplevel(self.master)
        edit_window.title("Edit Task")
        edit_window.geometry("600x400")

        tk.Label(edit_window, text="Select a Task to Edit").pack(pady=5)

        # Listbox to display tasks
        task_list = tk.Listbox(edit_window, width=80, height=15)
        task_list.pack(pady=10)

        # Populate the listbox with tasks
        for task in self.db.get_tasks():
            status = "✅" if task["status"] == "completed" else "❌"
            task_list.insert(
                tk.END,
                f"{task['name']} [Priority: {task['priority']}, Category: {task.get('category', 'General')}] - Status: {status}"
            )

        # Function to open the edit form
        def open_edit_form():
            try:
                selected_index = task_list.curselection()[0]
                selected_task = self.db[selected_index]

                # Create an edit form pre-filled with task details
                form_window = tk.Toplevel(edit_window)
                form_window.title("Edit Task")
                form_window.geometry("400x400")

                tk.Label(form_window, text="Task Name").pack(pady=5)
                name_entry = tk.Entry(form_window, width=40)
                name_entry.insert(0, selected_task["name"])
                name_entry.pack(pady=5)

                tk.Label(form_window, text="Deadline").pack(pady=5)
                deadline_entry = tk.Entry(form_window, width=40)
                deadline_entry.insert(0, selected_task["deadline"])
                deadline_entry.pack(pady=5)

                tk.Label(form_window, text="Category").pack(pady=5)
                category_combo = ttk.Combobox(form_window, values=["Work", "Personal", "Learning", "Health", "Other"])
                category_combo.set(selected_task.get("category", "General"))
                category_combo.pack(pady=5)

                tk.Label(form_window, text="Priority").pack(pady=5)
                priority_combo = ttk.Combobox(form_window, values=["High", "Medium", "Low"])
                priority_combo.set(selected_task["priority"])
                priority_combo.pack(pady=5)

                # Save the edited task
                def save_edits():
                    selected_task["name"] = name_entry.get()
                    selected_task["deadline"] = deadline_entry.get()
                    selected_task["category"] = category_combo.get()
                    selected_task["priority"] = priority_combo.get()
                    self.save_tasks()

                    # Display success message
                    success_label = tk.Label(form_window, text="Task updated successfully!", fg="green")
                    success_label.pack(pady=5)

                    # Refresh the task list
                    task_list.delete(0, tk.END)
                    for task in self.db.get_tasks():
                        status = "✅" if task["status"] == "completed" else "❌"
                        task_list.insert(
                            tk.END,
                            f"{task['name']} [Priority: {task['priority']}, Category: {task.get('category', 'General')}] - Status: {status}"
                        )
                        
                    # Close the edit form window after 1 second
                    form_window.after(1000, form_window.destroy)

                tk.Button(form_window, text="Save Changes", command=save_edits).pack(pady=10)

            except IndexError:
                tk.Label(edit_window, text="Please select a task to edit.", fg="red").pack(pady=5)

        tk.Button(edit_window, text="Edit Selected Task", command=open_edit_form).pack(pady=10)
    
    def start_notification_checker(self):
        def check_deadlines():
            while True:
                now = datetime.now()
                tasks = self.db.get_tasks()
                for task in tasks:
                    task_id, name, deadline, category, priority, status, created_at = task
                    if status == "pending":
                        try:
                            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
                            time_left = (deadline_dt - now).total_seconds()
                            if time_left < 0:
                                self.show_notification(f"Task Overdue: {name}", f"Deadline was {deadline}")
                            elif 0 <= time_left <= 300:  # Due within 5 minutes
                                self.show_notification(f"Task Due Soon: {name}", f"Deadline: {deadline}")
                        except ValueError:
                            print(f"Invalid deadline format for task '{name}': {deadline}")
                time.sleep(60) # Check every 60 seconds



        notification_thread = threading.Thread(target=check_deadlines, daemon=True)
        notification_thread.start()    

    def show_notification(self, title, message):
        notification_window = tk.Toplevel(self.master)
        notification_window.title("Notification")
        notification_window.geometry("300x150")

        tk.Label(notification_window, text=title, font=("Helvetica", 12, "bold")).pack(pady=10)
        tk.Label(notification_window, text=message, wraplength=250).pack(pady=10)

        # Close button to dismiss the notification
        tk.Button(notification_window, text="Close", command=notification_window.destroy).pack(pady=10)

        # Auto-close the notification after 5 seconds
        notification_window.after(5000, notification_window.destroy)

    def is_valid_deadline(self, deadline):
        try:
            datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            return False


    def add_task(self, name, deadline_input, category="General", priority="Medium", recurrence=None):
        deadline = self.parse_deadline(deadline_input)
        if not deadline:
            print("Invalid deadline format. Please try again.")
            return

        self.db.append({
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
            # For specific time (e.g., "2025-01-05 14:30")
            if " " in deadline_input:
                return datetime.strptime(deadline_input, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            # For relative times like "5m", "2h"
            elif deadline_input.endswith("m"):
                minutes = int(deadline_input[:-1])
                return (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
            elif deadline_input.endswith("h"):
                hours = int(deadline_input[:-1])
                return (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Default to full date (e.g., "2025-01-05")
                return datetime.strptime(deadline_input, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def complete_task(self, name):
        for task in self.db.get_tasks():
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

        self.db.append({
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
        if not self.db:
            print("No tasks available.")
        else:
            # Filter tasks by priority if specified
            tasks_to_display = (
                [task for task in self.db.get_tasks() if task["priority"].lower() == filter_priority.lower()]
                if filter_priority else self.db
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
        for task in self.db.get_tasks():
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
        for task in self.db.get_tasks():
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
        overdue_tasks = [task for task in self.db.get_tasks() if self.is_overdue(task["deadline"]) and task["status"] == "pending"]

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
        for task in self.db.get_tasks():
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
        total_tasks = len(self.db)
        completed_tasks = len([task for task in self.db.get_tasks() if task["status"] == "completed"])
        pending_tasks = len([task for task in self.db.get_tasks() if task["status"] == "pending"])
        overdue_tasks = len([task for task in self.db.get_tasks() if self.is_overdue(task["deadline"]) and task["status"] == "pending"])

        # Category Breakdown
        category_counts = {}
        for task in self.db.get_tasks():
            category = task.get("category", "General")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Priority Breakdown
        priority_counts = {"High": 0, "Medium": 0, "Low": 0}
        for task in self.db.get_tasks():
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
            filtered_tasks = [task for task in self.db.get_tasks() if task["priority"].lower() == value.lower()]
        elif by == "category":
            filtered_tasks = [task for task in self.db.get_tasks() if task.get("category", "General").lower() == value.lower()]
        elif by == "due_date":
            now = datetime.now()
            if value == "today":
                filtered_tasks = [
                    task for task in self.db.get_tasks() if datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").date() == now.date()
                ]
            elif value == "this_week":
                week_start = now - timedelta(days=now.weekday())
                week_end = week_start + timedelta(days=6)
                filtered_tasks = [
                    task for task in self.db.get_tasks()
                    if week_start.date()
                    <= datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M:%S").date()
                    <= week_end.date()
                ]
            elif value == "this_month":
                filtered_tasks = [
                    task for task in self.db.get_tasks()
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

class TaskDatabase:
    def __init__(self, db_file="tasks.db"):
        self.db_file = db_file
        self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()
        
    def get_connection(self):
        """Creates a new SQLite connection for the current thread."""
        return sqlite3.connect(self.db_file)

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            deadline TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """)
        self.connection.commit()

    def add_task(self, name, deadline, category, priority):
        self.cursor.execute("""
        INSERT INTO tasks (name, deadline, category, priority, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (name, deadline, category, priority, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.connection.commit()

    def get_tasks(self):
        """Fetches all tasks using a thread-safe connection."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            return cursor.fetchall()

    def update_task(self, task_id, field, value):
        self.cursor.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (value, task_id))
        self.connection.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.connection.commit()

    def close(self):
        self.connection.close()

# Background thread to periodically check deadlines
def start_deadline_checker(planner):
    def periodic_check():
        while True:
            planner.check_deadlines()
            time.sleep(60)

    thread = threading.Thread(target=periodic_check, daemon=True)
    thread.start()

# Initialize GUI
root = tk.Tk()
app = TaskPlanner(root)
root.mainloop()

# Example Usage
# if __name__ == "__main__":
    # planner = TaskPlanner()
    # start_deadline_checker(planner)

    # # while True:
    #     print("\nTask Planner Options:")
    #     print("1. Add Task")
    #     print("2. Complete Task")
    #     print("3. Update Task")
    #     print("4. View Tasks")
    #     print("5. Filter Tasks")
    #     print("6. Overdue Task Management")
    #     print("7. View Task Statistics")
    #     print("8. Exit")
    #     choice = input("Choose an option: ")

    #     if choice == "1":
    #         name = input("Enter task name: ")
    #         deadline = input("Enter task deadline (e.g., '5m', '2h', '2025-01-05 14:30'): ")
    #         category = input("Enter task category (e.g., Work, Personal): ")
    #         priority = input("Enter task priority (High, Medium, Low): ")
    #         recurrence = input("Enter recurrence (daily, weekly, monthly, or leave blank): ")
    #         planner.add_task(name, deadline, category, priority, recurrence)

    #     elif choice == "2":
    #         name = input("Enter task name to mark as complete: ")
    #         planner.complete_task(name)

    #     elif choice == "3":
    #         name = input("Enter task name to update: ")
    #         field = input("Enter the field to update (e.g., name, deadline, category, priority, recurrence): ")
    #         value = input(f"Enter new value for {field}: ")
    #         planner.update_task(name, field, value)

    #     elif choice == "4":
    #         planner.list_tasks()

    #     elif choice == "5":
    #         print("\nFilter Tasks Options:")
    #         print("1. Filter by Priority")
    #         print("2. Filter by Category")
    #         print("3. Filter by Due Date (Today, This Week, This Month)")
    #         filter_choice = input("Choose an option: ")

    #         if filter_choice == "1":
    #             priority = input("Enter priority to filter by (High, Medium, Low): ")
    #             planner.filter_tasks(by="priority", value=priority)

    #         elif filter_choice == "2":
    #             category = input("Enter category to filter by (e.g., Work, Personal): ")
    #             planner.filter_tasks(by="category", value=category)

    #         elif filter_choice == "3":
    #             print("1. Due Today")
    #             print("2. Due This Week")
    #             print("3. Due This Month")
    #             date_filter = input("Choose an option: ")
    #             if date_filter == "1":
    #                 planner.filter_tasks(by="due_date", value="today")
    #             elif date_filter == "2":
    #                 planner.filter_tasks(by="due_date", value="this_week")
    #             elif date_filter == "3":
    #                 planner.filter_tasks(by="due_date", value="this_month")
    #             else:
    #                 print("Invalid choice. Returning to main menu.")

    #         else:
    #             print("Invalid choice. Returning to main menu.")


    #     elif choice == "6":
    #         print("\nManaging Overdue Tasks...")
    #         planner.list_overdue_tasks()

    #     elif choice == "7":
    #         planner.show_statistics()

    #     elif choice == "8":
    #         print("Goodbye!")
    #         break

    #     else:
    #         print("Invalid choice. Please try again.")
