# tests/test_nlp_processor.py
import pytest
from nlp.nlp_processor import parse_command

def test_create_student_with_roll():
    res = parse_command("Add student Ali Raza roll 125")
    assert res.intent == "create_student"
    assert res.slots["name"] == "ali raza"
    assert res.slots["roll"] == 125

def test_show_student_result():
    res = parse_command("Show marks of roll 77")
    assert res.intent == "show_student_result"
    assert res.slots["student_id"] == 77

def test_list_students_in_course():
    res = parse_command("display students in course cs101")
    assert res.intent == "list_students"
    assert res.slots["course"] == "cs101"

def test_count_teachers():
    res = parse_command("how many teachers")
    assert res.intent == "count_teachers"

def test_unknown():
    res = parse_command("open the door please")
    assert res.intent == "unknown"
