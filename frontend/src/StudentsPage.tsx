// src/StudentsPage.tsx
import React, { useEffect, useState } from "react";
import { api } from "./api/client";
import { Student, StudentCreatePayload } from "./types";

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
  });

  const [editingId, setEditingId] = useState<number | null>(null);

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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === "gpa" ? Number(value) : value,
    }));
  };

  const resetForm = () => {
    setForm({ name: "", department: "", gpa: 0, email: "", password: "" }); // ✅ clear email/password too
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setError(null);

      if (editingId === null) {
        // ✅ CREATE: send full form (includes email/password)
        await api.post<Student>("/students/", form);
      } else {
        // ✅ UPDATE: DO NOT send email/password
        const { name, department, gpa } = form;
        await api.put<Student>(`/students/${editingId}`, { name, department, gpa });
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
            </div>

            <div className="form-row">
              <label>Department</label>
              <input
                name="department"
                value={form.department}
                onChange={handleChange}
                required
              />
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
                  <input
                    name="password"
                    type="password"
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
