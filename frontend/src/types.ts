// src/types.ts

// ---- Students ----
export interface Student {
  id: number;
  name: string;
  department: string;
  gpa: string; // backend se "3.40" string aati hai
}

export interface StudentCreatePayload {
  name: string;
  department: string;
  gpa: number;

  // ✅ NEW (optional)
  email?: string;
  password?: string;
}

// ---- Auth ----
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ---- Teachers ----
export interface Teacher {
  id: number;
  name: string;
  department: string;
  email: string;
  expertise: string | null;
}

export interface TeacherPayload {
  name: string;
  department: string;
  email: string;
  expertise?: string | null;
}

// ---- Courses ----
export interface Course {
  id: number;
  title: string;
  code: string;
  credit_hours: number;
  teacher_id: number | null;
}

export interface CoursePayload {
  title: string;
  code: string;
  credit_hours: number;
  teacher_id?: number | null;
}

// ---- Enrollments ----
export interface Enrollment {
  id: number;
  student_id: number;
  course_id: number;
  semester: string | null;
  status: string | null; // "enrolled" | "dropped" | "completed" etc.
  grade: string | null;  // backend se Numeric string
}

export interface EnrollmentPayload {
  student_id: number;
  course_id: number;
  semester?: string;
  status?: string;
  grade?: number | null;
}


export type UserRole = "admin" | "student" | "teacher" | "hod" | "user";

export interface MeResponse {
  id: number;
  name: string;
  email: string;
  role: UserRole;
}
