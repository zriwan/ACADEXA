// src/VoiceConsolePage.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api/client";

type SpeechRecognitionType = any;
type MicPermission = "unknown" | "granted" | "denied" | "prompt" | "unsupported";

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

type MicCaptureState = {
  stream: MediaStream | null;
  recorder: MediaRecorder | null;
  chunks: Blob[];
  timerId: number | null;
};

function makeId() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

const VoiceConsolePage: React.FC = () => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [micBusy, setMicBusy] = useState(false);
  const [transcribingMic, setTranscribingMic] = useState(false);

  // auth/me
  const [me, setMe] = useState<Me | null>(null);

  // voice states
  const [listening, setListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const [micPermission, setMicPermission] = useState<MicPermission>("unknown");

  const [error, setError] = useState<string | null>(null);
  const [responseJson, setResponseJson] = useState<any | null>(null);

  // history
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const recognitionRef = useRef<SpeechRecognitionType | null>(null);
  const shouldKeepListeningRef = useRef(false);
  const noSpeechRetriesRef = useRef(0);
  const autoSendTimerRef = useRef<number | null>(null);
  const finalizedTranscriptRef = useRef("");
  const loadingRef = useRef(false);
  const captureRef = useRef<MicCaptureState>({
    stream: null,
    recorder: null,
    chunks: [],
    timerId: null,
  });

  const [showRaw, setShowRaw] = useState(false);

  const isSecureContextOk = window.isSecureContext;

  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);

  // Detect SpeechRecognition support (Chrome/Edge)
  const SpeechRecognitionCtor = useMemo(() => {
    const w: any = window;
    return w.SpeechRecognition || w.webkitSpeechRecognition || null;
  }, []);

  const micSupported = useMemo(() => {
    return typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia;
  }, []);

  useEffect(() => {
    setVoiceSupported(!!SpeechRecognitionCtor || micSupported);
  }, [SpeechRecognitionCtor, micSupported]);

  const clearAutoSendTimer = () => {
    if (autoSendTimerRef.current) {
      window.clearTimeout(autoSendTimerRef.current);
      autoSendTimerRef.current = null;
    }
  };

  const toBase64 = (bytes: Uint8Array) => {
    let binary = "";
    const chunkSize = 0x8000;
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.subarray(i, i + chunkSize);
      for (let j = 0; j < chunk.length; j += 1) {
        binary += String.fromCharCode(chunk[j]);
      }
    }
    return window.btoa(binary);
  };

  const floatTo16BitPCM = (float32: Float32Array) => {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i += 1) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16;
  };

  const decodeAudioToPCM = async (blob: Blob) => {
    const arrayBuffer = await blob.arrayBuffer();
    const audioContext = new AudioContext();
    const decoded = await audioContext.decodeAudioData(arrayBuffer.slice(0));

    const targetSampleRate = 16000;
    const duration = decoded.duration;
    const frameCount = Math.ceil(duration * targetSampleRate);
    const offline = new OfflineAudioContext(1, frameCount, targetSampleRate);
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start(0);

    const rendered = await offline.startRendering();
    const mono = rendered.getChannelData(0);
    const pcm = floatTo16BitPCM(mono);
    const base64 = toBase64(new Uint8Array(pcm.buffer));

    try {
      await audioContext.close();
    } catch {
      // ignore
    }

    return { pcmBase64: base64, sampleRate: targetSampleRate };
  };

  const stopMicCapture = async (): Promise<MicCaptureState> => {
    const capture = captureRef.current;
    const finalized: MicCaptureState = {
      stream: capture.stream,
      recorder: capture.recorder,
      chunks: capture.chunks.slice(),
      timerId: null,
    };

    if (capture.timerId) {
      window.clearTimeout(capture.timerId);
      capture.timerId = null;
    }

    if (capture.recorder && capture.recorder.state !== "inactive") {
      await new Promise<void>((resolve) => {
        let settled = false;

        const finalize = () => {
          if (settled) return;
          settled = true;
          cleanup();
          resolve();
        };

        const onData = (event: BlobEvent) => {
          if (event.data && event.data.size > 0) {
            finalized.chunks.push(event.data);
          }
        };

        const onStop = () => finalize();

        const cleanup = () => {
          capture.recorder?.removeEventListener("dataavailable", onData);
          capture.recorder?.removeEventListener("stop", onStop);
        };

        capture.recorder?.addEventListener("dataavailable", onData);
        capture.recorder?.addEventListener("stop", onStop);

        try {
          if (capture.recorder?.state === "recording") {
            capture.recorder.requestData();
          }
          capture.recorder?.stop();
        } catch {
          finalize();
          return;
        }

        window.setTimeout(() => finalize(), 1000);
      });
    }

    if (capture.stream) {
      capture.stream.getTracks().forEach((track) => track.stop());
    }

    captureRef.current = {
      stream: null,
      recorder: null,
      chunks: [],
      timerId: null,
    };

    return finalized;
  };

  const transcribeCapturedAudio = async (capture: MicCaptureState) => {
    const chunks = capture.chunks;

    if (!chunks.length) {
      setError("No audio captured. Please try again.");
      setMicBusy(false);
      setTranscribingMic(false);
      return;
    }

    try {
      setTranscribingMic(true);
      const blob = new Blob(chunks, { type: chunks[0].type || "audio/webm" });
      const { pcmBase64, sampleRate } = await decodeAudioToPCM(blob);

      const res = await api.post("/voice/transcribe_pcm", {
        pcm_b64: pcmBase64,
        sample_rate: sampleRate,
      });

      const transcript = (res.data?.text || "").trim();
      if (!transcript) {
        setError("No speech detected. Please try again.");
      } else {
        setText(transcript);
        setError(null);
      }
    } catch (e: any) {
      const msg =
        e?.response?.data?.detail ||
        e?.message ||
        "Could not transcribe microphone audio.";
      setError(msg);
    } finally {
      setTranscribingMic(false);
      setMicBusy(false);
      shouldKeepListeningRef.current = false;
    }
  };

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
    let permissionStatus: PermissionStatus | null = null;

    async function loadMicPermission() {
      const permissionsApiAvailable =
        typeof navigator !== "undefined" &&
        !!navigator.permissions &&
        !!navigator.permissions.query;

      if (!permissionsApiAvailable) {
        setMicPermission("unknown");
        return;
      }

      try {
        permissionStatus = await navigator.permissions.query({
          name: "microphone" as PermissionName,
        });

        const state = permissionStatus.state;
        if (state === "granted" || state === "denied" || state === "prompt") {
          setMicPermission(state);
        } else {
          setMicPermission("unknown");
        }

        permissionStatus.onchange = () => {
          const next = permissionStatus?.state;
          if (next === "granted" || next === "denied" || next === "prompt") {
            setMicPermission(next);
          } else {
            setMicPermission("unknown");
          }
        };
      } catch {
        setMicPermission("unknown");
      }
    }

    loadMicPermission();

    return () => {
      if (permissionStatus) {
        permissionStatus.onchange = null;
      }
      shouldKeepListeningRef.current = false;
      noSpeechRetriesRef.current = 0;
      clearAutoSendTimer();
      void stopMicCapture();
      try {
        recognitionRef.current?.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    };
  }, [SpeechRecognitionCtor]);

  const scheduleAutoSendFromTranscript = () => {
    clearAutoSendTimer();
    autoSendTimerRef.current = window.setTimeout(async () => {
      const command = finalizedTranscriptRef.current.trim();
      if (!command) return;

      if (loadingRef.current) {
        scheduleAutoSendFromTranscript();
        return;
      }

      finalizedTranscriptRef.current = "";
      setText(command);
      await sendCommand(command);
    }, 1200);
  };

  const startListening = async () => {
    setError(null);

    if (!micSupported) {
      setError("Microphone capture is not supported in this browser.");
      return;
    }

    if (!isSecureContextOk) {
      setError(
        "Microphone requires a secure context. Open the app on localhost/https and try again."
      );
      return;
    }

    if (micBusy || listening) {
      return;
    }

    finalizedTranscriptRef.current = "";
    clearAutoSendTimer();

    if (SpeechRecognitionCtor) {
      try {
        const recognition = new SpeechRecognitionCtor();
        recognition.lang = "en-US";
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
          setListening(true);
          setMicBusy(true);
          setMicPermission("granted");
        };

        recognition.onresult = (event: any) => {
          let finalChunk = "";
          let interimChunk = "";

          for (let i = event.resultIndex; i < event.results.length; i += 1) {
            const result = event.results[i];
            const piece = result?.[0]?.transcript?.trim() || "";
            if (!piece) continue;

            if (result.isFinal) {
              finalChunk = `${finalChunk} ${piece}`.trim();
            } else {
              interimChunk = `${interimChunk} ${piece}`.trim();
            }
          }

          if (finalChunk) {
            finalizedTranscriptRef.current = `${finalizedTranscriptRef.current} ${finalChunk}`.trim();
            scheduleAutoSendFromTranscript();
          }

          const liveText = `${finalizedTranscriptRef.current} ${interimChunk}`.trim();
          setText(liveText);
          setError(null);
        };

        recognition.onerror = (event: any) => {
          const err = event?.error || "";
          if (err === "not-allowed" || err === "service-not-allowed") {
            setMicPermission("denied");
            setError("Microphone permission denied. Allow mic access and try again.");
            shouldKeepListeningRef.current = false;
            setListening(false);
            setMicBusy(false);
            clearAutoSendTimer();
            return;
          }

          if (err === "no-speech") {
            return;
          }

          setError("Mic could not capture speech clearly. Please speak again.");
        };

        recognition.onend = () => {
          if (shouldKeepListeningRef.current) {
            try {
              recognition.start();
              return;
            } catch {
              // ignore and fall through to idle state
            }
          }

          setListening(false);
          setMicBusy(false);
          clearAutoSendTimer();
        };

        recognitionRef.current = recognition;
        shouldKeepListeningRef.current = true;
        recognition.start();
        return;
      } catch {
        setError("Could not start live mic recognition. Falling back to capture mode.");
      }
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Browser does not support microphone access. Use latest Chrome or Edge.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicPermission("granted");
      setListening(true);
      setMicBusy(true);
      shouldKeepListeningRef.current = true;
      noSpeechRetriesRef.current = 0;

      const mimeCandidates = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
      ];
      const mimeType =
        mimeCandidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) ||
        "";

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      captureRef.current = {
        stream,
        recorder,
        chunks: [],
        timerId: null,
      };

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          captureRef.current.chunks.push(event.data);
        }
      };

      recorder.start(250);

      captureRef.current.timerId = window.setTimeout(() => {
        if (shouldKeepListeningRef.current) {
          void stopListening();
        }
      }, 5000);
    } catch (e: any) {
      const errName = e?.name || "";
      if (errName === "NotAllowedError" || errName === "SecurityError") {
        setMicPermission("denied");
        setError(
          "Microphone permission denied. Allow mic access for this site and try again."
        );
        return;
      }
      if (errName === "NotFoundError" || errName === "DevicesNotFoundError") {
        setError("No microphone found. Connect a mic and try again.");
        return;
      }
      setError("Could not start microphone. Please try again.");
    }
  };

  const stopListening = async () => {
    shouldKeepListeningRef.current = false;
    noSpeechRetriesRef.current = 0;
    setListening(false);
    clearAutoSendTimer();

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
      setMicBusy(false);
      return;
    }

    const capture = captureRef.current;

    if (!micBusy && !capture.stream) {
      return;
    }

    const snapshot = await stopMicCapture();
    await transcribeCapturedAudio(snapshot);
  };

  const pushHistory = (item: HistoryItem) => {
    setHistory((prev) => {
      const next = [item].concat(prev);
      return next.slice(0, 10);
    });
  };

  const updateHistory = (id: string, patch: Partial<HistoryItem>) => {
    setHistory((prev) =>
      prev.map((h) => {
        if (h.id === id) {
          return Object.assign({}, h, patch);
        }
        return h;
      })
    );
  };

  const sendCommand = async (overrideText?: string) => {
    if (loadingRef.current) return;

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
      if (err.code === "ECONNABORTED" || /timeout/i.test(err.message || "")) {
        msg =
          "Request timed out. Ollama may be loading the model. Try again in a few seconds.";
      } else if (err.response) {
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

    if (type === "gpa") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>Student ID</th>
              <th>GPA</th>
            </tr>
          </thead>
          <tbody>
            {results.map((g: any) => (
              <tr key={g.student_id ?? g.id}>
                <td>{g.student_id ?? g.id}</td>
                <td>{g.gpa ?? "-"}</td>
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

    if (type === "attendance_summary") {
      return (
        <table className="table">
          <thead>
            <tr>
              <th>Course</th>
              <th>Total</th>
              <th>Present</th>
              <th>Absent</th>
              <th>Late</th>
              <th>Percent</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r: any) => (
              <tr key={r.course_id ?? r.course_code}>
                <td>
                  {r.course_code ? `${r.course_code} — ${r.course_title}` : r.course_title}
                </td>
                <td>{r.total_sessions}</td>
                <td>{r.present}</td>
                <td>{r.absent}</td>
                <td>{r.late}</td>
                <td>{r.percent_present}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    return (
      <pre className="json-view">
        {JSON.stringify(results, null, 2)}
      </pre>
    );
  };

  const renderObjectResults = () => {
    if (!responseJson) return null;
    const results = responseJson.results;
    const type = responseJson.results_type;

    if (!results || typeof results !== "object") return null;

    if (type === "attendance_course_detail" && Array.isArray(results.rows)) {
      return (
        <div className="result-panel">
          <div className="result-meta">
            <div>
              <strong>Course:</strong>{" "}
              {results.course_code
                ? `${results.course_code} — ${results.course_title}`
                : results.course_title || "—"}
            </div>
            <div>
              <strong>Student:</strong> #{results.student_id}
            </div>
          </div>

          <table className="table" style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Session ID</th>
                <th>Status</th>
                <th>Start</th>
                <th>End</th>
              </tr>
            </thead>
            <tbody>
              {results.rows.map((r: any) => (
                <tr key={`${r.session_id}-${r.lecture_date}`}>
                  <td>{r.lecture_date}</td>
                  <td>{r.session_id}</td>
                  <td>{r.status}</td>
                  <td>{r.start_time ?? "-"}</td>
                  <td>{r.end_time ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return (
      <div className="result-panel">
        <pre className="json-view">{JSON.stringify(results, null, 2)}</pre>
      </div>
    );
  };

  const renderResultsSection = () => {
    if (!responseJson) return null;

    const results = responseJson.results;
    const intent = responseJson.parsed?.intent || "unknown";

    if (Array.isArray(results)) {
      if (results.length === 0) {
        if (intent !== "unknown") {
          return <p className="mt-4 text-sm text-gray-500">No records found for this command.</p>;
        }
        return null;
      }

      return <div className="mt-4">{renderResultsTable()}</div>;
    }

    if (results && typeof results === "object") {
      return <div className="mt-4">{renderObjectResults()}</div>;
    }

    if (intent !== "unknown") {
      return <p className="mt-4 text-sm text-gray-500">No records found for this command.</p>;
    }

    return null;
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
    <div className="voice-portal">
      {/* Hero / Overview */}
      <section className="card voice-hero">
        <div className="voice-hero-main">
          <h2 className="voice-hero-title">Voice Assistant</h2>
          <p className="voice-hero-subtitle">
            Ask for attendance, courses, results, and department insights using
            natural language.
          </p>
          <div className="voice-hero-meta">
            <span
              className={`chip ${voiceSupported ? "chip-success" : "chip-danger"}`}
            >
              {voiceSupported ? "Mic Ready" : "Mic Unavailable"}
            </span>
            {voiceSupported && (
              <span
                className={`chip ${
                  micPermission === "granted"
                    ? "chip-success"
                    : micPermission === "denied"
                    ? "chip-danger"
                    : "chip-muted"
                }`}
              >
                Mic Permission: {micPermission}
              </span>
            )}
            <span className={`chip ${listening ? "chip-info" : "chip-muted"}`}>
              {listening ? "Listening" : "Idle"}
            </span>
            {me && <span className="chip chip-muted">Role: {me.role}</span>}
          </div>
        </div>
        <div className="voice-hero-stats">
          <div className="stat-card">
            <div className="stat-label">Commands today</div>
            <div className="stat-value">{history.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Last activity</div>
            <div className="stat-value">
              {history[0]?.at ? history[0].at.split(",")[0] : "—"}
            </div>
          </div>
        </div>
      </section>

      <div className="voice-grid">
        {/* Left Column */}
        <div className="voice-col">
          {/* Quick commands */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">
                Quick Actions {me ? `(${me.role})` : ""}
              </h2>
            </div>
            <div className="card-body">
              <div className="quick-actions">
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
            </div>
          </section>

          {/* Command input card */}
          <section className="card">
            <div className="card-header voice-card-header">
              <h2 className="card-title">Command Center</h2>

              <div className="command-actions">
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
                  <label>Command</label>
                  <textarea
                    rows={3}
                    placeholder='e.g. "show my attendance" or "list courses"'
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
        </div>

        {/* Right Column */}
        <div className="voice-col">
          {/* History card */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">Recent Activity</h2>
            </div>
            <div className="card-body">
              {history.length === 0 && (
                <div className="empty-state">No activity yet.</div>
              )}
              {history.length > 0 && (
                <div className="history-list">
                  {history.map((h) => (
                    <div key={h.id} className="history-item">
                      <div className="history-meta">
                        <div className="history-text" title={h.text}>
                          {h.text}
                        </div>
                        <div className="history-time">{h.at}</div>
                        {h.error && (
                          <div className="history-error">{h.error}</div>
                        )}
                      </div>

                      <div className="history-actions">
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
              <h2 className="card-title">Assistant Response</h2>
            </div>

            <div className="card-body">
              {!responseJson && !loading && (
                <div className="empty-state">No response yet.</div>
              )}
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
      </div>
    </div>
  );
};

export default VoiceConsolePage;
