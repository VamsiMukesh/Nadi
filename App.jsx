import React, { useState, useEffect, useCallback } from "react";

// ─── MOCK DATA GENERATORS ────────────────────────────────────────────────────
const generateHeartRate = (base = 72) => Math.floor(base + (Math.random() - 0.5) * 20);
const generateSpO2 = () => parseFloat((97 + Math.random() * 3).toFixed(1));
const generateBloodPressure = () => ({
  systolic: Math.floor(115 + (Math.random() - 0.5) * 30),
  diastolic: Math.floor(75 + (Math.random() - 0.5) * 18),
});
const generateTemperature = () => parseFloat((36.4 + Math.random() * 1.2).toFixed(1));
const generateSteps = () => Math.floor(Math.random() * 12000);
const generateSleepHours = () => parseFloat((5.5 + Math.random() * 3).toFixed(1));
const generateStressLevel = () => Math.floor(20 + Math.random() * 60);
const generateHRV = () => Math.floor(40 + Math.random() * 40);
const generateCalories = () => Math.floor(1800 + Math.random() * 1200);
const generateHydration = () => Math.floor(4 + Math.random() * 5);

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const generateWeeklyHR = () => WEEKDAYS.map(day => ({ day, value: generateHeartRate(70) }));
const generateWeeklySleep = () => WEEKDAYS.map(day => ({ day, value: generateSleepHours() }));
const generateWeeklySteps = () => WEEKDAYS.map(day => ({ day, value: generateSteps() }));
const generateMonthlyBP = () =>
  Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    systolic: Math.floor(115 + (Math.random() - 0.5) * 30),
    diastolic: Math.floor(75 + (Math.random() - 0.5) * 18),
  }));

// ─── AI INSIGHTS ENGINE ──────────────────────────────────────────────────────
function generateAIInsights(vitals) {
  const insights = [];
  if (vitals.heartRate > 90)
    insights.push({ type: "warning", icon: "⚡", title: "Elevated Heart Rate", message: "Your heart rate is above the normal resting range. Consider relaxation techniques or light stretching." });
  else if (vitals.heartRate < 55)
    insights.push({ type: "warning", icon: "💤", title: "Low Heart Rate", message: "Your resting heart rate is below average. Ensure you are well-hydrated and getting adequate nutrition." });
  else
    insights.push({ type: "good", icon: "💚", title: "Heart Rate Normal", message: "Your heart rate is within healthy resting range. Keep up the great work!" });

  if (vitals.spO2 < 95)
    insights.push({ type: "alert", icon: "🚨", title: "Low Oxygen Saturation", message: "SpO2 below 95% — consider breathing exercises. If persistent, consult a healthcare professional immediately." });
  else
    insights.push({ type: "good", icon: "🫁", title: "Oxygen Levels Healthy", message: "Your blood oxygen saturation is within the optimal range (95–100%)." });

  if (vitals.temperature > 37.8)
    insights.push({ type: "warning", icon: "🌡️", title: "Elevated Temperature", message: "Your body temperature is above normal. Stay hydrated and monitor for other symptoms." });

  if (vitals.sleepHours < 6)
    insights.push({ type: "warning", icon: "🌙", title: "Sleep Deficit Detected", message: "You got less than 6 hours of sleep. Aim for 7–9 hours for optimal recovery and cognition." });
  else if (vitals.sleepHours >= 7.5)
    insights.push({ type: "good", icon: "✨", title: "Excellent Sleep", message: "Great sleep duration! Consistent sleep supports immune health and mental clarity." });

  if (vitals.stressLevel > 65)
    insights.push({ type: "warning", icon: "🧠", title: "High Stress Detected", message: "Your HRV and stress indicators suggest elevated stress. Try a 5-minute deep breathing session." });
  else if (vitals.stressLevel < 35)
    insights.push({ type: "good", icon: "😌", title: "Low Stress Level", message: "Your stress indicators are healthy. Maintain your current routine and mindfulness practices." });

  if (vitals.steps < 5000)
    insights.push({ type: "warning", icon: "🚶", title: "Low Activity Today", message: "You've taken fewer than 5,000 steps. A short 20-minute walk can boost your energy and mood." });
  else if (vitals.steps >= 10000)
    insights.push({ type: "good", icon: "🏆", title: "Activity Goal Achieved!", message: "Incredible! You've hit 10,000 steps today. Your cardiovascular fitness is improving." });

  if (vitals.hydration < 6)
    insights.push({ type: "warning", icon: "💧", title: "Hydration Reminder", message: "You're below your daily hydration target. Drink a glass of water to stay on track." });

  return insights.slice(0, 4);
}

// ─── SPARKLINE SVG COMPONENT ─────────────────────────────────────────────────
function Sparkline({ data, color = "#4ade80", width = 200, height = 50 }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 8) - 4;
    return `${x},${y}`;
  }).join(" ");

  const areaPoints = `0,${height} ${points} ${width},${height}`;

  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <defs>
        <linearGradient id={`grad-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#grad-${color.replace("#", "")})`} />
      <polyline points={points} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={(data.length - 1) / (data.length - 1) * width} cy={height - ((data[data.length - 1] - min) / range) * (height - 8) - 4} r="3.5" fill={color} />
    </svg>
  );
}

