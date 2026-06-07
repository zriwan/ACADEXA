// src/StudentsPage.tsx
import React, { useEffect, useState } from "react";
import { api } from "./api/client";
import { Student, StudentCreatePayload } from "./types";
import PasswordInput from "./PasswordInput";

const alphaOnlyRegex = /^[A-Za-z ]+$/;

const sanitizeAlphaInput = (value: string) => value.replace(/[^A-Za-z ]/g, "");

const StudentsPage: React.FC = () => {
  const [meEmail, setMeEmail] = useState<string | null>(null);

  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<StudentCreatePayload>({
    name: "",
    department: "",
    gpa: 0,
    email: "",
    password: "",
    current_semester: 1,
  });

  const [editingId, setEditingId] = useState<number | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validateAlphaRequired = (value: string, label: string) => {
    const trimmed = value.trim();
    if (!trimmed) return `${label} is required`;
    if (!alphaOnlyRegex.test(trimmed)) return `${label} must contain only alphabets and spaces`;
    return "";
  };

  const fetchMe = async () => {
    try {
      const res = await api.get("/auth/me");
      setMeEmail(res.data?.email ?? null);
    } catch {
      setMeEmail(null);
    }
  };

  const fetchStudents = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<Student[]>("/students/");
      setStudents(res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load students (are you logged in / allowed?)");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMe();
    fetchStudents();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;

    const alphaFields = ["name", "department"];
    const nextValue = alphaFields.includes(name) ? sanitizeAlphaInput(value) : value;

    setForm((prev) => ({
      ...prev,
      [name]: name === "gpa" || name === "current_semester" ? Number(nextValue) : nextValue,
    }));

    if (name === "name" || name === "department") {
      const label = name === "name" ? "Name" : "Department";
      const msg = validateAlphaRequired(nextValue, label);
      setFieldErrors((prev) => ({ ...prev, [name]: msg }));
    }
  };

  const resetForm = () => {
    setForm({ name: "", department: "", gpa: 0, email: "", password: "", current_semester: 1 }); // ✅ clear email/password too
    setEditingId(null);
    setFieldErrors({});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const nameError = validateAlphaRequired(form.name, "Name");
    const departmentError = validateAlphaRequired(form.department, "Department");

    const nextErrors = {
      name: nameError,
      department: departmentError,
    };
    setFieldErrors(nextErrors);

    if (nameError || departmentError) {
      setError("Please fix form errors before submitting.");
      return;
    }

    try {
      setError(null);

      if (editingId === null) {
        // ✅ CREATE: send full form (includes email/password)
        await api.post<Student>("/students/", form);
      } else {
        // ✅ UPDATE: DO NOT send email/password
        const { name, department, gpa, current_semester } = form;
        await api.put<Student>(`/students/${editingId}`, { name, department, gpa, current_semester });
      }

      resetForm();
      await fetchStudents();
    } catch (err: any) {
      console.error(err);
      setError(
        editingId === null
          ? "Failed to create student (maybe not allowed?)"
          : "Failed to update student (maybe not allowed?)"
      );
    }
  };

  const startEdit = (s: Student) => {
    setForm({
      name: s.name,
      department: s.department,
      gpa: Number(s.gpa),
      email: "", // ✅ keep empty in edit mode
      password: "", // ✅ keep empty in edit mode
      current_semester: s.current_semester || 1,
    });
    setEditingId(s.id);
    setError(null);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this student?")) return;

    try {
      setError(null);
      await api.delete(`/students/${id}`);
      await fetchStudents();
    } catch (err: any) {
      console.error(err);
      setError("Failed to delete student (maybe not allowed?)");
    }
  };

  return (
    <div>
      <h1 className="page-title">Students</h1>
      <p className="page-subtitle">
        Manage student records, departments, and GPA from a single place.
      </p>

      {/* Session */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Session</h2>
        </div>
        <div className="card-body">
          {meEmail ? (
            <p>
              Logged in as <strong>{meEmail}</strong>
            </p>
          ) : (
            <p>Not logged in (or session expired).</p>
          )}
        </div>
      </section>

      {/* Add / edit student */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">
            {editingId === null ? "Add Student" : `Edit Student #${editingId}`}
          </h2>
        </div>

        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Name</label>
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                required
              />
              {fieldErrors.name && (
                <div className="alert alert-error" style={{ marginTop: "0.5rem" }}>
                  {fieldErrors.name}
                </div>
              )}
            </div>

            <div className="form-row">
              <label>Department</label>
              <input
                name="department"
                value={form.department}
                onChange={handleChange}
                required
              />
              {fieldErrors.department && (
                <div className="alert alert-error" style={{ marginTop: "0.5rem" }}>
                  {fieldErrors.department}
                </div>
              )}
            </div>

            <div className="form-row">
              <label>GPA</label>
              <input
                name="gpa"
                type="number"
                step="0.01"
                min="0"
                max="4"
                value={form.gpa}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-row">
              <label>Current Semester (1-8)</label>
              <select
                name="current_semester"
                value={form.current_semester || 1}
                onChange={handleChange}
                required
              >
                <option value="1">Semester 1</option>
                <option value="2">Semester 2</option>
                <option value="3">Semester 3</option>
                <option value="4">Semester 4</option>
                <option value="5">Semester 5</option>
                <option value="6">Semester 6</option>
                <option value="7">Semester 7</option>
                <option value="8">Semester 8</option>
              </select>
            </div>

            {/* ✅ Show email/password only when creating */}
            {editingId === null && (
              <>
                <div className="form-row">
                  <label>Student Email</label>
                  <input
                    name="email"
                    value={form.email || ""}
                    onChange={handleChange}
                    placeholder="student@example.com"
                    required
                  />
                </div>

                <div className="form-row">
                  <label>Student Password</label>
                  <PasswordInput
                    name="password"
                    value={form.password || ""}
                    onChange={handleChange}
                    placeholder="min 6 chars"
                    required
                  />
                </div>
              </>
            )}

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

      {/* List students */}
      <section>
        <div className="card">
          <div
            className="card-header"
            style={{ display: "flex", justifyContent: "space-between" }}
          >
            <h2 className="card-title">All Students</h2>
            <button className="btn btn-secondary" onClick={fetchStudents}>
              Refresh
            </button>
          </div>

          <div className="card-body">
            {loading && <p>Loading...</p>}

            {!loading && students.length === 0 && <p>No students found.</p>}

            {!loading && students.length > 0 && (
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Department</th>
                    <th>GPA</th>
                    <th>Semester</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {students.map((s) => (
                    <tr key={s.id}>
                      <td>{s.id}</td>
                      <td>{s.name}</td>
                      <td>{s.department}</td>
                      <td>{s.gpa}</td>
                      <td>{s.current_semester || "-"}</td>
                      <td>
                        <div className="table-actions">
                          <button
                            className="btn btn-secondary"
                            onClick={() => startEdit(s)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-danger"
                            onClick={() => handleDelete(s.id)}
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
        </div>
      </section>
    </div>
  );
};

export default StudentsPage;
