import React, { useEffect, useState } from "react";
import { api } from "./api/client";

type Me = {
  id: number;
  name: string;
  email: string;
  role: "admin" | "student" | "teacher" | "hod";
  student_id?: number | null;
  teacher_id?: number | null;
};

const HODHome: React.FC = () => {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get("/auth/me");
        setMe(res.data);
      } catch {
        setMe(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>;

  return (
    <div style={{ padding: 16 }}>
      <h1 className="page-title">HOD Dashboard</h1>
      <p className="page-subtitle">
        Basic department overview. Use tabs for Students, Teachers, Courses,
        Enrollments and Analytics.
      </p>

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Current User</h2>
        </div>
        <div className="card-body">
          {!me ? (
            <p>Not logged in.</p>
          ) : (
            <ul style={{ lineHeight: 1.9 }}>
              <li>
                <strong>Name:</strong> {me.name}
              </li>
              <li>
                <strong>Email:</strong> {me.email}
              </li>
              <li>
                <strong>Role:</strong> {me.role}
              </li>
            </ul>
          )}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Quick Notes</h2>
        </div>
        <div className="card-body">
          <ul style={{ lineHeight: 1.9 }}>
            <li>Use Analytics for department performance.</li>
            <li>Use Courses/Enrollments for oversight.</li>
            <li>Use Voice Console for quick queries.</li>
          </ul>
        </div>
      </section>
    </div>
  );
};

export default HODHome;
