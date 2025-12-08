// src/EnrollmentsPage.tsx

import React, { useEffect, useState } from "react";
import { api } from "./api/client";
import {
  Enrollment,
  EnrollmentPayload,
  Student,
  Course,
} from "./types";

const EnrollmentsPage: React.FC = () => {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<EnrollmentPayload>({
    student_id: 0,
    course_id: 0,
    semester: "",
    status: "enrolled",
    grade: null,
  });

  const [editingId, setEditingId] = useState<number | null>(null);

  const getStudentName = (id: number) => {
    const s = students.find((s) => s.id === id);
    return s ? `${s.name} (#${s.id})` : `Student #${id}`;
  };

  const getCourseLabel = (id: number) => {
    const c = courses.find((c) => c.id === id);
    return c ? `${c.code} — ${c.title}` : `Course #${id}`;
  };

  const fetchStudents = async () => {
    try {
      const res = await api.get<Student[]>("/students/");
      setStudents(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCourses = async () => {
    try {
      const res = await api.get<Course[]>("/courses/");
      setCourses(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchEnrollments = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<Enrollment[]>("/enrollments/");
      setEnrollments(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to load enrollments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
    fetchCourses();
    fetchEnrollments();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    setForm((prev) => {
      if (name === "student_id" || name === "course_id") {
        return {
          ...prev,
          [name]: value ? Number(value) : 0,
        };
      }
      if (name === "grade") {
        return {
          ...prev,
          grade: value === "" ? null : Number(value),
        };
      }
      return {
        ...prev,
        [name]: value,
      };
    });
  };

  const resetForm = () => {
    setForm({
      student_id: 0,
      course_id: 0,
      semester: "",
      status: "enrolled",
      grade: null,
    });
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.student_id || !form.course_id) {
      setError("Please select both student and course");
      return;
    }

    try {
      setError(null);

      const body: any = {
        student_id: form.student_id,
        course_id: form.course_id,
      };
      if (form.semester && form.semester.trim()) {
        body.semester = form.semester.trim();
      }
      if (form.status && form.status.trim()) {
        body.status = form.status.trim();
      }
      if (form.grade !== null && !Number.isNaN(form.grade)) {
        body.grade = form.grade;
      }

      if (editingId === null) {
        await api.post<Enrollment>("/enrollments/", body);
      } else {
        await api.patch<Enrollment>(`/enrollments/${editingId}`, body);
      }

      resetForm();
      await fetchEnrollments();
    } catch (err: any) {
      console.error(err);
      setError(
        editingId === null
          ? "Failed to create enrollment (maybe duplicate or not authenticated?)"
          : "Failed to update enrollment (maybe not authenticated?)"
      );
    }
  };

  const startEdit = (en: Enrollment) => {
    setForm({
      student_id: en.student_id,
      course_id: en.course_id,
      semester: en.semester ?? "",
      status: en.status ?? "enrolled",
      grade: en.grade ? Number(en.grade) : null,
    });
    setEditingId(en.id);
    setError(null);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to drop this enrollment?")) {
      return;
    }
    try {
      setError(null);
      await api.delete(`/enrollments/${id}`);
      await fetchEnrollments();
    } catch (err: any) {
      console.error(err);
      setError("Failed to delete enrollment (maybe not authenticated?)");
    }
  };

  return (
    <div>
      <h1 className="page-title">Enrollments</h1>
      <p className="page-subtitle">
        Enroll students into courses, manage status and grades.
      </p>

      {/* Form card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">
            {editingId === null
              ? "Enroll student in course"
              : `Edit Enrollment #${editingId}`}
          </h2>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Student</label>
              <select
                name="student_id"
                value={form.student_id || ""}
                onChange={handleChange}
                required
              >
                <option value="">-- select student --</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} (#{s.id}, {s.department})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <label>Course</label>
              <select
                name="course_id"
                value={form.course_id || ""}
                onChange={handleChange}
                required
              >
                <option value="">-- select course --</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} — {c.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <label>Semester</label>
              <input
                name="semester"
                placeholder="e.g. Fall 2025"
                value={form.semester ?? ""}
                onChange={handleChange}
              />
            </div>

            <div className="form-row">
              <label>Status</label>
              <select
                name="status"
                value={form.status ?? "enrolled"}
                onChange={handleChange}
              >
                <option value="enrolled">Enrolled</option>
                <option value="completed">Completed</option>
                <option value="dropped">Dropped</option>
              </select>
            </div>

            <div className="form-row">
              <label>Grade (GPA)</label>
              <input
                name="grade"
                type="number"
                step="0.01"
                min={0}
                max={4}
                value={form.grade ?? ""}
                onChange={handleChange}
              />
            </div>

            <button type="submit" className="btn btn-primary">
              {editingId === null ? "Create Enrollment" : "Update Enrollment"}
            </button>
            {editingId !== null && (
              <button
                type="button"
                className="btn btn-secondary"
                style={{ marginLeft: "0.5rem" }}
                onClick={resetForm}
              >
                Cancel
              </button>
            )}
          </form>

          {error && <div className="alert alert-error">{error}</div>}
        </div>
      </section>

      {/* List card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">All Enrollments</h2>
        </div>
        <div className="card-body">
          {loading && <p>Loading...</p>}
          {!loading && enrollments.length === 0 && (
            <p>No enrollments found.</p>
          )}
          {!loading && enrollments.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Student</th>
                  <th>Course</th>
                  <th>Semester</th>
                  <th>Status</th>
                  <th>Grade</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {enrollments.map((en) => (
                  <tr key={en.id}>
                    <td>{en.id}</td>
                    <td>{getStudentName(en.student_id)}</td>
                    <td>{getCourseLabel(en.course_id)}</td>
                    <td>{en.semester ?? "-"}</td>
                    <td>{en.status ?? "-"}</td>
                    <td>{en.grade ?? "-"}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="btn btn-secondary"
                          onClick={() => startEdit(en)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleDelete(en.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
};

export default EnrollmentsPage;