// ─── BAR CHART COMPONENT ─────────────────────────────────────────────────────
function BarChart({ data, valueKey, color, maxVal, unit = "", barWidth = 28 }) {
  const max = maxVal || Math.max(...data.map(d => d[valueKey]));
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "6px", height: "100px", padding: "0 4px" }}>
      {data.map((item, i) => {
        const pct = (item[valueKey] / max) * 100;
        return (
          <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
            <span style={{ fontSize: "9px", color: "#94a3b8", fontFamily: "'Inter', sans-serif" }}>{item[valueKey]}{unit}</span>
            <div style={{ width: "100%", maxWidth: barWidth, height: "72px", background: "#1e293b", borderRadius: "6px", display: "flex", alignItems: "flex-end", overflow: "hidden" }}>
              <div style={{ width: "100%", height: `${pct}%`, background: `linear-gradient(to top, ${color}, ${color}aa)`, borderRadius: "6px 6px 0 0", transition: "height 0.6s cubic-bezier(0.4,0,0.2,1)" }} />
            </div>
            <span style={{ fontSize: "9px", color: "#64748b", fontFamily: "'Inter', sans-serif" }}>{item.day}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── BP LINE CHART ───────────────────────────────────────────────────────────
function BPChart({ data }) {
  const W = 600, H = 120, pad = { t: 10, r: 10, b: 24, l: 30 };
  const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;
  const minV = 50, maxV = 160;
  const scaleY = v => pad.t + cH - ((v - minV) / (maxV - minV)) * cH;
  const scaleX = i => pad.l + (i / (data.length - 1)) * cW;

  const sysPath = data.map((d, i) => `${i === 0 ? "M" : "L"}${scaleX(i)},${scaleY(d.systolic)}`).join("");
  const diaPath = data.map((d, i) => `${i === 0 ? "M" : "L"}${scaleX(i)},${scaleY(d.diastolic)}`).join("");

  const labelIndices = [0, 7, 14, 21, 29];
  return (
    <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ display: "block" }}>
      <defs>
        <linearGradient id="sysGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f87171" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#f87171" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="diaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#60a5fa" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#60a5fa" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[60, 80, 100, 120, 140].map(v => (
        <g key={v}>
          <line x1={pad.l} y1={scaleY(v)} x2={W - pad.r} y2={scaleY(v)} stroke="#1e293b" strokeWidth="1" />
          <text x={pad.l - 6} y={scaleY(v) + 3} textAnchor="end" fill="#64748b" fontSize="9">{v}</text>
        </g>
      ))}
      <path d={`${sysPath} L${scaleX(data.length - 1)},${H - pad.b} L${scaleX(0)},${H - pad.b} Z`} fill="url(#sysGrad)" />
      <path d={sysPath} fill="none" stroke="#f87171" strokeWidth="2" strokeLinecap="round" />
      <path d={`${diaPath} L${scaleX(data.length - 1)},${H - pad.b} L${scaleX(0)},${H - pad.b} Z`} fill="url(#diaGrad)" />
      <path d={diaPath} fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinecap="round" />
      {labelIndices.map(i => (
        <text key={i} x={scaleX(i)} y={H - 6} textAnchor="middle" fill="#64748b" fontSize="9">{data[i].day}</text>
      ))}
    </svg>
  );
}

