// src/StudentsPage.tsx

import React, { useEffect, useState } from "react";
import { api, setAuthToken } from "./api/client";
import { Student, StudentCreatePayload, TokenResponse } from "./types";

const StudentsPage: React.FC = () => {
  // Auth state
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [loggedInAs, setLoggedInAs] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Students state
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<StudentCreatePayload>({
    name: "",
    department: "",
    gpa: 0,
  });

  const [editingId, setEditingId] = useState<number | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setAuthError(null);

      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await api.post<TokenResponse>("/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const token = res.data.access_token;
      setAuthToken(token);
      setLoggedInAs(email);
    } catch (err: any) {
      console.error(err);
      setAuthError("Login failed. Check email/password.");
      setAuthToken(null);
      setLoggedInAs(null);
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
      setError("Failed to load students");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
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
    setForm({ name: "", department: "", gpa: 0 });
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);

      if (editingId === null) {
        await api.post<Student>("/students/", form);
      } else {
        await api.put<Student>(`/students/${editingId}`, form);
      }

      resetForm();
      await fetchStudents();
    } catch (err: any) {
      console.error(err);
      setError(
        editingId === null
          ? "Failed to create student (maybe not authenticated?)"
          : "Failed to update student (maybe not authenticated?)"
      );
    }
  };

  const startEdit = (s: Student) => {
    setForm({
      name: s.name,
      department: s.department,
      gpa: Number(s.gpa),
    });
    setEditingId(s.id);
    setError(null);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this student?")) {
      return;
    }
    try {
      setError(null);
      await api.delete(`/students/${id}`);
      await fetchStudents();
    } catch (err: any) {
      console.error(err);
      setError("Failed to delete student (maybe not authenticated?)");
    }
  };

  return (
    <div>
      <h1 className="page-title">Students</h1>
      <p className="page-subtitle">
        Manage student records, departments, and GPA from a single place.
      </p>

      {/* Login card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Login</h2>
        </div>
        <div className="card-body">
          {loggedInAs ? (
            <p>
              Logged in as <strong>{loggedInAs}</strong>
            </p>
          ) : (
            <form onSubmit={handleLogin}>
              <div className="form-row">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="admin@example.com"
                />
              </div>
              <div className="form-row">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                />
              </div>
              <button type="submit" className="btn btn-primary">
                Login
              </button>
            </form>
          )}
          {authError && <div className="alert alert-error">{authError}</div>}
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
          <div className="card-header">
            <h2 className="card-title">All Students</h2>
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
