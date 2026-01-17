import React, { useEffect, useState } from "react";
import { api } from "./api/client";

export default function TeacherHome() {
  const [profile, setProfile] = useState<any>(null);
  const [courses, setCourses] = useState<any>(null);
  const [enrollments, setEnrollments] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [p, c, e] = await Promise.all([
          api.get("/teachers/me"),
          api.get("/teachers/me/courses"),
          api.get("/teachers/me/enrollments"),
        ]);
        setProfile(p.data);
        setCourses(c.data);
        setEnrollments(e.data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div style={{ padding: 16 }}>Loading teacher dashboard...</div>;

  return (
    <div style={{ padding: 16 }}>
      <h2>Teacher Dashboard</h2>

      <div style={{ marginTop: 12 }}>
        <h3>My Profile</h3>
        <pre>{JSON.stringify(profile, null, 2)}</pre>
      </div>

      <div style={{ marginTop: 12 }}>
        <h3>My Courses</h3>
        <pre>{JSON.stringify(courses, null, 2)}</pre>
      </div>

      <div style={{ marginTop: 12 }}>
        <h3>My Enrollments (Students in my Courses)</h3>
        <pre>{JSON.stringify(enrollments, null, 2)}</pre>
      </div>
    </div>
  );
}export {};

