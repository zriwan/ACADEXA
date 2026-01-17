// src/VoiceConsolePage.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api/client";

type SpeechRecognitionType = any;

type Me = {
  id: number;
  name: string;
  email: string;
  role: "admin" | "student" | "teacher" | "hod";
  student_id?: number | null;
  teacher_id?: number | null;
};

type HistoryItem = {
  id: string;
  text: string;
  at: string;
  response?: any;
  error?: string | null;
};

function makeId() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

const VoiceConsolePage: React.FC = () => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  // auth/me
  const [me, setMe] = useState<Me | null>(null);

  // voice states
  const [listening, setListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [responseJson, setResponseJson] = useState<any | null>(null);

  // history
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const recognitionRef = useRef<SpeechRecognitionType | null>(null);

  const [showRaw, setShowRaw] = useState(false);

  // Detect SpeechRecognition support (Chrome/Edge)
  const SpeechRecognitionCtor = useMemo(() => {
    const w: any = window;
    return w.SpeechRecognition || w.webkitSpeechRecognition || null;
  }, []);

  // load me
  useEffect(() => {
    async function loadMe() {
      try {
        const res = await api.get("/auth/me");
        setMe(res.data);
      } catch {
        setMe(null);
      }
    }
    loadMe();
  }, []);

  useEffect(() => {
    if (!SpeechRecognitionCtor) {
      setVoiceSupported(false);
      return;
    }

    const rec = new SpeechRecognitionCtor();
    rec.continuous = false; // single utterance
    rec.interimResults = true;
    rec.lang = "en-US"; // change if you want (e.g. "ur-PK")

    rec.onstart = () => {
      setListening(true);
      setError(null);
    };

    rec.onend = () => {
      setListening(false);
    };

    rec.onerror = (e: any) => {
      setListening(false);

      if (e?.error === "not-allowed" || e?.error === "service-not-allowed") {
        setError(
          "Microphone permission denied. Allow mic permission in browser site settings, then reload."
        );
      } else if (e?.error === "no-speech") {
        setError("No speech detected. Try again and speak clearly.");
      } else {
        setError(`Speech recognition error: ${e?.error || "unknown"}`);
      }
    };

    rec.onresult = (event: any) => {
      let transcript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        const chunk = res[0]?.transcript || "";
        transcript += chunk;

        if (res.isFinal) {
          finalTranscript += chunk;
        }
      }

      const merged = (finalTranscript || transcript).trim();
      if (merged) {
        setText(merged);
      }
    };

    recognitionRef.current = rec;

    return () => {
      try {
        rec.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    };
  }, [SpeechRecognitionCtor]);

  const startListening = () => {
    setError(null);

    if (!voiceSupported || !recognitionRef.current) {
      setError(
        "Speech recognition is not supported in this browser. Use Chrome/Edge, or type the command."
      );
      return;
    }

    try {
      recognitionRef.current.start();
    } catch {
      setError("Could not start microphone. Please try again.");
    }
  };

  const stopListening = () => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // ignore
    }
  };

  const pushHistory = (item: HistoryItem) => {
    setHistory((prev) => {
      const next = [item, ...prev];
      return next.slice(0, 10);
    });
  };

  const updateHistory = (id: string, patch: Partial<HistoryItem>) => {
    setHistory((prev) =>
      prev.map((h) => (h.id === id ? { ...h, ...patch } : h))
    );
  };

  const sendCommand = async (overrideText?: string) => {
    const command = (overrideText ?? text).trim();
    if (!command) return;

    const historyId = makeId();
    pushHistory({
      id: historyId,
      text: command,
      at: new Date().toLocaleString(),
    });

    try {
      setLoading(true);
      setError(null);
      setResponseJson(null);

      const res = await api.post("/voice/command", { text: command });

      setResponseJson(res.data);
      updateHistory(historyId, { response: res.data, error: null });

      setText("");
    } catch (err: any) {
      console.error(err);

      let msg = "Unknown error";
      if (err.response) {
        const status = err.response.status;
        const data = err.response.data;

        if (status === 401) {
          msg = "Not authenticated. Please login first.";
        } else {
          msg =
            `Error ${status}: ` +
            (typeof data === "string" ? data : JSON.stringify(data));
        }
      } else if (err.request) {
        msg = "No response from server. Is backend running on 127.0.0.1:8000?";
      } else {
        msg = "Unexpected error: " + err.message;
      }

      setError(msg);
      updateHistory(historyId, { error: msg });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    await sendCommand();
  };

  const handleClear = () => {
    setText("");
    setError(null);
    setResponseJson(null);
  };

  // ------- UI helper: render structured table from results -------
  const renderResultsTable = () => {
    if (!responseJson) return null;

    const results = responseJson.results;
    const type = responseJson.results_type;

    if (!results || !Array.isArray(results) || results.length === 0) {
      return null;
    }

    if (type === "students") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Department</th>
              <th>GPA</th>
            </tr>
          </thead>
          <tbody>
            {results.map((s: any) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.name}</td>
                <td>{s.department}</td>
                <td>{s.gpa}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    if (type === "courses") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Code</th>
              <th>Title</th>
              <th>Credit hours</th>
            </tr>
          </thead>
          <tbody>
            {results.map((c: any) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.code}</td>
                <td>{c.title}</td>
                <td>{c.credit_hours}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    if (type === "teachers") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Department</th>
              <th>Email</th>
              <th>Expertise</th>
            </tr>
          </thead>
          <tbody>
            {results.map((t: any) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.name}</td>
                <td>{t.department}</td>
                <td>{t.email}</td>
                <td>{t.expertise}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    if (type === "enrollments") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Student</th>
              <th>Course</th>
              <th>Semester</th>
              <th>Status</th>
              <th>Grade</th>
            </tr>
          </thead>
          <tbody>
            {results.map((en: any) => (
              <tr key={en.id ?? en.enrollment_id}>
                <td>{en.id ?? en.enrollment_id}</td>
                <td>
                  {en.student_name
                    ? `${en.student_name} (#${en.student_id})`
                    : `#${en.student_id}`}
                </td>
                <td>
                  {en.course_code
                    ? `${en.course_code} — ${en.course_title}`
                    : `#${en.course_id}`}
                </td>
                <td>{en.semester ?? "-"}</td>
                <td>{en.status ?? "-"}</td>
                <td>{en.grade ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    return (
      <pre
        style={{
          background: "#0b1120",
          color: "#e5e7eb",
          padding: "0.75rem",
          borderRadius: 8,
          fontSize: "0.8rem",
          overflowX: "auto",
        }}
      >
        {JSON.stringify(results, null, 2)}
      </pre>
    );
  };

  const renderResultsSection = () => {
    if (!responseJson) return null;

    const results = responseJson.results;
    const intent = responseJson.parsed?.intent || "unknown";

    if (!results || !Array.isArray(results) || results.length === 0) {
      if (intent !== "unknown") {
        return (
          <p className="mt-4 text-sm text-gray-500">
            No records found for this command.
          </p>
        );
      }
      return null;
    }

    return <div className="mt-4">{renderResultsTable()}</div>;
  };

  // role-based quick commands
  const quickCommands = useMemo(() => {
    const role = me?.role;

    if (role === "student") {
      return [
        "show my gpa",
        "which courses am I enrolled in",
        "my enrollments",
        "list courses",
      ];
    }

    if (role === "teacher") {
      return [
        "which courses am I teaching",
        "show my enrollments",
        "list courses",
        "list students",
      ];
    }

    // admin / hod fallback
    return [
      "list students",
      "list teachers",
      "list courses",
      "list enrollments for student 1",
    ];
  }, [me?.role]);

  return (
    <div>
      <h1 className="page-title">Command</h1>
      <p className="page-subtitle">
        Type or speak a command. The system will parse intent and return matching
        results.
      </p>

      {/* Quick commands */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">
            Quick Commands {me ? `(${me.role})` : ""}
          </h2>
        </div>
        <div
          className="card-body"
          style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
        >
          {quickCommands.map((cmd) => (
            <button
              key={cmd}
              className="btn btn-secondary"
              disabled={loading}
              onClick={() => sendCommand(cmd)}
              type="button"
            >
              {cmd}
            </button>
          ))}
        </div>
      </section>

      {/* Command input card */}
      <section className="card">
        <div
          className="card-header"
          style={{
            display: "flex",
            gap: "0.5rem",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 className="card-title">Command Console</h2>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClear}
              disabled={loading}
            >
              Clear
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={listening ? stopListening : startListening}
              disabled={loading || !voiceSupported}
              title={!voiceSupported ? "Use Chrome/Edge for mic" : ""}
            >
              {listening ? "Stop Mic" : "Use Mic"}
            </button>

            <button
              type="button"
              className="btn btn-primary"
              onClick={() => sendCommand()}
              disabled={loading || listening || !text.trim()}
            >
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>

        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>Command text</label>
              <input
                placeholder='e.g. "list students in course cs101"'
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
          </form>

          {!voiceSupported && (
            <div className="alert alert-error">
              Speech recognition is not supported in this browser. Use
              Chrome/Edge, or type the command.
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}
        </div>
      </section>

      {/* History card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">History (last 10)</h2>
        </div>
        <div className="card-body">
          {history.length === 0 && <p>No history yet.</p>}
          {history.length > 0 && (
            <div style={{ display: "grid", gap: 8 }}>
              {history.map((h) => (
                <div
                  key={h.id}
                  style={{
                    border: "1px solid #eee",
                    borderRadius: 8,
                    padding: 10,
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 8,
                    alignItems: "center",
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {h.text}
                    </div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{h.at}</div>
                    {h.error && (
                      <div style={{ fontSize: 12, color: "crimson" }}>
                        {h.error}
                      </div>
                    )}
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="btn btn-secondary"
                      type="button"
                      disabled={loading}
                      onClick={() => sendCommand(h.text)}
                    >
                      Run
                    </button>
                    <button
                      className="btn btn-secondary"
                      type="button"
                      disabled={loading || !h.response}
                      onClick={() => setResponseJson(h.response)}
                      title={!h.response ? "No response stored" : ""}
                    >
                      View
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Response card */}
      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Response</h2>
        </div>

        <div className="card-body">
          {!responseJson && !loading && <p>No command run yet.</p>}
          {loading && <p>Waiting for response...</p>}

          {responseJson && !loading && (
            <>
              {responseJson.info && (
                <div style={{ marginBottom: "0.75rem" }}>
                  <p>
                    <strong>Info:</strong> {responseJson.info}
                  </p>
                </div>
              )}

              <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                Intent:{" "}
                <strong>{responseJson.parsed?.intent || "unknown"}</strong>
              </p>

              {renderResultsSection()}

              <div style={{ marginTop: "1rem" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowRaw((v) => !v)}
                >
                  {showRaw ? "Hide Raw JSON" : "Show Raw JSON"}
                </button>

                {showRaw && (
                  <pre
                    style={{
                      marginTop: "0.5rem",
                      background: "#0b1120",
                      color: "#e5e7eb",
                      padding: "0.75rem",
                      borderRadius: 8,
                      fontSize: "0.8rem",
                      overflowX: "auto",
                      maxHeight: 300,
                    }}
                  >
                    {JSON.stringify(responseJson, null, 2)}
                  </pre>
                )}
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
};

export default VoiceConsolePage;
