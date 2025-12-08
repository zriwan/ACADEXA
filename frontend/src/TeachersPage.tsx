// src/TeachersPage.tsx

import React, { useEffect, useState } from "react";
import { api } from "./api/client";
import { Teacher, TeacherPayload } from "./types";

const TeachersPage: React.FC = () => {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<TeacherPayload>({
    name: "",
    department: "",
    email: "",
    expertise: "",
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
    });
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);

      if (editingId === null) {
        await api.post<Teacher>("/teachers/", form);
      } else {
        await api.put<Teacher>(`/teachers/${editingId}`, form);
      }

      resetForm();
      await fetchTeachers();
    } catch (err: any) {
      console.error(err);
      setError(
        editingId === null
          ? "Failed to create teacher (maybe not authenticated?)"
          : "Failed to update teacher (maybe not authenticated?)"
      );
    }
  };

  const startEdit = (t: Teacher) => {
    setForm({
      name: t.name,
      department: t.department,
      email: t.email,
      expertise: t.expertise ?? "",
    });
    setEditingId(t.id);
    setError(null);
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
      <p className="page-subtitle">
        Maintain teacher profiles, departments, and contact details.
      </p>

      {/* Form card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">
            {editingId === null ? "Add Teacher" : `Edit Teacher #${editingId}`}
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
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-row">
              <label>Expertise</label>
              <input
                name="expertise"
                value={form.expertise ?? ""}
                onChange={handleChange}
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
                        <button
                          className="btn btn-secondary"
                          onClick={() => startEdit(t)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleDelete(t.id)}
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

export default TeachersPage;
