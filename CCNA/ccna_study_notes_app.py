import json
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError as error:
    print()
    print("Tkinter could not be loaded.")
    print()
    print("This usually means the system Tk library is missing.")
    print()
    print("Arch Linux:")
    print("  sudo pacman -S tk")
    print()
    print("Debian/Ubuntu:")
    print("  sudo apt update")
    print("  sudo apt install python3-tk tk")
    print()
    print("Original error:")
    print(f"  {error}")
    print()
    sys.exit(1)


APP_TITLE = "CCNA 200-301 Study Notes"
NOTES_FILE = Path("ccna_study_notes.json")


STUDY_PLAN = {
    "Week 1 - Introduction to Networking": [
        "Chapter 1 - Introduction to TCP/IP Networking",
        "Chapter 2 - Fundamentals of Ethernet LANs",
        "Chapter 3 - Fundamentals of WANs and IP Routing",
    ],
    "Week 2 - Implementing Ethernet LANs": [
        "Chapter 4 - Using the Command-Line Interface",
        "Chapter 5 - Analyzing Ethernet LAN Switching",
        "Chapter 6 - Configuring Basic Switch Management",
        "Chapter 7 - Configuring and Verifying Switch Interfaces",
    ],
    "Week 3 - Implementing VLANs and STP": [
        "Chapter 8 - Implementing Ethernet Virtual LANs",
        "Chapter 9 - Spanning Tree Protocol Concepts",
        "Chapter 10 - RSTP and EtherChannel Configuration",
    ],
    "Week 4 - IPv4 Addressing": [
        "Chapter 11 - Perspectives on IPv4 Subnetting",
        "Chapter 12 - Analyzing Classful IPv4 Networks",
        "Chapter 13 - Analyzing Subnet Masks",
        "Chapter 14 - Analyzing Existing Subnets",
        "Chapter 15 - Subnet Design",
    ],
    "Week 5 - IPv4 Routing": [
        "Chapter 16 - Operating Cisco Routers",
        "Chapter 17 - Configuring IPv4 Addresses and Static Routes",
        "Chapter 18 - IP Routing in the LAN",
        "Chapter 19 - IP Addressing on Hosts",
        "Chapter 20 - Troubleshooting IPv4 Routing",
    ],
    "Week 6 - OSPF": [
        "Chapter 21 - Understanding OSPF Concepts",
        "Chapter 22 - Implementing Basic OSPF Features",
        "Chapter 23 - Implementing Optional OSPF Features",
        "Chapter 24 - OSPF Neighbors and Route Selection",
    ],
    "Week 7 - IP Version 6": [
        "Chapter 25 - Fundamentals of IP Version 6",
        "Chapter 26 - IPv6 Addressing and Subnetting",
        "Chapter 27 - Implementing IPv6 Addressing on Routers",
        "Chapter 28 - Implementing IPv6 Addressing on Hosts",
        "Chapter 29 - Implementing IPv6 Routing",
    ],
    "Week 8 - Exam Updates and Appendixes": [
        "Chapter 30 - CCNA 200-301 Official Cert Guide, Volume 1, Second Edition Exam Updates",
        "Appendix A - Numeric Reference Tables",
        "Appendix B - Exam Topics Cross-Reference",
        "Appendix C - Answers to the Do I Know This Already? Quizzes",
        "Appendix D - Practice for Chapter 12: Analyzing Classful IPv4 Networks",
        "Appendix E - Practice for Chapter 13: Analyzing Subnet Masks",
        "Appendix F - Practice for Chapter 14: Analyzing Existing Subnets",
        "Appendix G - Practice for Chapter 15: Subnet Design",
        "Appendix H - Practice for Chapter 25: Fundamentals of IP Version 6",
        "Appendix I - Practice for Chapter 27: Implementing IPv6 Addressing on Routers",
        "Appendix J - Study Planner",
        "Appendix K - Topics from Previous Editions",
        "Appendix L - LAN Troubleshooting",
        "Appendix M - Variable-Length Subnet Masks",
    ],
    "Week 9 - Final Review and Practice Exams": [
        "Full Practice Exam 1",
        "Full Practice Exam 2",
        "Wrong Answer Review",
        "Subnetting Review",
        "IPv4 Routing Review",
        "OSPF Review",
        "IPv6 Review",
        "Switching Review",
        "VLAN and STP Review",
        "Final Readiness Check",
    ],
}


class StudyNotesApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1150x750")
        self.minsize(1000, 650)

        self.notes = self.load_notes()

        self.current_week = tk.StringVar(value=list(STUDY_PLAN.keys())[0])
        self.current_topic = tk.StringVar(value=STUDY_PLAN[self.current_week.get()][0])

        self.topic_buttons = {}
        self.autosave_job = None
        self.clear_status_job = None

        self.build_ui()
        self.load_week(self.current_week.get())

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 12))

        app_title = ttk.Label(
            header_frame,
            text=APP_TITLE,
            font=("TkDefaultFont", 16, "bold"),
        )
        app_title.pack(side="left", padx=(0, 20))

        ttk.Label(header_frame, text="Week:").pack(side="left")

        self.week_dropdown = ttk.Combobox(
            header_frame,
            textvariable=self.current_week,
            values=list(STUDY_PLAN.keys()),
            state="readonly",
            width=65,
        )
        self.week_dropdown.pack(side="left", padx=(8, 12))
        self.week_dropdown.bind("<<ComboboxSelected>>", self.on_week_change)

        save_button = ttk.Button(
            header_frame,
            text="Save Notes",
            command=self.save_current_note,
        )
        save_button.pack(side="left", padx=4)

        clear_button = ttk.Button(
            header_frame,
            text="Clear Chapter",
            command=self.clear_current_topic,
        )
        clear_button.pack(side="left", padx=4)

        self.status_label = ttk.Label(header_frame, text="")
        self.status_label.pack(side="right")

        body = ttk.PanedWindow(main_frame, orient="horizontal")
        body.pack(fill="both", expand=True)

        left_panel = ttk.Frame(body, padding=(0, 0, 12, 0))
        right_panel = ttk.Frame(body)

        body.add(left_panel, weight=1)
        body.add(right_panel, weight=3)

        chapters_header = ttk.Label(
            left_panel,
            text="Chapters",
            font=("TkDefaultFont", 14, "bold"),
        )
        chapters_header.pack(anchor="w", pady=(0, 8))

        self.week_title_label = ttk.Label(
            left_panel,
            text="",
            font=("TkDefaultFont", 11, "bold"),
            wraplength=360,
            justify="left",
        )
        self.week_title_label.pack(anchor="w", pady=(0, 10))

        chapter_list_frame = ttk.Frame(left_panel)
        chapter_list_frame.pack(fill="both", expand=True)

        self.topic_canvas = tk.Canvas(chapter_list_frame, highlightthickness=0)
        self.topic_canvas.pack(side="left", fill="both", expand=True)

        topic_scrollbar = ttk.Scrollbar(
            chapter_list_frame,
            orient="vertical",
            command=self.topic_canvas.yview,
        )
        topic_scrollbar.pack(side="right", fill="y")

        self.topic_canvas.configure(yscrollcommand=topic_scrollbar.set)

        self.topic_container = ttk.Frame(self.topic_canvas)
        self.topic_canvas_window = self.topic_canvas.create_window(
            (0, 0),
            window=self.topic_container,
            anchor="nw",
        )

        self.topic_container.bind(
            "<Configure>",
            self.update_topic_scroll_region,
        )

        self.topic_canvas.bind(
            "<Configure>",
            self.resize_topic_container,
        )

        self.topic_canvas.bind("<Enter>", self.bind_topic_mousewheel)
        self.topic_canvas.bind("<Leave>", self.unbind_topic_mousewheel)

        notes_header_frame = ttk.Frame(right_panel)
        notes_header_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            notes_header_frame,
            text="Notes for:",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(side="left")

        self.topic_title_label = ttk.Label(
            notes_header_frame,
            text="",
            font=("TkDefaultFont", 14, "bold"),
            wraplength=700,
            justify="left",
        )
        self.topic_title_label.pack(side="left", padx=(8, 0))

        notes_frame = ttk.Frame(right_panel)
        notes_frame.pack(fill="both", expand=True)

        self.notes_text = tk.Text(
            notes_frame,
            wrap="word",
            undo=True,
            font=("TkDefaultFont", 11),
            padx=12,
            pady=12,
        )
        self.notes_text.pack(side="left", fill="both", expand=True)
        self.notes_text.bind("<KeyRelease>", self.schedule_autosave)

        notes_scrollbar = ttk.Scrollbar(
            notes_frame,
            orient="vertical",
            command=self.notes_text.yview,
        )
        notes_scrollbar.pack(side="right", fill="y")

        self.notes_text.configure(yscrollcommand=notes_scrollbar.set)

        footer = ttk.Frame(main_frame)
        footer.pack(fill="x", pady=(10, 0))

        footer_text = (
            "Select a week, then click a chapter. "
            "Each chapter has separate notes. "
            "Notes are saved locally in ccna_study_notes.json."
        )
        ttk.Label(footer, text=footer_text).pack(anchor="w")

    def bind_topic_mousewheel(self, event=None):
        self.topic_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.topic_canvas.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.topic_canvas.bind_all("<Button-5>", self.on_mousewheel_linux)

    def unbind_topic_mousewheel(self, event=None):
        self.topic_canvas.unbind_all("<MouseWheel>")
        self.topic_canvas.unbind_all("<Button-4>")
        self.topic_canvas.unbind_all("<Button-5>")

    def on_mousewheel(self, event):
        self.topic_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_linux(self, event):
        if event.num == 4:
            self.topic_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.topic_canvas.yview_scroll(1, "units")

    def update_topic_scroll_region(self, event=None):
        self.topic_canvas.configure(scrollregion=self.topic_canvas.bbox("all"))

    def resize_topic_container(self, event):
        self.topic_canvas.itemconfigure(
            self.topic_canvas_window,
            width=event.width,
        )

    def load_notes(self):
        if not NOTES_FILE.exists():
            return {}

        try:
            with NOTES_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {}

            return self.normalize_notes_data(data)

        except json.JSONDecodeError:
            messagebox.showwarning(
                "Invalid JSON",
                f"{NOTES_FILE} could not be read. A new notes file will be created.",
            )
            return {}

        except OSError as error:
            messagebox.showerror(
                "File Error",
                f"Could not read {NOTES_FILE}.\n\n{error}",
            )
            return {}

    def normalize_notes_data(self, data):
        """
        Supports both:
        1. Current format:
           {
             "Week 1 - Introduction to Networking": {
               "Chapter 1 - Introduction to TCP/IP Networking": "notes"
             }
           }

        2. Old week-level format:
           {
             "Week 1 - Introduction to Networking": "old week-level notes"
           }

        Old week-level notes are moved into the first chapter of that week.
        """
        normalized = {}

        for week, topics in STUDY_PLAN.items():
            normalized[week] = {}

            existing_week_data = data.get(week, {})

            if isinstance(existing_week_data, str):
                first_topic = topics[0]
                normalized[week][first_topic] = existing_week_data

            elif isinstance(existing_week_data, dict):
                for topic in topics:
                    value = existing_week_data.get(topic, "")
                    normalized[week][topic] = value if isinstance(value, str) else ""

            else:
                for topic in topics:
                    normalized[week][topic] = ""

            for topic in topics:
                if topic not in normalized[week]:
                    normalized[week][topic] = ""

        return normalized

    def ensure_week_exists(self, week):
        if week not in self.notes:
            self.notes[week] = {}

        for topic in STUDY_PLAN[week]:
            if topic not in self.notes[week]:
                self.notes[week][topic] = ""

    def write_notes_file(self):
        try:
            with NOTES_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.notes, file, indent=2, ensure_ascii=False)

        except OSError as error:
            messagebox.showerror(
                "File Error",
                f"Could not save notes to {NOTES_FILE}.\n\n{error}",
            )

    def on_week_change(self, event=None):
        self.save_current_note(show_message=False)

        selected_week = self.current_week.get()
        first_topic = STUDY_PLAN[selected_week][0]

        self.current_topic.set(first_topic)
        self.load_week(selected_week)

    def load_week(self, week):
        self.ensure_week_exists(week)

        self.week_title_label.configure(text=week)

        for widget in self.topic_container.winfo_children():
            widget.destroy()

        self.topic_buttons = {}

        for index, topic in enumerate(STUDY_PLAN[week], start=1):
            button_text = f"{index}. {topic}"

            button = tk.Button(
                self.topic_container,
                text=button_text,
                anchor="w",
                justify="left",
                wraplength=360,
                relief="flat",
                padx=8,
                pady=8,
                command=lambda selected_topic=topic: self.select_topic(selected_topic),
            )
            button.pack(fill="x", pady=(0, 4))

            self.topic_buttons[topic] = button

        self.load_topic(self.current_topic.get())

    def select_topic(self, topic):
        if topic == self.current_topic.get():
            return

        self.save_current_note(show_message=False)
        self.current_topic.set(topic)
        self.load_topic(topic)

    def load_topic(self, topic):
        week = self.current_week.get()
        self.ensure_week_exists(week)

        self.topic_title_label.configure(text=topic)

        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", self.notes[week].get(topic, ""))

        self.highlight_selected_topic()
        self.set_status(f"Loaded: {topic}")

    def highlight_selected_topic(self):
        selected_topic = self.current_topic.get()

        for topic, button in self.topic_buttons.items():
            if topic == selected_topic:
                button.configure(
                    relief="sunken",
                    bg="#d9eaff",
                    activebackground="#d9eaff",
                )
            else:
                button.configure(
                    relief="flat",
                    bg=self.cget("bg"),
                    activebackground=self.cget("bg"),
                )

    def save_current_note(self, show_message=True):
        week = self.current_week.get()
        topic = self.current_topic.get()

        self.ensure_week_exists(week)

        content = self.notes_text.get("1.0", "end-1c")
        self.notes[week][topic] = content

        self.write_notes_file()

        if show_message:
            self.set_status("Saved")

    def schedule_autosave(self, event=None):
        if self.autosave_job is not None:
            self.after_cancel(self.autosave_job)

        self.autosave_job = self.after(1000, self.autosave)

    def autosave(self):
        self.save_current_note(show_message=False)
        self.set_status("Autosaved")
        self.autosave_job = None

    def clear_current_topic(self):
        week = self.current_week.get()
        topic = self.current_topic.get()

        confirmed = messagebox.askyesno(
            "Clear Chapter Notes",
            f"Clear notes for this chapter?\n\n{week}\n{topic}",
        )

        if not confirmed:
            return

        self.notes_text.delete("1.0", "end")
        self.notes[week][topic] = ""
        self.write_notes_file()
        self.set_status("Cleared")

    def set_status(self, message):
        self.status_label.configure(text=message)

        if self.clear_status_job is not None:
            self.after_cancel(self.clear_status_job)

        self.clear_status_job = self.after(2500, self.clear_status)

    def clear_status(self):
        self.status_label.configure(text="")
        self.clear_status_job = None

    def on_close(self):
        if self.autosave_job is not None:
            self.after_cancel(self.autosave_job)
            self.autosave_job = None

        self.save_current_note(show_message=False)
        self.destroy()


def main():
    app = StudyNotesApp()
    app.mainloop()


if __name__ == "__main__":
    main()