// ─── RADIAL GAUGE ────────────────────────────────────────────────────────────
function RadialGauge({ value, max, color, label, unit }) {
  const pct = Math.min(value / max, 1);
  const angle = pct * 270 - 135;
  const r = 38, cx = 50, cy = 54;
  const toRad = deg => (deg * Math.PI) / 180;
  const startAngle = -135, endAngle = startAngle + pct * 270;
  const x1 = cx + r * Math.cos(toRad(startAngle));
  const y1 = cy + r * Math.sin(toRad(startAngle));
  const x2 = cx + r * Math.cos(toRad(endAngle));
  const y2 = cy + r * Math.sin(toRad(endAngle));
  const largeArc = pct > 0.5 ? 1 : 0;

  return (
    <div style={{ textAlign: "center" }}>
      <svg width="100" height="100" viewBox="0 0 100 100">
        <path d={`M ${cx + r * Math.cos(toRad(-135))},${cy + r * Math.sin(toRad(-135))} A ${r} ${r} 0 1 1 ${cx + r * Math.cos(toRad(135))},${cy + r * Math.sin(toRad(135))}`} fill="none" stroke="#1e293b" strokeWidth="8" strokeLinecap="round" />
        {pct > 0.01 && (
          <path d={`M ${x1},${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2},${y2}`} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" />
        )}
        <text x={cx} y={cy - 2} textAnchor="middle" fill="#f1f5f9" fontSize="14" fontWeight="700" fontFamily="'Inter', sans-serif">{value}</text>
        <text x={cx} y={cy + 12} textAnchor="middle" fill="#64748b" fontSize="8">{unit}</text>
      </svg>
      <div style={{ fontSize: "11px", color: "#64748b", marginTop: "-4px" }}>{label}</div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [vitals, setVitals] = useState({
    heartRate: 72, spO2: 98.2, temperature: 36.6, steps: 7842,
    sleepHours: 7.2, stressLevel: 38, hrv: 62, calories: 2150,
    hydration: 6,
    bp: { systolic: 120, diastolic: 78 },
  });
  const [weeklyHR, setWeeklyHR] = useState(generateWeeklyHR());
  const [weeklySleep, setWeeklySleep] = useState(generateWeeklySleep());
  const [weeklySteps, setWeeklySteps] = useState(generateWeeklySteps());
  const [monthlyBP, setMonthlyBP] = useState(generateMonthlyBP());
  const [notifications, setNotifications] = useState([
    { id: 1, text: "Time to drink water!", time: "2 min ago", read: false },
    { id: 2, text: "Great job hitting 7k steps!", time: "1 hr ago", read: false },
    { id: 3, text: "Sleep score report ready", time: "3 hr ago", read: true },
  ]);
  const [showNotif, setShowNotif] = useState(false);
  const [devices, setDevices] = useState([
    { id: 1, name: "Smart Watch Pro", status: "connected", battery: 82, lastSync: "Just now", icon: "⌚" },
    { id: 2, name: "Blood Pressure Cuff", status: "connected", battery: 67, lastSync: "5 min ago", icon: "💪" },
    { id: 3, name: "Pulse Oximeter", status: "connected", battery: 91, lastSync: "Just now", icon: "🩺" },
    { id: 4, name: "Smart Thermometer", status: "idle", battery: 45, lastSync: "2 hr ago", icon: "🌡️" },
    { id: 5, name: "Sleep Tracker Band", status: "connected", battery: 73, lastSync: "8 hr ago", icon: "🌙" },
  ]);
  const [goals, setGoals] = useState([
    { id: 1, label: "Daily Steps", current: 7842, target: 10000, unit: "steps", color: "#4ade80", icon: "🚶" },
    { id: 2, label: "Water Intake", current: 6, target: 8, unit: "glasses", color: "#60a5fa", icon: "💧" },
    { id: 3, label: "Sleep Duration", current: 7.2, target: 8, unit: "hrs", color: "#a78bfa", icon: "🌙" },
    { id: 4, label: "Calories Burned", current: 2150, target: 2500, unit: "kcal", color: "#fb923c", icon: "🔥" },
    { id: 5, label: "Meditation", current: 12, target: 20, unit: "min", color: "#34d399", icon: "🧘" },
  ]);
  const [aiInsights, setAiInsights] = useState(() => generateAIInsights({
    heartRate: 72, spO2: 98.2, temperature: 36.6, steps: 7842,
    sleepHours: 7.2, stressLevel: 38, hydration: 6,
  }));

  // Simulate live IoT data
  useEffect(() => {
    const interval = setInterval(() => {
      setVitals(prev => {
        const next = {
          ...prev,
          heartRate: generateHeartRate(prev.heartRate),
          spO2: generateSpO2(),
          hrv: Math.floor(prev.hrv + (Math.random() - 0.5) * 6),
        };
        setAiInsights(generateAIInsights({ ...next, sleepHours: prev.sleepHours, stressLevel: prev.stressLevel, hydration: prev.hydration }));
        return next;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  // ── STYLES ──
  const s = {
    app: { minHeight: "100vh", background: "#0f172a", color: "#f1f5f9", fontFamily: "'Inter', -apple-system, sans-serif", display: "flex", flexDirection: "column" },
    header: { background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)", borderBottom: "1px solid #1e293b", padding: "14px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100 },
    logo: { display: "flex", alignItems: "center", gap: "10px" },
    logoIcon: { width: "36px", height: "36px", background: "linear-gradient(135deg, #4ade80, #22d3ee)", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", boxShadow: "0 0 16px rgba(74,222,128,0.3)" },
    logoText: { fontSize: "18px", fontWeight: "700", letterSpacing: "-0.5px" },
    logoSub: { fontSize: "9px", color: "#64748b", letterSpacing: "1.5px", textTransform: "uppercase" },
    headerRight: { display: "flex", alignItems: "center", gap: "16px" },
    notifBtn: { position: "relative", background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "20px", padding: "4px" },
    notifBadge: { position: "absolute", top: "-2px", right: "-4px", background: "#f87171", color: "#fff", fontSize: "9px", width: "16px", height: "16px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "700" },
    avatar: { width: "34px", height: "34px", borderRadius: "50%", background: "linear-gradient(135deg, #4ade80, #22d3ee)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px", fontWeight: "700", color: "#0f172a" },
    nav: { display: "flex", gap: "4px", padding: "10px 24px", background: "#0f172a", borderBottom: "1px solid #1e293b", overflowX: "auto" },
    navBtn: (active) => ({ background: active ? "linear-gradient(135deg, #4ade80 0%, #22d3ee 100%)" : "transparent", color: active ? "#0f172a" : "#64748b", border: "none", padding: "8px 18px", borderRadius: "20px", cursor: "pointer", fontSize: "13px", fontWeight: active ? "700" : "500", whiteSpace: "nowrap", transition: "all 0.2s", boxShadow: active ? "0 2px 12px rgba(74,222,128,0.3)" : "none" }),
    content: { flex: 1, padding: "20px 24px", maxWidth: "1200px", margin: "0 auto", width: "100%", boxSizing: "border-box" },
    grid2: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginBottom: "20px" },
    grid3: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px", marginBottom: "20px" },
    card: { background: "#1e293b", borderRadius: "16px", padding: "18px", border: "1px solid #293548", position: "relative", overflow: "hidden" },
    cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" },
    cardLabel: { fontSize: "12px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.8px", fontWeight: "600" },
    cardValue: { fontSize: "32px", fontWeight: "800", letterSpacing: "-1px", color: "#f1f5f9" },
    cardUnit: { fontSize: "14px", fontWeight: "400", color: "#64748b", marginLeft: "4px" },
    statusDot: (color) => ({ width: "8px", height: "8px", borderRadius: "50%", background: color, display: "inline-block", marginRight: "6px", boxShadow: `0 0 6px ${color}` }),
    sectionTitle: { fontSize: "18px", fontWeight: "700", marginBottom: "14px", color: "#f1f5f9", display: "flex", alignItems: "center", gap: "8px" },
  };

  // ── NOTIFICATION DROPDOWN ──
  const NotifDropdown = () => (
    <div style={{ position: "absolute", top: "44px", right: "24px", width: "320px", background: "#1e293b", borderRadius: "14px", border: "1px solid #293548", boxShadow: "0 12px 40px rgba(0,0,0,0.4)", zIndex: 200, overflow: "hidden" }}>
      <div style={{ padding: "14px 18px", borderBottom: "1px solid #293548", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontWeight: "700", fontSize: "14px" }}>Notifications</span>
        <span onClick={() => setNotifications(ns => ns.map(n => ({ ...n, read: true })))} style={{ fontSize: "11px", color: "#4ade80", cursor: "pointer" }}>Mark all read</span>
      </div>
      {notifications.map(n => (
        <div key={n.id} style={{ padding: "12px 18px", borderBottom: "1px solid #1e293b", background: n.read ? "transparent" : "#1e3a2e20", display: "flex", alignItems: "flex-start", gap: "10px" }}>
          {!n.read && <span style={s.statusDot("#4ade80")} />}
          <div>
            <div style={{ fontSize: "13px", color: "#e2e8f0" }}>{n.text}</div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>{n.time}</div>
          </div>
        </div>
      ))}
    </div>
  );

  // ══════════════════════════════════════════════════════════════════════════
  // DASHBOARD TAB
  // ══════════════════════════════════════════════════════════════════════════
  const DashboardTab = () => (
    <div>
      {/* Live Status Bar */}
      <div style={{ ...s.card, marginBottom: "20px", background: "linear-gradient(135deg, #1a2332, #1e293b)", display: "flex", flexWrap: "wrap", gap: "20px", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ ...s.statusDot("#4ade80") }}></span>
          <span style={{ fontSize: "13px", fontWeight: "600", color: "#4ade80" }}>LIVE — IoT Devices Connected</span>
        </div>
        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
          {devices.filter(d => d.status === "connected").map(d => (
            <span key={d.id} style={{ fontSize: "12px", color: "#94a3b8" }}>{d.icon} {d.name}</span>
          ))}
        </div>
        <span style={{ fontSize: "11px", color: "#475569" }}>Last sync: {new Date().toLocaleTimeString()}</span>
      </div>

      {/* Vital Cards Row */}
      <div style={s.grid2}>
        {/* Heart Rate */}
        <div style={{ ...s.card, borderTop: "3px solid #f87171" }}>
          <div style={s.cardHeader}>
            <span style={s.cardLabel}>Heart Rate</span>
            <span style={{ fontSize: "11px", color: "#4ade80", background: "#4ade8020", padding: "2px 8px", borderRadius: "10px" }}>● Live</span>
          </div>
          <div style={s.cardValue}>{vitals.heartRate}<span style={s.cardUnit}>bpm</span></div>
          <Sparkline data={Array.from({ length: 20 }, () => generateHeartRate(vitals.heartRate))} color="#f87171" width={180} height={36} />
        </div>

        {/* SpO2 */}
        <div style={{ ...s.card, borderTop: "3px solid #22d3ee" }}>
          <div style={s.cardHeader}>
            <span style={s.cardLabel}>Blood Oxygen</span>
            <span style={{ fontSize: "11px", color: "#22d3ee", background: "#22d3ee20", padding: "2px 8px", borderRadius: "10px" }}>● Live</span>
          </div>
          <div style={s.cardValue}>{vitals.spO2}<span style={s.cardUnit}>%</span></div>
          <Sparkline data={Array.from({ length: 20 }, () => generateSpO2())} color="#22d3ee" width={180} height={36} />
        </div>

        {/* Temperature */}
        <div style={{ ...s.card, borderTop: "3px solid #fb923c" }}>
          <div style={s.cardHeader}>
            <span style={s.cardLabel}>Temperature</span>
            <span style={{ fontSize: "11px", color: "#fb923c", background: "#fb923c20", padding: "2px 8px", borderRadius: "10px" }}>Normal</span>
          </div>
          <div style={s.cardValue}>{vitals.temperature}<span style={s.cardUnit}>°C</span></div>
          <div style={{ display: "flex", gap: "4px", marginTop: "8px" }}>
            {["36.0", "36.3", "36.6", "36.9", "37.2", "37.5"].map(t => (
              <div key={t} style={{ flex: 1, height: "6px", borderRadius: "3px", background: Math.abs(parseFloat(t) - vitals.temperature) < 0.15 ? "#fb923c" : "#1e293b" }} />
            ))}
          </div>
        </div>

        {/* HRV */}
        <div style={{ ...s.card, borderTop: "3px solid #a78bfa" }}>
          <div style={s.cardHeader}>
            <span style={s.cardLabel}>HRV Score</span>
            <span style={{ fontSize: "11px", color: vitals.hrv > 50 ? "#4ade80" : "#fb923c", background: vitals.hrv > 50 ? "#4ade8020" : "#fb923c20", padding: "2px 8px", borderRadius: "10px" }}>{vitals.hrv > 50 ? "Good" : "Fair"}</span>
          </div>
          <div style={s.cardValue}>{vitals.hrv}<span style={s.cardUnit}>ms</span></div>
          <div style={{ width: "100%", height: "6px", background: "#1e293b", borderRadius: "3px", marginTop: "10px", overflow: "hidden" }}>
            <div style={{ width: `${(vitals.hrv / 100) * 100}%`, height: "100%", background: "linear-gradient(90deg, #f87171, #fb923c, #4ade80)", borderRadius: "3px", transition: "width 0.4s" }} />
          </div>
        </div>
      </div>

      {/* BP + Steps + Sleep Row */}
      <div style={s.grid3}>
        {/* Blood Pressure */}
        <div style={s.card}>
          <div style={s.cardHeader}>
            <span style={s.cardLabel}>Blood Pressure</span>
            <span style={{ fontSize: "11px", color: "#64748b" }}>30-day trend</span>
          </div>
          <div style={{ display: "flex", gap: "20px", marginBottom: "10px" }}>
            <div><span style={{ fontSize: "22px", fontWeight: "800", color: "#f87171" }}>{vitals.bp.systolic}</span><span style={{ fontSize: "11px", color: "#64748b" }}> SYS</span></div>
            <span style={{ color: "#475569", fontSize: "18px" }}>/</span>
            <div><span style={{ fontSize: "22px", fontWeight: "800", color: "#60a5fa" }}>{vitals.bp.diastolic}</span><span style={{ fontSize: "11px", color: "#64748b" }}> DIA</span></div>
            <span style={{ fontSize: "11px", color: "#64748b", alignSelf: "flex-end" }}>mmHg</span>
          </div>
          <BPChart data={monthlyBP} />
          <div style={{ display: "flex", gap: "16px", marginTop: "8px" }}>
            <span style={{ fontSize: "11px", color: "#f87171" }}>━ Systolic</span>
            <span style={{ fontSize: "11px", color: "#60a5fa" }}>━ Diastolic</span>
          </div>
        </div>

        {/* Steps */}
        <div style={s.card}>
          <div style={s.cardHeader}>
            <span style={s.cardLabel}>Steps — Weekly</span>
            <span style={{ fontSize: "11px", color: "#4ade80" }}>+12% vs last week</span>
          </div>
          <BarChart data={weeklySteps} valueKey="value" color="#4ade80" maxVal={12000} />
        </div>

        {/* Sleep */}
        <div style={s.card}>
          <div style={s.cardHeader}>
            <span style={s.cardLabel}>Sleep — Weekly</span>
            <span style={{ fontSize: "11px", color: "#a78bfa" }}>Avg 7.1h</span>
          </div>
          <BarChart data={weeklySleep} valueKey="value" color="#a78bfa" maxVal={10} unit="h" />
        </div>
      </div>

      {/* AI Insights */}
      <div style={{ ...s.card, marginBottom: "20px" }}>
        <div style={s.sectionTitle}>🤖 AI Health Insights <span style={{ fontSize: "11px", color: "#64748b", fontWeight: "400" }}>— Updated every 3 seconds</span></div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px" }}>
          {aiInsights.map((ins, i) => (
            <div key={i} style={{ background: ins.type === "alert" ? "#3b1515" : ins.type === "warning" ? "#2a2218" : "#1a2e2a", borderRadius: "12px", padding: "14px", border: `1px solid ${ins.type === "alert" ? "#7f1d1d" : ins.type === "warning" ? "#4a3e1a" : "#1e3a2e"}` }}>
              <div style={{ fontSize: "16px", marginBottom: "4px" }}>{ins.icon} <span style={{ fontSize: "13px", fontWeight: "700", color: ins.type === "alert" ? "#fca5a5" : ins.type === "warning" ? "#fde68a" : "#86efac" }}>{ins.title}</span></div>
              <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0, lineHeight: "1.4" }}>{ins.message}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Row: Gauges + Calories */}
      <div style={s.grid3}>
        <div style={s.card}>
          <div style={s.cardHeader}><span style={s.cardLabel}>Key Metrics</span></div>
          <div style={{ display: "flex", justifyContent: "space-around" }}>
            <RadialGauge value={vitals.steps} max={10000} color="#4ade80" label="Steps" unit="/ 10k" />
            <RadialGauge value={vitals.hydration} max={8} color="#60a5fa" label="Water" unit="/ 8 glasses" />
            <RadialGauge value={vitals.stressLevel} max={100} color="#fb923c" label="Stress" unit="/ 100" />
          </div>
        </div>
        <div style={s.card}>
          <div style={s.cardHeader}><span style={s.cardLabel}>Calories Burned</span><span style={{ fontSize: "11px", color: "#fb923c" }}>🔥</span></div>
          <div style={s.cardValue}>{vitals.calories}<span style={s.cardUnit}>kcal</span></div>
          <div style={{ marginTop: "10px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>
              <span>Progress to goal (2500 kcal)</span><span>{Math.round((vitals.calories / 2500) * 100)}%</span>
            </div>
            <div style={{ width: "100%", height: "8px", background: "#1e293b", borderRadius: "4px", overflow: "hidden" }}>
              <div style={{ width: `${Math.min((vitals.calories / 2500) * 100, 100)}%`, height: "100%", background: "linear-gradient(90deg, #fb923c, #f87171)", borderRadius: "4px" }} />
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "space-around", marginTop: "14px" }}>
            {[{ label: "BMR", val: "1820", color: "#60a5fa" }, { label: "Exercise", val: "330", color: "#4ade80" }].map(item => (
              <div key={item.label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: "16px", fontWeight: "700", color: item.color }}>{item.val}</div>
                <div style={{ fontSize: "10px", color: "#64748b" }}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={s.card}>
          <div style={s.cardHeader}><span style={s.cardLabel}>Heart Rate Weekly</span></div>
          <BarChart data={weeklyHR} valueKey="value" color="#f87171" maxVal={100} unit="" />
        </div>
      </div>
    </div>
  );

  // ══════════════════════════════════════════════════════════════════════════
  // GOALS TAB
  // ══════════════════════════════════════════════════════════════════════════
  const GoalsTab = () => (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
        <div style={s.sectionTitle}>🎯 Daily Goals</div>
        <button style={{ background: "linear-gradient(135deg, #4ade80, #22d3ee)", color: "#0f172a", border: "none", padding: "8px 16px", borderRadius: "20px", cursor: "pointer", fontSize: "13px", fontWeight: "700" }}>+ Add Goal</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
        {goals.map(g => {
          const pct = Math.min((g.current / g.target) * 100, 100);
          return (
            <div key={g.id} style={s.card}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "24px" }}>{g.icon}</span>
                  <div>
                    <div style={{ fontSize: "15px", fontWeight: "700" }}>{g.label}</div>
                    <div style={{ fontSize: "12px", color: "#64748b" }}>{g.current} / {g.target} {g.unit}</div>
                  </div>
                </div>
                <span style={{ fontSize: "18px", fontWeight: "800", color: g.color }}>{Math.round(pct)}%</span>
              </div>
              <div style={{ width: "100%", height: "10px", background: "#1e293b", borderRadius: "5px", marginTop: "14px", overflow: "hidden" }}>
                <div style={{ width: `${pct}%`, height: "100%", background: pct >= 100 ? "linear-gradient(90deg, #4ade80, #22d3ee)" : `linear-gradient(90deg, ${g.color}, ${g.color}bb)`, borderRadius: "5px", transition: "width 0.6s cubic-bezier(0.4,0,0.2,1)" }} />
              </div>
              {pct >= 100 && <div style={{ marginTop: "8px", fontSize: "12px", color: "#4ade80", fontWeight: "600" }}>🎉 Goal achieved!</div>}
            </div>
          );
        })}
      </div>

      {/* Weekly Summary */}
      <div style={{ ...s.card, marginTop: "24px" }}>
        <div style={s.sectionTitle}>📊 Weekly Performance</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "12px" }}>
          {[
            { label: "Goals Completed", value: "5/7", color: "#4ade80", sub: "71% rate" },
            { label: "Avg Steps", value: "8.2k", color: "#60a5fa", sub: "↑ 15%" },
            { label: "Sleep Quality", value: "7.4h", color: "#a78bfa", sub: "Good" },
            { label: "Active Minutes", value: "94", color: "#fb923c", sub: "↑ 8%" },
            { label: "Hydration", value: "6.8", color: "#22d3ee", sub: "glasses/day" },
            { label: "Stress Avg", value: "42", color: "#f87171", sub: "Moderate" },
          ].map((item, i) => (
            <div key={i} style={{ background: "#1a2332", borderRadius: "12px", padding: "14px", textAlign: "center", border: "1px solid #1e293b" }}>
              <div style={{ fontSize: "22px", fontWeight: "800", color: item.color }}>{item.value}</div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>{item.label}</div>
              <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>{item.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // ══════════════════════════════════════════════════════════════════════════
  // DEVICES TAB
  // ══════════════════════════════════════════════════════════════════════════
  const DevicesTab = () => (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
        <div style={s.sectionTitle}>📱 Connected Devices</div>
        <button style={{ background: "linear-gradient(135deg, #4ade80, #22d3ee)", color: "#0f172a", border: "none", padding: "8px 16px", borderRadius: "20px", cursor: "pointer", fontSize: "13px", fontWeight: "700" }}>+ Pair Device</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
        {devices.map(d => (
          <div key={d.id} style={{ ...s.card, display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ width: "52px", height: "52px", borderRadius: "14px", background: d.status === "connected" ? "#1a2e2a" : "#2a2420", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "24px", border: `1px solid ${d.status === "connected" ? "#1e3a2e" : "#3a2e20"}` }}>{d.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "14px", fontWeight: "700" }}>{d.name}</span>
                <span style={{ fontSize: "11px", color: d.status === "connected" ? "#4ade80" : "#fb923c", background: d.status === "connected" ? "#4ade8020" : "#fb923c20", padding: "3px 10px", borderRadius: "12px", textTransform: "capitalize" }}>{d.status}</span>
              </div>
              <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px" }}>Last sync: {d.lastSync}</div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "6px" }}>
                <span style={{ fontSize: "10px", color: "#64748b" }}>🔋 {d.battery}%</span>
                <div style={{ flex: 1, height: "4px", background: "#1e293b", borderRadius: "2px", overflow: "hidden" }}>
                  <div style={{ width: `${d.battery}%`, height: "100%", background: d.battery > 50 ? "#4ade80" : d.battery > 20 ? "#fb923c" : "#f87171", borderRadius: "2px" }} />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* IoT Architecture Diagram */}
      <div style={{ ...s.card, marginTop: "24px" }}>
        <div style={s.sectionTitle}>🔗 IoT System Architecture</div>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "0", flexWrap: "wrap", padding: "20px 0" }}>
          {[
            { label: "IoT Sensors", icon: "📡", color: "#60a5fa", desc: "Wearables & Smart Devices" },
            { label: "Edge Gateway", icon: "🔄", color: "#a78bfa", desc: "Data Preprocessing" },
            { label: "Cloud Server", icon: "☁️", color: "#22d3ee", desc: "Storage & Processing" },
            { label: "AI Engine", icon: "🤖", color: "#4ade80", desc: "ML Analysis & Insights" },
            { label: "User Dashboard", icon: "📊", color: "#fb923c", desc: "Visualization & Alerts" },
          ].map((node, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center" }}>
              <div style={{ textAlign: "center", width: "130px" }}>
                <div style={{ width: "60px", height: "60px", borderRadius: "16px", background: `${node.color}15`, border: `2px solid ${node.color}40`, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "24px" }}>{node.icon}</div>
                <div style={{ fontSize: "12px", fontWeight: "700", color: node.color, marginTop: "8px" }}>{node.label}</div>
                <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>{node.desc}</div>
              </div>
              {i < 4 && <div style={{ fontSize: "20px", color: "#475569", marginBottom: "28px" }}>→</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // ══════════════════════════════════════════════════════════════════════════
  // AI ANALYSIS TAB
  // ══════════════════════════════════════════════════════════════════════════
  const AITab = () => {
    const [analysisRunning, setAnalysisRunning] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);

    const runAnalysis = () => {
      setAnalysisRunning(true);
      setTimeout(() => {
        setAnalysisResult({
          overallScore: 78,
          riskLevel: "Low",
          trends: [
            { metric: "Heart Rate", trend: "Stable", change: "+2%", good: true },
            { metric: "Sleep Quality", trend: "Improving", change: "+8%", good: true },
            { metric: "Activity Level", trend: "Declining", change: "-5%", good: false },
            { metric: "Stress Levels", trend: "Elevated", change: "+12%", good: false },
            { metric: "Hydration", trend: "On Track", change: "+3%", good: true },
            { metric: "Blood Pressure", trend: "Stable", change: "-1%", good: true },
          ],
          recommendations: [
            "Increase daily step count by adding a 15-minute evening walk.",
            "Practice breathing exercises to manage elevated stress levels.",
            "Maintain current sleep schedule — your consistency is improving.",
            "Consider adding resistance training to complement cardio activity.",
            "Keep up hydration — aim for 8 glasses per day.",
          ],
        });
        setAnalysisRunning(false);
      }, 2200);
    };

    return (
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
          <div style={s.sectionTitle}>🤖 AI Health Analysis</div>
          <button onClick={runAnalysis} disabled={analysisRunning} style={{ background: analysisRunning ? "#475569" : "linear-gradient(135deg, #4ade80, #22d3ee)", color: analysisRunning ? "#94a3b8" : "#0f172a", border: "none", padding: "10px 20px", borderRadius: "22px", cursor: analysisRunning ? "not-allowed" : "pointer", fontSize: "13px", fontWeight: "700", display: "flex", alignItems: "center", gap: "6px" }}>
            {analysisRunning ? "⏳ Analyzing..." : "▶ Run Full Analysis"}
          </button>
        </div>

        {/* Health Score */}
        <div style={{ ...s.card, marginBottom: "16px", display: "flex", gap: "30px", alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ width: "120px", height: "120px", borderRadius: "50%", background: "conic-gradient(from 220deg, #1e293b 0%, #1e293b 62%, #4ade80 62%, #4ade80 100%)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto" }}>
              <div style={{ width: "86px", height: "86px", borderRadius: "50%", background: "#1e293b", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: "32px", fontWeight: "800", color: "#4ade80" }}>78</span>
                <span style={{ fontSize: "10px", color: "#64748b" }}>/ 100</span>
              </div>
            </div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "#f1f5f9", marginTop: "8px" }}>Overall Health Score</div>
            <div style={{ fontSize: "11px", color: "#4ade80" }}>Risk: Low</div>
          </div>
          <div style={{ flex: 1, minWidth: "200px" }}>
            <div style={{ fontSize: "13px", fontWeight: "600", color: "#94a3b8", marginBottom: "10px" }}>Score Breakdown</div>
            {[
              { label: "Cardiovascular", value: 82, color: "#f87171" },
              { label: "Sleep Health", value: 75, color: "#a78bfa" },
              { label: "Activity", value: 68, color: "#4ade80" },
              { label: "Nutrition & Hydration", value: 79, color: "#60a5fa" },
              { label: "Mental Wellness", value: 72, color: "#fb923c" },
            ].map((item, i) => (
              <div key={i} style={{ marginBottom: "8px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#94a3b8", marginBottom: "3px" }}>
                  <span>{item.label}</span><span style={{ color: item.color, fontWeight: "700" }}>{item.value}</span>
                </div>
                <div style={{ width: "100%", height: "6px", background: "#1e293b", borderRadius: "3px", overflow: "hidden" }}>
                  <div style={{ width: `${item.value}%`, height: "100%", background: item.color, borderRadius: "3px" }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Trend Analysis */}
        {analysisResult && (
          <>
            <div style={s.card}>
              <div style={s.sectionTitle}>📈 Trend Analysis</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "12px" }}>
                {analysisResult.trends.map((t, i) => (
                  <div key={i} style={{ background: "#1a2332", borderRadius: "10px", padding: "12px", textAlign: "center", border: `1px solid ${t.good ? "#1e3a2e" : "#3a2e20"}` }}>
                    <div style={{ fontSize: "13px", fontWeight: "700", color: "#f1f5f9" }}>{t.metric}</div>
                    <div style={{ fontSize: "11px", color: t.good ? "#4ade80" : "#fb923c", marginTop: "4px" }}>{t.trend}</div>
                    <div style={{ fontSize: "14px", fontWeight: "800", color: t.good ? "#4ade80" : "#f87171", marginTop: "4px" }}>{t.change}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ ...s.card, marginTop: "16px" }}>
              <div style={s.sectionTitle}>💡 AI Recommendations</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {analysisResult.recommendations.map((rec, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "12px", background: "#1a2332", borderRadius: "10px", padding: "12px 16px", border: "1px solid #1e293b" }}>
                    <span style={{ width: "24px", height: "24px", borderRadius: "50%", background: "linear-gradient(135deg, #4ade80, #22d3ee)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", color: "#0f172a", fontWeight: "700", flexShrink: 0 }}>{i + 1}</span>
                    <span style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: "1.5" }}>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {!analysisResult && (
          <div style={{ ...s.card, textAlign: "center", padding: "50px 20px" }}>
            <div style={{ fontSize: "48px", marginBottom: "12px" }}>🧬</div>
            <div style={{ fontSize: "16px", color: "#94a3b8", fontWeight: "600" }}>Run a full AI analysis to get deep health insights</div>
            <div style={{ fontSize: "13px", color: "#64748b", marginTop: "6px" }}>Our ML models analyze your vitals, habits, and trends to provide personalized recommendations.</div>
          </div>
        )}
      </div>
    );
  };

  // ══════════════════════════════════════════════════════════════════════════
  // HISTORY TAB
  // ══════════════════════════════════════════════════════════════════════════
  const HistoryTab = () => {
    const historyData = Array.from({ length: 14 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return {
        date: `${MONTHS[date.getMonth()]} ${date.getDate()}`,
        hr: generateHeartRate(),
        spO2: generateSpO2(),
        steps: generateSteps(),
        sleep: generateSleepHours(),
        bp: generateBloodPressure(),
        stress: generateStressLevel(),
      };
    });

    return (
      <div>
        <div style={s.sectionTitle}>📋 Health History — Last 14 Days</div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "600px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #293548" }}>
                {["Date", "Heart Rate", "SpO2", "Steps", "Sleep", "BP", "Stress"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "10px 12px", fontSize: "11px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.6px", fontWeight: "600" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {historyData.map((row, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #1e293b", background: i % 2 === 0 ? "#0f172a" : "#1a2332" }}>
                  <td style={{ padding: "10px 12px", fontSize: "13px", color: "#cbd5e1", fontWeight: "600" }}>{row.date}</td>
                  <td style={{ padding: "10px 12px" }}><span style={{ fontSize: "13px", color: "#f87171", fontWeight: "700" }}>{row.hr}</span><span style={{ fontSize: "10px", color: "#64748b" }}> bpm</span></td>
                  <td style={{ padding: "10px 12px" }}><span style={{ fontSize: "13px", color: "#22d3ee", fontWeight: "700" }}>{row.spO2}</span><span style={{ fontSize: "10px", color: "#64748b" }}> %</span></td>
                  <td style={{ padding: "10px 12px" }}><span style={{ fontSize: "13px", color: "#4ade80", fontWeight: "700" }}>{row.steps.toLocaleString()}</span></td>
                  <td style={{ padding: "10px 12px" }}><span style={{ fontSize: "13px", color: "#a78bfa", fontWeight: "700" }}>{row.sleep}</span><span style={{ fontSize: "10px", color: "#64748b" }}> hrs</span></td>
                  <td style={{ padding: "10px 12px" }}><span style={{ fontSize: "13px", color: "#f87171", fontWeight: "700" }}>{row.bp.systolic}/{row.bp.diastolic}</span><span style={{ fontSize: "10px", color: "#64748b" }}> mmHg</span></td>
                  <td style={{ padding: "10px 12px" }}>
                    <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "10px", background: row.stress > 60 ? "#3b1515" : row.stress > 40 ? "#2a2218" : "#1a2e2a", color: row.stress > 60 ? "#fca5a5" : row.stress > 40 ? "#fde68a" : "#86efac", fontWeight: "600" }}>
                      {row.stress > 60 ? "High" : row.stress > 40 ? "Moderate" : "Low"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Export Options */}
        <div style={{ ...s.card, marginTop: "20px", display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontSize: "13px", color: "#94a3b8", fontWeight: "600" }}>Export Data:</span>
          {["CSV", "PDF", "JSON"].map(fmt => (
            <button key={fmt} style={{ background: "#1a2332", color: "#94a3b8", border: "1px solid #293548", padding: "6px 16px", borderRadius: "16px", cursor: "pointer", fontSize: "12px", fontWeight: "600" }}>{fmt}</button>
          ))}
        </div>
      </div>
    );
  };

  // ══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ══════════════════════════════════════════════════════════════════════════
  const tabs = [
    { id: "dashboard", label: "📊 Dashboard" },
    { id: "ai", label: "🤖 AI Analysis" },
    { id: "goals", label: "🎯 Goals" },
    { id: "devices", label: "📱 Devices" },
    { id: "history", label: "📋 History" },
  ];

  return (
    <div style={s.app}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.logo}>
          <div style={s.logoIcon}>❤️</div>
          <div>
            <div style={s.logoText}>HealthSync</div>
            <div style={s.logoSub}>IoT Health Ecosystem</div>
          </div>
        </div>
        <div style={s.headerRight}>
          <div style={{ position: "relative" }}>
            <button style={s.notifBtn} onClick={() => setShowNotif(!showNotif)}>🔔</button>
            {unreadCount > 0 && <div style={s.notifBadge}>{unreadCount}</div>}
            {showNotif && <NotifDropdown />}
          </div>
          <div style={s.avatar}>JD</div>
        </div>
      </div>

      {/* Navigation */}
      <div style={s.nav}>
        {tabs.map(t => (
          <button key={t.id} style={s.navBtn(activeTab === t.id)} onClick={() => setActiveTab(t.id)}>{t.label}</button>
        ))}
      </div>

      {/* Content */}
      <div style={s.content} onClick={() => setShowNotif(false)}>
        {activeTab === "dashboard" && <DashboardTab />}
        {activeTab === "ai" && <AITab />}
        {activeTab === "goals" && <GoalsTab />}
        {activeTab === "devices" && <DevicesTab />}
        {activeTab === "history" && <HistoryTab />}
      </div>
    </div>
  );
}
