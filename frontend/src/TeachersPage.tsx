// src/TeachersPage.tsx
import React, { useEffect, useState } from "react";
import { api } from "./api/client";
import { Teacher } from "./types";

type TeacherForm = {
  name: string;
  department: string;
  email: string;
  expertise?: string;
  password?: string; // ✅ NEW
};

type CreateAccountRes = {
  teacher_id: number;
  user_id: number;
  email: string;
  temp_password: string;
};

const TeachersPage: React.FC = () => {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [createdInfo, setCreatedInfo] = useState<CreateAccountRes | null>(null);

  const [form, setForm] = useState<TeacherForm>({
    name: "",
    department: "",
    email: "",
    expertise: "",
    password: "",
  });

  const [editingId, setEditingId] = useState<number | null>(null);

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<Teacher[]>("/teachers/");
      setTeachers(res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load teachers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeachers();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setForm({
      name: "",
      department: "",
      email: "",
      expertise: "",
      password: "",
    });
    setEditingId(null);
    setCreatedInfo(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      setCreatedInfo(null);

      if (editingId === null) {
        // ✅ CREATE TEACHER ACCOUNT (User + Teacher)
        const payload = {
          name: form.name,
          department: form.department,
          email: form.email,
          expertise: form.expertise || null,
          password: form.password || null, // admin-set OR null
        };

        const res = await api.post<CreateAccountRes>("/teachers/create-account", payload);
        setCreatedInfo(res.data);
      } else {
        // ✅ EDIT TEACHER PROFILE ONLY
        const payload = {
          name: form.name,
          department: form.department,
          email: form.email,
          expertise: form.expertise || null,
        };
        await api.put<Teacher>(`/teachers/${editingId}`, payload);
      }

      // refresh list
      await fetchTeachers();

      // keep createdInfo visible; only reset inputs (not createdInfo)
      if (editingId !== null) resetForm();
      else {
        setForm((p) => ({ ...p, password: "" }));
      }
    } catch (err: any) {
      console.error(err);
      const detail = err?.response?.data?.detail || "Request failed";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
  };

  const startEdit = (t: Teacher) => {
    setForm({
      name: t.name,
      department: t.department,
      email: t.email,
      expertise: t.expertise ?? "",
      password: "", // not used in edit
    });
    setEditingId(t.id);
    setError(null);
    setCreatedInfo(null);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this teacher?")) {
      return;
    }
    try {
      setError(null);
      await api.delete(`/teachers/${id}`);
      await fetchTeachers();
    } catch (err: any) {
      console.error(err);
      setError("Failed to delete teacher (maybe teacher has courses?)");
    }
  };

  return (
    <div>
      <h1 className="page-title">Teachers</h1>
      <p className="page-subtitle">Create teacher login + manage teacher profiles.</p>

      {/* Form card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">
            {editingId === null ? "Add Teacher Account" : `Edit Teacher #${editingId}`}
          </h2>
        </div>

        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Name</label>
              <input name="name" value={form.name} onChange={handleChange} required />
            </div>

            <div className="form-row">
              <label>Department</label>
              <input name="department" value={form.department} onChange={handleChange} required />
            </div>

            <div className="form-row">
              <label>Email</label>
              <input type="email" name="email" value={form.email} onChange={handleChange} required />
            </div>

            <div className="form-row">
              <label>Expertise</label>
              <input name="expertise" value={form.expertise ?? ""} onChange={handleChange} />
            </div>

            {/* ✅ NEW: password only on CREATE */}
            {editingId === null && (
              <div className="form-row">
                <label>Teacher Password</label>
                <input
                  type="text"
                  name="password"
                  value={form.password ?? ""}
                  onChange={handleChange}
                  placeholder="Set password (or leave empty to auto-generate)"
                />
              </div>
            )}

            <button type="submit" className="btn btn-primary">
              {editingId === null ? "Create Teacher Account" : "Update"}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              style={{ marginLeft: "0.5rem" }}
              onClick={resetForm}
            >
              {editingId === null ? "Clear" : "Cancel"}
            </button>
          </form>

          {createdInfo && (
            <div className="alert" style={{ marginTop: 12 }}>
              ✅ Teacher created: <b>{createdInfo.email}</b> <br />
              Teacher ID: <b>{createdInfo.teacher_id}</b>, User ID: <b>{createdInfo.user_id}</b> <br />
              Password: <b>{createdInfo.temp_password}</b> <br />
              <span style={{ color: "#666" }}>
                (Copy this password and share with teacher for login)
              </span>
            </div>
          )}

          {error && <div className="alert alert-error" style={{ marginTop: 12 }}>{error}</div>}
        </div>
      </section>

      {/* List card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">All Teachers</h2>
        </div>
        <div className="card-body">
          {loading && <p>Loading...</p>}
          {!loading && teachers.length === 0 && <p>No teachers found.</p>}
          {!loading && teachers.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Department</th>
                  <th>Email</th>
                  <th>Expertise</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {teachers.map((t) => (
                  <tr key={t.id}>
                    <td>{t.id}</td>
                    <td>{t.name}</td>
                    <td>{t.department}</td>
                    <td>{t.email}</td>
                    <td>{t.expertise}</td>
                    <td>
                      <div className="table-actions">
                        <button className="btn btn-secondary" onClick={() => startEdit(t)}>
                          Edit
                        </button>
                        <button className="btn btn-danger" onClick={() => handleDelete(t.id)}>
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

export default TeachersPage;
