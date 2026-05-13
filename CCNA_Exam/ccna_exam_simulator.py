import json
import random
import time
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from datetime import datetime


QUESTION_BANK_FILE = "question_bank.json"
EXAM_QUESTION_COUNT = 120
EXAM_DURATION_SECONDS = 2 * 60 * 60  # 2 hours


SAMPLE_QUESTIONS = [
    {
        "id": 1,
        "type": "single",
        "question": "Which OSI layer is responsible for logical addressing and routing?",
        "options": [
            "Layer 1 - Physical",
            "Layer 2 - Data Link",
            "Layer 3 - Network",
            "Layer 4 - Transport"
        ],
        "answer": [2],
        "explanation": "Layer 3, the Network layer, handles logical addressing and routing."
    },
    {
        "id": 2,
        "type": "multiple",
        "question": "Which two protocols are used for dynamic routing? Choose two.",
        "options": [
            "OSPF",
            "ARP",
            "EIGRP",
            "DHCP"
        ],
        "answer": [0, 2],
        "explanation": "OSPF and EIGRP are dynamic routing protocols."
    }
]


class CCNAExamSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("CCNA 200-301 Exam Simulator")
        self.root.geometry("1000x720")

        self.question_bank = []
        self.exam_questions = []
        self.current_index = 0
        self.user_answers = {}
        self.marked_for_review = set()

        self.exam_started = False
        self.exam_submitted = False
        self.start_time = None
        self.remaining_seconds = EXAM_DURATION_SECONDS

        self.selected_single = tk.IntVar(value=-1)
        self.selected_multiple = []

        self.build_start_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_start_screen(self):
        self.clear_window()

        self.exam_started = False
        self.exam_submitted = False

        title = tk.Label(
            self.root,
            text="CCNA 200-301 Exam Simulator",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=30)

        info = tk.Label(
            self.root,
            text=(
                "Simulation settings:\n\n"
                f"Questions: {EXAM_QUESTION_COUNT} randomized, non-repeating questions\n"
                "Timer: 2 hours\n"
                "Question source: question_bank.json\n\n"
                "Supported question types:\n"
                "- single: one correct answer\n"
                "- multiple: multiple correct answers\n\n"
                "No answer is pre-selected when a new question is displayed."
            ),
            font=("Arial", 14),
            justify="left"
        )
        info.pack(pady=20)

        start_button = tk.Button(
            self.root,
            text="Start Exam",
            font=("Arial", 14, "bold"),
            width=25,
            command=self.start_exam
        )
        start_button.pack(pady=20)

        load_button = tk.Button(
            self.root,
            text="Load Different Question Bank",
            font=("Arial", 12),
            width=30,
            command=self.load_custom_question_bank
        )
        load_button.pack(pady=5)

        sample_button = tk.Button(
            self.root,
            text="Create Sample question_bank.json",
            font=("Arial", 12),
            width=30,
            command=self.create_sample_question_bank
        )
        sample_button.pack(pady=5)

    def create_sample_question_bank(self):
        path = Path(QUESTION_BANK_FILE)

        if path.exists():
            overwrite = messagebox.askyesno(
                "File exists",
                "question_bank.json already exists. Overwrite it?"
            )
            if not overwrite:
                return

        with open(path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_QUESTIONS, f, indent=4)

        messagebox.showinfo(
            "Created",
            "Sample question_bank.json created. Replace it with your own full question bank."
        )

    def load_custom_question_bank(self):
        file_path = filedialog.askopenfilename(
            title="Select question bank",
            filetypes=[("JSON files", "*.json")]
        )

        if not file_path:
            return

        global QUESTION_BANK_FILE
        QUESTION_BANK_FILE = file_path

        messagebox.showinfo(
            "Loaded",
            f"Selected question bank:\n{file_path}"
        )

    def load_questions(self):
        path = Path(QUESTION_BANK_FILE)

        if not path.exists():
            messagebox.showerror(
                "Missing question bank",
                (
                    f"Could not find {QUESTION_BANK_FILE}.\n\n"
                    "Create a question_bank.json file first, or use the sample generator."
                )
            )
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                questions = json.load(f)
        except Exception as e:
            messagebox.showerror("JSON error", f"Could not read question bank:\n{e}")
            return False

        if not isinstance(questions, list):
            messagebox.showerror(
                "Invalid format",
                "question_bank.json must contain a list of question objects."
            )
            return False

        valid_questions = []

        for q in questions:
            if self.validate_question(q):
                valid_questions.append(q)

        if not valid_questions:
            messagebox.showerror(
                "No valid questions",
                "The question bank does not contain any valid questions."
            )
            return False

        unique_questions = self.remove_duplicate_questions(valid_questions)

        if len(unique_questions) < len(valid_questions):
            removed = len(valid_questions) - len(unique_questions)
            messagebox.showinfo(
                "Duplicates removed",
                f"{removed} duplicate question(s) were ignored."
            )

        if len(unique_questions) < EXAM_QUESTION_COUNT:
            proceed = messagebox.askyesno(
                "Not enough questions",
                (
                    f"Question bank contains only {len(unique_questions)} unique valid questions.\n\n"
                    f"The simulator is configured for {EXAM_QUESTION_COUNT} questions.\n\n"
                    "Do you want to start with all available questions?"
                )
            )

            if not proceed:
                return False

        self.question_bank = unique_questions
        return True

    def remove_duplicate_questions(self, questions):
        """
        Removes duplicates based on question text.

        This protects the exam session from duplicate questions even if the
        question_bank.json file contains repeated entries with different IDs.
        """
        seen = set()
        unique = []

        for q in questions:
            normalized_question = " ".join(q["question"].lower().split())

            if normalized_question not in seen:
                seen.add(normalized_question)
                unique.append(q)

        return unique

    def validate_question(self, q):
        required_fields = ["id", "type", "question", "options", "answer"]

        for field in required_fields:
            if field not in q:
                return False

        if q["type"] not in ["single", "multiple"]:
            return False

        if not isinstance(q["question"], str) or not q["question"].strip():
            return False

        if not isinstance(q["options"], list) or len(q["options"]) < 2:
            return False

        if not isinstance(q["answer"], list) or len(q["answer"]) < 1:
            return False

        for option in q["options"]:
            if not isinstance(option, str) or not option.strip():
                return False

        for answer_index in q["answer"]:
            if not isinstance(answer_index, int):
                return False

            if answer_index < 0 or answer_index >= len(q["options"]):
                return False

        if q["type"] == "single" and len(q["answer"]) != 1:
            return False

        if q["type"] == "multiple" and len(q["answer"]) < 2:
            return False

        return True

    def start_exam(self):
        if not self.load_questions():
            return

        question_count = min(EXAM_QUESTION_COUNT, len(self.question_bank))

        # random.sample guarantees no repeated question objects inside one exam session.
        self.exam_questions = random.sample(self.question_bank, question_count)

        self.current_index = 0
        self.user_answers = {}
        self.marked_for_review = set()

        self.exam_started = True
        self.exam_submitted = False
        self.start_time = time.time()
        self.remaining_seconds = EXAM_DURATION_SECONDS

        self.build_exam_screen()
        self.show_question()
        self.update_timer()

    def build_exam_screen(self):
        self.clear_window()

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=20, pady=10)

        self.timer_label = tk.Label(
            top_frame,
            text="Time remaining: 02:00:00",
            font=("Arial", 16, "bold")
        )
        self.timer_label.pack(side="left")

        self.progress_label = tk.Label(
            top_frame,
            text="Question 1/120",
            font=("Arial", 14)
        )
        self.progress_label.pack(side="right")

        self.question_frame = tk.Frame(self.root)
        self.question_frame.pack(fill="both", expand=True, padx=30, pady=20)

        self.question_text = tk.Label(
            self.question_frame,
            text="",
            wraplength=900,
            justify="left",
            font=("Arial", 15, "bold")
        )
        self.question_text.pack(anchor="w", pady=10)

        self.options_frame = tk.Frame(self.question_frame)
        self.options_frame.pack(anchor="w", fill="x", pady=10)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=20, pady=20)

        self.previous_button = tk.Button(
            bottom_frame,
            text="Previous",
            width=15,
            command=self.previous_question
        )
        self.previous_button.pack(side="left", padx=5)

        self.next_button = tk.Button(
            bottom_frame,
            text="Next",
            width=15,
            command=self.next_question
        )
        self.next_button.pack(side="left", padx=5)

        self.review_button = tk.Button(
            bottom_frame,
            text="Mark for Review",
            width=18,
            command=self.toggle_review
        )
        self.review_button.pack(side="left", padx=5)

        self.jump_button = tk.Button(
            bottom_frame,
            text="Question List",
            width=15,
            command=self.open_question_list
        )
        self.jump_button.pack(side="left", padx=5)

        self.clear_button = tk.Button(
            bottom_frame,
            text="Clear Answer",
            width=15,
            command=self.clear_current_answer
        )
        self.clear_button.pack(side="left", padx=5)

        self.submit_button = tk.Button(
            bottom_frame,
            text="Submit Exam",
            width=15,
            bg="#d9534f",
            fg="white",
            command=self.confirm_submit
        )
        self.submit_button.pack(side="right", padx=5)

    def show_question(self):
        """
        Displays the current question.

        Important:
        This function does not save answers. Answers are saved before changing
        question index. This prevents answers from being copied into the next
        question by mistake.
        """
        if self.exam_submitted:
            return

        q = self.exam_questions[self.current_index]

        self.progress_label.config(
            text=f"Question {self.current_index + 1}/{len(self.exam_questions)}"
        )

        review_status = " [Marked for Review]" if self.current_index in self.marked_for_review else ""

        self.question_text.config(
            text=f"{self.current_index + 1}. {q['question']}{review_status}"
        )

        for widget in self.options_frame.winfo_children():
            widget.destroy()

        saved_answer = self.user_answers.get(self.current_index, [])

        if q["type"] == "single":
            # No pre-selected answer for unanswered questions.
            # Tkinter radio buttons remain unselected when value is -1.
            selected_value = saved_answer[0] if saved_answer else -1
            self.selected_single = tk.IntVar(value=selected_value)

            for i, option in enumerate(q["options"]):
                rb = tk.Radiobutton(
                    self.options_frame,
                    text=f"{chr(65 + i)}. {option}",
                    variable=self.selected_single,
                    value=i,
                    font=("Arial", 13),
                    wraplength=850,
                    justify="left",
                    anchor="w"
                )
                rb.pack(anchor="w", pady=4)

        elif q["type"] == "multiple":
            self.selected_multiple = []

            for i, option in enumerate(q["options"]):
                # No pre-selected checkbox for unanswered questions.
                var = tk.BooleanVar(value=i in saved_answer)
                self.selected_multiple.append((i, var))

                cb = tk.Checkbutton(
                    self.options_frame,
                    text=f"{chr(65 + i)}. {option}",
                    variable=var,
                    font=("Arial", 13),
                    wraplength=850,
                    justify="left",
                    anchor="w"
                )
                cb.pack(anchor="w", pady=4)

        self.previous_button.config(
            state="normal" if self.current_index > 0 else "disabled"
        )

        self.next_button.config(
            state="normal" if self.current_index < len(self.exam_questions) - 1 else "disabled"
        )

        if self.current_index in self.marked_for_review:
            self.review_button.config(text="Unmark Review")
        else:
            self.review_button.config(text="Mark for Review")

    def save_current_answer(self):
        if not self.exam_questions:
            return

        q = self.exam_questions[self.current_index]

        if q["type"] == "single":
            selected = self.selected_single.get()

            if selected >= 0:
                self.user_answers[self.current_index] = [selected]
            else:
                self.user_answers.pop(self.current_index, None)

        elif q["type"] == "multiple":
            selected = [
                index for index, var in self.selected_multiple
                if var.get()
            ]

            if selected:
                self.user_answers[self.current_index] = selected
            else:
                self.user_answers.pop(self.current_index, None)

    def clear_current_answer(self):
        self.user_answers.pop(self.current_index, None)
        self.show_question()

    def previous_question(self):
        self.save_current_answer()

        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()

    def next_question(self):
        self.save_current_answer()

        if self.current_index < len(self.exam_questions) - 1:
            self.current_index += 1
            self.show_question()

    def toggle_review(self):
        self.save_current_answer()

        if self.current_index in self.marked_for_review:
            self.marked_for_review.remove(self.current_index)
        else:
            self.marked_for_review.add(self.current_index)

        self.show_question()

    def open_question_list(self):
        self.save_current_answer()

        window = tk.Toplevel(self.root)
        window.title("Question List")
        window.geometry("420x600")

        listbox = tk.Listbox(window, font=("Arial", 12))
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for i in range(len(self.exam_questions)):
            answered = "Answered" if i in self.user_answers else "Unanswered"
            review = "Review" if i in self.marked_for_review else ""

            label = f"Q{i + 1}: {answered}"

            if review:
                label += f" | {review}"

            listbox.insert(tk.END, label)

        def jump_to_question():
            selection = listbox.curselection()

            if not selection:
                return

            self.current_index = selection[0]
            window.destroy()
            self.show_question()

        jump_button = tk.Button(
            window,
            text="Go to Selected Question",
            command=jump_to_question
        )
        jump_button.pack(pady=10)

    def update_timer(self):
        if not self.exam_started or self.exam_submitted:
            return

        elapsed = int(time.time() - self.start_time)
        self.remaining_seconds = EXAM_DURATION_SECONDS - elapsed

        if self.remaining_seconds <= 0:
            self.remaining_seconds = 0
            self.timer_label.config(text="Time remaining: 00:00:00")
            messagebox.showinfo(
                "Time expired",
                "The 2-hour timer has expired. The exam will be submitted."
            )
            self.submit_exam()
            return

        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60

        self.timer_label.config(
            text=f"Time remaining: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

        self.root.after(1000, self.update_timer)

    def confirm_submit(self):
        self.save_current_answer()

        unanswered = len(self.exam_questions) - len(self.user_answers)

        confirm = messagebox.askyesno(
            "Submit exam",
            (
                f"Submit exam now?\n\n"
                f"Answered: {len(self.user_answers)}\n"
                f"Unanswered: {unanswered}\n"
                f"Marked for review: {len(self.marked_for_review)}"
            )
        )

        if confirm:
            self.submit_exam()

    def submit_exam(self):
        self.save_current_answer()
        self.exam_submitted = True

        correct = 0
        incorrect = 0
        unanswered = 0
        detailed_results = []

        for i, q in enumerate(self.exam_questions):
            correct_answer = sorted(q["answer"])
            user_answer = sorted(self.user_answers.get(i, []))

            if not user_answer:
                status = "unanswered"
                unanswered += 1
            elif user_answer == correct_answer:
                status = "correct"
                correct += 1
            else:
                status = "incorrect"
                incorrect += 1

            detailed_results.append({
                "question_number": i + 1,
                "question_id": q.get("id"),
                "question": q["question"],
                "status": status,
                "user_answer_indexes": user_answer,
                "correct_answer_indexes": correct_answer,
                "user_answer_text": [q["options"][x] for x in user_answer],
                "correct_answer_text": [q["options"][x] for x in correct_answer],
                "explanation": q.get("explanation", "")
            })

        total = len(self.exam_questions)
        score_percent = round((correct / total) * 100, 2) if total else 0

        result = {
            "exam": "CCNA 200-301 Simulator",
            "submitted_at": datetime.now().isoformat(timespec="seconds"),
            "total_questions": total,
            "correct": correct,
            "incorrect": incorrect,
            "unanswered": unanswered,
            "score_percent": score_percent,
            "duration_seconds_used": int(time.time() - self.start_time),
            "results": detailed_results
        }

        result_file = self.save_results(result)

        self.show_results_screen(
            total=total,
            correct=correct,
            incorrect=incorrect,
            unanswered=unanswered,
            score_percent=score_percent,
            result_file=result_file
        )

    def save_results(self, result):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ccna_exam_result_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)

        return filename

    def show_results_screen(self, total, correct, incorrect, unanswered, score_percent, result_file):
        self.clear_window()

        title = tk.Label(
            self.root,
            text="Exam Results",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=30)

        result_text = (
            f"Total questions: {total}\n"
            f"Correct: {correct}\n"
            f"Incorrect: {incorrect}\n"
            f"Unanswered: {unanswered}\n"
            f"Score: {score_percent}%\n\n"
            f"Detailed result file saved as:\n{result_file}"
        )

        label = tk.Label(
            self.root,
            text=result_text,
            font=("Arial", 15),
            justify="left"
        )
        label.pack(pady=20)

        review_button = tk.Button(
            self.root,
            text="Review Answers",
            font=("Arial", 13),
            width=20,
            command=self.show_answer_review
        )
        review_button.pack(pady=10)

        restart_button = tk.Button(
            self.root,
            text="Restart Exam",
            font=("Arial", 13),
            width=20,
            command=self.build_start_screen
        )
        restart_button.pack(pady=10)

        exit_button = tk.Button(
            self.root,
            text="Exit",
            font=("Arial", 13),
            width=20,
            command=self.root.quit
        )
        exit_button.pack(pady=10)

    def show_answer_review(self):
        window = tk.Toplevel(self.root)
        window.title("Answer Review")
        window.geometry("1000x700")

        text = tk.Text(window, wrap="word", font=("Arial", 11))
        text.pack(fill="both", expand=True, padx=10, pady=10)

        for i, q in enumerate(self.exam_questions):
            user_answer = sorted(self.user_answers.get(i, []))
            correct_answer = sorted(q["answer"])

            if not user_answer:
                status = "UNANSWERED"
            elif user_answer == correct_answer:
                status = "CORRECT"
            else:
                status = "INCORRECT"

            text.insert(tk.END, f"Question {i + 1}: {status}\n")
            text.insert(tk.END, f"{q['question']}\n\n")

            for index, option in enumerate(q["options"]):
                marker = chr(65 + index)
                text.insert(tk.END, f"{marker}. {option}\n")

            user_text = ", ".join(chr(65 + x) for x in user_answer) if user_answer else "None"
            correct_text = ", ".join(chr(65 + x) for x in correct_answer)

            text.insert(tk.END, f"\nYour answer: {user_text}\n")
            text.insert(tk.END, f"Correct answer: {correct_text}\n")

            explanation = q.get("explanation")
            if explanation:
                text.insert(tk.END, f"Explanation: {explanation}\n")

            text.insert(tk.END, "\n" + "-" * 100 + "\n\n")

        text.config(state="disabled")


def main():
    root = tk.Tk()
    CCNAExamSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
