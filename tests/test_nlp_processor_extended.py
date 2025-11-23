# tests/test_nlp_processor_extended.py
import pytest
from nlp.nlp_processor import parse_command, _normalize

# ---------- Normalization tests ----------
@pytest.mark.parametrize("raw,expected", [
    ("  SHOW   Result of Student  125  ", "show result of student 125"),
    ("Assign teacher Ahmed to course AI-101!!!", "assign teacher ahmed to course ai-101"),
    ("Create course Data-Mining", "create course data-mining"),
    ("DELETE student 007", "delete student 007"),
    ("List   students   in   course   cs101", "list students in course cs101"),
    ("Update student 33 name to Hamza, Khan", "update student 33 name to hamza khan"),
])
def test_normalize(raw, expected):
    assert _normalize(raw) == expected

# ---------- Intent: create_student ----------
@pytest.mark.parametrize("text,exp_name,exp_roll", [
    ("Add student Ali Raza roll 125", "ali raza", 125),
    ("create student hamza", "hamza", None),
    ("register student  muhammad usman  roll 5", "muhammad usman", 5),
])
def test_create_student(text, exp_name, exp_roll):
    res = parse_command(text)
    assert res.intent == "create_student"
    assert res.slots["name"] == exp_name
    assert res.slots.get("roll") == exp_roll

# ---------- Intent: delete_student ----------
@pytest.mark.parametrize("text,exp_id", [
    ("Delete student 7", 7),
    ("remove student 123", 123),
])
def test_delete_student(text, exp_id):
    res = parse_command(text)
    assert res.intent == "delete_student"
    assert res.slots["student_id"] == exp_id

# ---------- Intent: update_student_name ----------
def test_update_student_name():
    res = parse_command("Update student 33 name to Hamza Khan")
    assert res.intent == "update_student_name"
    assert res.slots == {"student_id": 33, "name": "hamza khan"}

# ---------- Intent: list_students ----------
@pytest.mark.parametrize("text,course", [
    ("list all students", None),
    ("show students in course cs101", "cs101"),
    ("display students in course ai-101", "ai-101"),
])
def test_list_students(text, course):
    res = parse_command(text)
    assert res.intent == "list_students"
    assert res.slots.get("course") == course

# ---------- Intent: show_student_result ----------
@pytest.mark.parametrize("text,exp_id", [
    ("Show result of student 125", 125),
    ("Get marks of roll 77", 77),
    ("display result student 9", 9),
])
def test_show_student_result(text, exp_id):
    res = parse_command(text)
    assert res.intent == "show_student_result"
    assert res.slots["student_id"] == exp_id

# ---------- Intent: create_course ----------
@pytest.mark.parametrize("text,exp_title", [
    ("add course Data Mining", "data mining"),
    ("create course ai-101", "ai-101"),
])
def test_create_course(text, exp_title):
    res = parse_command(text)
    assert res.intent == "create_course"
    assert res.slots["title"] == exp_title

# ---------- Intent: delete_course ----------
@pytest.mark.parametrize("text,code", [
    ("delete course cs-999", "cs-999"),
    ("remove course ai101", "ai101"),
])
def test_delete_course(text, code):
    res = parse_command(text)
    assert res.intent == "delete_course"
    assert res.slots["course_code"] == code

# ---------- Intent: count_teachers ----------
def test_count_teachers():
    res = parse_command("how many teachers")
    assert res.intent == "count_teachers"
    assert res.slots == {}

# ---------- Intent: assign_teacher_to_course ----------
def test_assign_teacher_to_course():
    res = parse_command("assign teacher Ahmed Ali to course CS-101")
    assert res.intent == "assign_teacher_to_course"
    assert res.slots["teacher"] == "ahmed ali"
    assert res.slots["course"] == "cs-101"

# ---------- Unknown / out-of-domain ----------
@pytest.mark.parametrize("text", [
    "open the door please",
    "tell me a joke",
    "play music",
])
def test_unknown(text):
    res = parse_command(text)
    assert res.intent == "unknown"
    assert res.slots == {}
