// src/CoursesPage.tsx

import React, { useEffect, useState } from "react";
import { api } from "./api/client";
import { Course, CoursePayload, Teacher } from "./types";

const CoursesPage: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<CoursePayload>({
    title: "",
    code: "",
    credit_hours: 3,
    teacher_id: null,
  });

  const [editingId, setEditingId] = useState<number | null>(null);

  const fetchCourses = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<Course[]>("/courses/");
      setCourses(res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load courses");
    } finally {
      setLoading(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      const res = await api.get<Teacher[]>("/teachers/");
      setTeachers(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchCourses();
    fetchTeachers();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    setForm((prev) => {
      if (name === "credit_hours") {
        return { ...prev, credit_hours: Number(value) };
      }
      if (name === "teacher_id") {
        return { ...prev, teacher_id: value ? Number(value) : null };
      }
      return { ...prev, [name]: value };
    });
  };

  const resetForm = () => {
    setForm({
      title: "",
      code: "",
      credit_hours: 3,
      teacher_id: null,
    });
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);

      if (editingId === null) {
        await api.post<Course>("/courses/", form);
      } else {
        await api.put<Course>(`/courses/${editingId}`, form);
      }

      resetForm();
      await fetchCourses();
    } catch (err: any) {
      console.error(err);
      setError(
        editingId === null
          ? "Failed to create course (maybe not authenticated?)"
          : "Failed to update course (maybe not authenticated?)"
      );
    }
  };

  const startEdit = (c: Course) => {
    setForm({
      title: c.title,
      code: c.code,
      credit_hours: c.credit_hours,
      teacher_id: c.teacher_id ?? null,
    });
    setEditingId(c.id);
    setError(null);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this course?")) {
      return;
    }
    try {
      setError(null);
      await api.delete(`/courses/${id}`);
      await fetchCourses();
    } catch (err: any) {
      console.error(err);
      setError("Failed to delete course (maybe it has enrollments?)");
    }
  };

  const getTeacherName = (teacher_id: number | null) => {
    if (!teacher_id) return "-";
    const t = teachers.find((t) => t.id === teacher_id);
    return t ? t.name : `#${teacher_id}`;
  };

  return (
    <div>
      <h1 className="page-title">Courses</h1>
      <p className="page-subtitle">
        Create courses, assign teachers, and manage credit hours.
      </p>

      {/* Form card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">
            {editingId === null ? "Add Course" : `Edit Course #${editingId}`}
          </h2>
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Title</label>
              <input
                name="title"
                value={form.title}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-row">
              <label>Code</label>
              <input
                name="code"
                value={form.code}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-row">
              <label>Credit hours</label>
              <input
                type="number"
                name="credit_hours"
                min={1}
                max={6}
                value={form.credit_hours}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-row">
              <label>Teacher</label>
              <select
                name="teacher_id"
                value={form.teacher_id ?? ""}
                onChange={handleChange}
              >
                <option value="">-- Unassigned --</option>
                {teachers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.department})
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" className="btn btn-primary">
              {editingId === null ? "Create" : "Update"}
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
          <h2 className="card-title">All Courses</h2>
        </div>
        <div className="card-body">
          {loading && <p>Loading...</p>}
          {!loading && courses.length === 0 && <p>No courses found.</p>}
          {!loading && courses.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Code</th>
                  <th>Credit hours</th>
                  <th>Teacher</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {courses.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td>{c.title}</td>
                    <td>{c.code}</td>
                    <td>{c.credit_hours}</td>
                    <td>{getTeacherName(c.teacher_id)}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="btn btn-secondary"
                          onClick={() => startEdit(c)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleDelete(c.id)}
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

export default CoursesPage;
