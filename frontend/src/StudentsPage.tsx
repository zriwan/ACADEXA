// src/StudentsPage.tsx

import React, { useEffect, useState } from "react";
import { api, setAuthToken } from "./api/client";
import { Student, StudentCreatePayload, TokenResponse } from "./types";

const TOKEN_KEY = "acadexa_token";
const EMAIL_KEY = "acadexa_email";

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

  // ---- Helpers ----
  const restoreSession = () => {
    const token = localStorage.getItem(TOKEN_KEY);
    const savedEmail = localStorage.getItem(EMAIL_KEY);

    if (token) {
      setAuthToken(token);
      if (savedEmail) setLoggedInAs(savedEmail);
      return true;
    }
    return false;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
    setAuthToken(null);
    setLoggedInAs(null);
    setEmail("");
    setPassword("");
  };

  // ---- Auth ----
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setAuthError(null);

      // ✅ Backend expects x-www-form-urlencoded with keys: username, password
      const body = new URLSearchParams();
      body.append("username", email); // email goes into "username"
      body.append("password", password);

      const res = await api.post<TokenResponse>("/auth/login", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const token = res.data.access_token;

      // Persist session
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(EMAIL_KEY, email);

      setAuthToken(token);
      setLoggedInAs(email);

      // Optional: load students after login
      await fetchStudents(true);
    } catch (err: any) {
      console.error(err);
      setAuthError("Login failed. Check email/password.");
      logout();
    }
  };

  // ---- Data ----
  const fetchStudents = async (silent: boolean = false) => {
    try {
      if (!silent) {
        setLoading(true);
      }
      setError(null);

      const res = await api.get<Student[]>("/students/");
      setStudents(res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load students (are you logged in?)");
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    // Try to restore session first
    const hasSession = restoreSession();

    // Fetch students (will succeed only if token exists)
    if (hasSession) {
      fetchStudents();
    }
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

   if (!localStorage.getItem("acadexa_token")) {
  setError("Please login first.");
  return;
}


    try {
      setError(null);

      if (editingId === null) {
        await api.post<Student>("/students/", form);
      } else {
        await api.put<Student>(`/students/${editingId}`, form);
      }

      resetForm();
      await fetchStudents(true);
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
   if (!localStorage.getItem("acadexa_token")) {
  setError("Please login first.");
  return;
}


    if (!window.confirm("Are you sure you want to delete this student?")) {
      return;
    }

    try {
      setError(null);
      await api.delete(`/students/${id}`);
      await fetchStudents(true);
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <p>
                Logged in as <strong>{loggedInAs}</strong>
              </p>
              <button type="button" className="btn btn-secondary" onClick={logout}>
                Logout
              </button>
            </div>
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
          {!loggedInAs && (
            <div className="alert alert-error" style={{ marginBottom: "1rem" }}>
              Please login to create, update, or delete students.
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Name</label>
              <input name="name" value={form.name} onChange={handleChange} required />
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

            <button type="submit" className="btn btn-primary" disabled={!loggedInAs}>
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
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between" }}>
            <h2 className="card-title">All Students</h2>
            <button
              className="btn btn-secondary"
              onClick={() => fetchStudents()}
              disabled={!loggedInAs}
              title={!loggedInAs ? "Login required" : "Refresh list"}
            >
              Refresh
            </button>
          </div>

          <div className="card-body">
            {loading && <p>Loading...</p>}

            {!loading && !loggedInAs && (
              <p>Please login to view student records.</p>
            )}

            {!loading && loggedInAs && students.length === 0 && <p>No students found.</p>}

            {!loading && loggedInAs && students.length > 0 && (
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
                          <button className="btn btn-secondary" onClick={() => startEdit(s)}>
                            Edit
                          </button>
                          <button className="btn btn-danger" onClick={() => handleDelete(s.id)}>
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
