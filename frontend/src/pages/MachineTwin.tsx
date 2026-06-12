import { useEffect, useState } from"react";
import { useParams, Link } from"react-router-dom";
import {
 ArrowLeft,
 Activity,
 AlertTriangle,
 ShieldAlert,
 History,
 CheckCircle,
 Info,
 Clock,
 RefreshCw,
 AlertOctagon,
 Heart,
 Zap,
 Waves,
 Thermometer,
 ShieldCheck,
} from"lucide-react";
import {
 AreaChart,
 Area,
 XAxis,
 YAxis,
 CartesianGrid,
 Tooltip,
 ResponsiveContainer,
} from"recharts";
import { machineService } from"../services/machineService";
import type { MachineAnalyticsResponse } from"../services/machineService";


// Helper for explanatory tooltips
function InfoTooltip({
 title,
 definition,
 why,
 good,
 bad,
}: {
 title: string;
 definition: string;
 why: string;
 good: string;
 bad: string;
}) {
 return (
 <div className="relative group inline-block ml-1.5 align-middle">
 <Info className="h-4 w-4 text-muted-foreground hover:text-white cursor-help transition-colors" />
 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-3.5 w-72 bg-[#14171d] border border-border text-xs text-gray-300 p-3.5 rounded-lg shadow-2xl hidden group-hover:block z-50 pointer-events-none leading-relaxed normal-case font-normal text-left">
 <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-[#14171d]"></div>
 <div className="font-bold text-white mb-1.5 border-b border-border/40 pb-1">{title}</div>
 <div className="mb-1.5">
 <span className="text-primary font-bold">Definition:</span> {definition}
 </div>
 <div className="mb-1.5">
 <span className="text-primary font-bold">Why it matters:</span> {why}
 </div>
 <div className="grid grid-cols-2 gap-2 mt-2 pt-1.5 border-t border-border/20 text-[10px]">
 <div>
 <span className="text-emerald-400 font-bold">Healthy:</span> {good}
 </div>
 <div>
 <span className="text-red-400 font-bold">Critical:</span> {bad}
 </div>
 </div>
 </div>
 </div>
 );
}

// Gauge Component for Live Operating Conditions
function GaugeBar({
 label,
 value,
 unit,
 min,
 max,
 status,
 explain,
 icon,
}: {
 label: string;
 value: number | null;
 unit: string;
 min: number;
 max: number;
 status:"healthy" |"warning" |"critical";
 explain: string;
 icon: React.ReactNode;
}) {
 const displayVal = value !== null ? value.toFixed(1) :"N/A";
 const percent = value !== null ? Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100)) : 0;

 const barColor =
 status ==="critical" ?"bg-rose-500" : status ==="warning" ?"bg-amber-500" :"bg-emerald-500";
 const textColor =
 status ==="critical" ?"text-rose-400" : status ==="warning" ?"text-amber-400" :"text-emerald-400";
 const borderColor =
 status ==="critical" ?"border-rose-500/20" : status ==="warning" ?"border-amber-500/20" :"border-emerald-500/20";

 return (
 <div className={`bg-[#0d0f12] p-5 border rounded-xl flex flex-col justify-between space-y-3 shadow-sm ${borderColor}`}>
 <div className="flex justify-between items-center text-xs font-semibold">
 <span className="text-muted-foreground uppercase flex items-center gap-1.5">
 {icon}
 {label}
 </span>
 <span className={`font-bold text-sm ${textColor}`}>
 {displayVal} {unit}
 </span>
 </div>
 <div className="h-2 bg-[#14171d] rounded-full overflow-hidden border border-border/20">
 <div
 className={`h-full rounded-full transition-all duration-500 ${barColor}`}
 style={{ width: `${percent}%` }}
 ></div>
 </div>
 <div className="flex justify-between text-[10px] font-medium text-gray-500">
 <span>Min: {min} {unit}</span>
 <span className="truncate max-w-[120px]" title={explain}>{explain}</span>
 <span>Max: {max} {unit}</span>
 </div>
 </div>
 );
}

export default function MachineTwin() {
 const { id } = useParams<{ id: string }>();
 const [machine, setMachine] = useState<MachineAnalyticsResponse | null>(null);

 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 // Time & Trend selectors
 const [twinWindow, setTwinWindow] = useState<string>("24h");
 const [activeTrend, setActiveTrend] = useState<"temperature" |"degradation" |"efficiency" |"power">(
"temperature"
 );
 const [isRefreshing, setIsRefreshing] = useState(false);

 useEffect(() => {
 async function fetchMachineData() {
 if (!id) return;
 setIsRefreshing(true);
 try {
 const twinData = await machineService.getMachineDetails(id, twinWindow);
 setMachine(twinData);

 setError(null);
 } catch (err: any) {
 setError(err.message ||"Failed to load digital twin telemetry & diagnostics");
 } finally {
 setLoading(false);
 setIsRefreshing(false);
 }
 }
 fetchMachineData();
 const interval = setInterval(fetchMachineData, 30000); // 30s auto-refresh
 return () => clearInterval(interval);
 }, [id, twinWindow]);

 if (loading) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-gray-400">
 <div className="text-center space-y-3">
 <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto"></div>
 <p className="text-sm font-semibold tracking-widest uppercase">Connecting Digital Twin Stream...</p>
 </div>
 </div>
 );
 }

 if (error || !machine) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-red-400 p-8">
 <div className="max-w-md text-center border border-red-500/20 bg-red-950/10 p-8 rounded-xl">
 <AlertTriangle className="h-10 w-10 mx-auto mb-3 text-red-500" />
 <h3 className="font-bold text-base mb-2">Twin Connection Failed</h3>
 <p className="text-sm text-gray-400 mb-4">{error ||"Twin telemetry record not found"}</p>
 <Link
 to="/"
 className="px-5 py-2.5 bg-primary text-white rounded-lg text-sm hover:bg-primary/95 transition font-semibold"
 >
 Back to Dashboard
 </Link>
 </div>
 </div>
 );
 }

 // Formatting history for Recharts
 const trendChartData = machine.history.map((h) => {
 let val = 0;
 if (activeTrend ==="temperature") val = h.temperature ?? 0;
 else if (activeTrend ==="degradation") val = h.degradation_level * 100;
 else if (activeTrend ==="efficiency") val = h.cycle_efficiency ?? (h.anomaly_detected ? 78 : 95);
 else if (activeTrend ==="power") val = h.power_consumption ?? 0;

 return {
 time: h.timestamp,
 value: Number(val.toFixed(1)),
 };
 });

 // Color code status badges
 const getStatusBadge = (status: string) => {
 switch (status) {
 case"healthy":
 return (
 <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase flex items-center gap-1.5">
 <ShieldCheck className="h-4 w-4 text-emerald-400" />
 Healthy
 </span>
 );
 case"warning":
 return (
 <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase flex items-center gap-1.5">
 <AlertTriangle className="h-4 w-4 text-amber-400 animate-pulse" />
 Warning
 </span>
 );
 case"critical":
 return (
 <span className="bg-rose-500/10 text-rose-400 border border-rose-500/20 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase flex items-center gap-1.5 animate-pulse">
 <AlertOctagon className="h-4 w-4 text-rose-400" />
 Critical Fault
 </span>
 );
 default:
 return (
 <span className="bg-slate-500/10 text-slate-400 border border-slate-500/20 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase">
 Offline
 </span>
 );
 }
 };

 // Determine status color for gauges
 const getMetricStatus = (metric: string, val: number | null) => {
 if (val === null) return"healthy";
 if (metric ==="temperature") {
 return val > 75 ?"critical" : val > 60 ?"warning" :"healthy";
 }
 if (metric ==="pressure") {
 return val > 20 || val < 5 ?"critical" : val > 15 || val < 8 ?"warning" :"healthy";
 }
 if (metric ==="power") {
 return val > 120 ?"critical" : val > 95 ?"warning" :"healthy";
 }
 if (metric ==="vibration") {
 return val > 5 ?"critical" : val > 3.5 ?"warning" :"healthy";
 }
 if (metric ==="degradation") {
 return val > 0.8 ?"critical" : val > 0.4 ?"warning" :"healthy";
 }
 return"healthy";
 };

 // Human-friendly trend definitions
 const getTrendMetadata = () => {
 switch (activeTrend) {
 case"temperature":
 return {
 title:"Temperature Trend",
 unit:"°C",
 color:"#e11d48",
 def:"Current core thermal readings.",
 expected:"Expected: 10 - 75 °C",
 };
 case"degradation":
 return {
 title:"Degradation Trend",
 unit:"%",
 color:"#d97706",
 def:"Estimated component surface wear level.",
 expected:"Expected: Under 40%",
 };
 case"efficiency":
 return {
 title:"Operational Efficiency Trend",
 unit:"%",
 color:"#10b981",
 def:"Cycle efficiency rate relative to design limits.",
 expected:"Expected: 85 - 100 %",
 };
 case"power":
 return {
 title:"Power Consumption Trend",
 unit:"kW",
 color:"#3b82f6",
 def:"Electrical power consumed under load.",
 expected:"Expected: 5 - 120 kW",
 };
 }
 };

 const trendMeta = getTrendMetadata();
 const conds = machine.current_conditions;

 return (
 <div className="p-8 space-y-8 bg-[#0d0f12] min-h-screen text-gray-200 overflow-y-auto">
 {/* ====================================================
 NEW SECTION 1 — MACHINE HEALTH HEADER
 ==================================================== */}
 <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-border pb-6 gap-6">
 <div className="flex items-center gap-4">
 <Link
 to="/machines"
 className="p-2.5 bg-[#14171d] border border-border rounded-lg text-gray-400 hover:text-white hover:bg-[#1c222c] transition shadow-sm"
 >
 <ArrowLeft className="h-5 w-5" />
 </Link>
 <div>
 <div className="flex items-center gap-3">
 <h1 className="text-3xl font-bold text-white flex items-center gap-2">
 Machine <span className="text-primary">{machine.machine_id}</span>
 </h1>
 <div className="flex items-center gap-1.5 text-xs text-muted-foreground ml-3 font-semibold">
 <Clock className="h-4 w-4" />
 <span>Last Updated: {new Date(machine.last_updated).toLocaleTimeString()}</span>
 {isRefreshing && <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary ml-1.5" />}
 </div>
 </div>
 <p className="text-xs text-muted-foreground uppercase font-bold mt-1">
 {machine.machine_type.replace(/_/g,"")} | Factory: AutoForge Node 01
 </p>
 </div>
 </div>
 <div className="flex items-center gap-6">
 <div className="bg-[#14171d] px-5 py-3 border border-border rounded-xl text-right shadow-md">
 <span className="text-xs text-muted-foreground uppercase font-bold block">Health Score</span>
 <span className={`text-2xl font-bold mt-1 block ${
 machine.health_status ==="healthy" ?"text-emerald-400" :
 machine.health_status ==="warning" ?"text-amber-400" :
"text-rose-400"
 }`}>{Math.round(machine.health_score)}%</span>
 </div>
 <div>{getStatusBadge(machine.health_status)}</div>
 </div>
 </div>

 {/* Grid of Gauges + Pred Maintenance */}
 <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
 {/* ====================================================
 NEW SECTION 2 — LIVE OPERATING CONDITIONS
 ==================================================== */}
 <div className="lg:col-span-3 bg-[#101216] border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <div className="flex justify-between items-center border-b border-border/40 pb-3">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2 text-white">
 <Activity className="h-5 w-5 text-primary" />
 Live Operating Conditions
 </h3>
 <InfoTooltip
 title="Live Operating Conditions"
 definition="Current physical parameters from telemetry sensors."
 why="Monitors asset safety bounds and prevents catastrophic failures."
 good="Gauges showing nominal values (Green)."
 bad="Gauges breaching warning (Yellow) or critical (Red) lines."
 />
 </div>
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
 <GaugeBar
 label="Temperature"
 value={conds.temperature}
 unit="°C"
 min={10}
 max={100}
 status={getMetricStatus("temperature", conds.temperature)}
 explain="Thermal state"
 icon={<Thermometer className="h-4 w-4 text-rose-400" />}
 />
 <GaugeBar
 label="Pressure"
 value={conds.pressure}
 unit="bar"
 min={0}
 max={30}
 status={getMetricStatus("pressure", conds.pressure)}
 explain="Pneumatic/Hydraulic"
 icon={<Waves className="h-4 w-4 text-blue-400" />}
 />
 <GaugeBar
 label="Power"
 value={conds.power_consumption}
 unit="kW"
 min={0}
 max={150}
 status={getMetricStatus("power", conds.power_consumption)}
 explain="Power draw load"
 icon={<Zap className="h-4 w-4 text-amber-400" />}
 />
 <GaugeBar
 label="Vibration"
 value={conds.vibration}
 unit="mm/s"
 min={0}
 max={8}
 status={getMetricStatus("vibration", conds.vibration)}
 explain="Harmonics stability"
 icon={<Activity className="h-4 w-4 text-purple-400" />}
 />
 <GaugeBar
 label="Degradation"
 value={conds.degradation * 100}
 unit="%"
 min={0}
 max={100}
 status={getMetricStatus("degradation", conds.degradation)}
 explain="Cumulative wear level"
 icon={<Heart className="h-4 w-4 text-rose-500" />}
 />
 </div>
 </div>

 {/* ====================================================
 NEW SECTION 7 — PREDICTIVE MAINTENANCE PANEL
 ==================================================== */}
 <div className="bg-[#101216] border border-border p-6 rounded-xl flex flex-col justify-between space-y-5 shadow-lg">
 <div className="flex justify-between items-center border-b border-border/40 pb-3">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2 text-white">
 <ShieldAlert className="h-5 w-5 text-primary" />
 Predictive Maintenance
 </h3>
 <InfoTooltip
 title="Predictive Maintenance"
 definition="Proactive analytics estimating mechanical failure probabilities."
 why="Assists maintenance teams to plan shutdowns before physical failures."
 good="Failure Risk < 15%, RUL > 100 days."
 bad="Failure Risk > 50%, RUL < 14 days."
 />
 </div>

 <div className="space-y-4 text-xs font-semibold">
 <div className="flex justify-between items-center bg-[#0d0f12] p-3.5 border border-border/60 rounded-xl shadow-sm">
 <span className="text-muted-foreground uppercase text-[10px]">Failure Risk</span>
 <span
 className={`text-base font-bold ${
 machine.predictive_maintenance.failure_risk_pct > 70
 ?"text-rose-500 animate-pulse"
 : machine.predictive_maintenance.failure_risk_pct > 30
 ?"text-amber-500"
 :"text-emerald-400"
 }`}
 >
 {machine.predictive_maintenance.failure_risk_pct}%
 </span>
 </div>

 <div className="flex justify-between items-center bg-[#0d0f12] p-3.5 border border-border/60 rounded-xl shadow-sm">
 <span className="text-muted-foreground uppercase text-[10px]">Remaining Useful Life</span>
 <span className="text-base font-bold text-white">
 {machine.predictive_maintenance.remaining_useful_life_days} days
 </span>
 </div>

 <div className="flex justify-between items-center bg-[#0d0f12] p-3.5 border border-border/60 rounded-xl shadow-sm">
 <span className="text-muted-foreground uppercase text-[10px]">Health Trend</span>
 <span
 className={`text-base font-bold uppercase ${
 machine.predictive_maintenance.health_trend ==="Stable"
 ?"text-emerald-400"
 :"text-rose-400 animate-pulse"
 }`}
 >
 {machine.predictive_maintenance.health_trend}
 </span>
 </div>
 </div>

 <div className="bg-[#0d0f12] p-4 rounded-xl border border-border/60 shadow-inner">
 <span className="text-xs text-muted-foreground uppercase font-bold block mb-1">
 Recommendation
 </span>
 <p className="text-xs text-gray-300 leading-relaxed font-semibold">
 {machine.predictive_maintenance.maintenance_recommendation}
 </p>
 </div>
 </div>
 </div>

 {/* ====================================================
 NEW SECTION 3 — HEALTH TREND ANALYTICS
 ==================================================== */}
 <div className="bg-[#101216] border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-border/40 pb-4 gap-4">
 <div className="flex items-center gap-2.5">
 <h3 className="text-lg font-bold uppercase text-white">
 Health Trend Analytics
 </h3>
 <InfoTooltip
 title="Trend Analytics"
 definition="High-resolution time-series plotting core health parameters."
 why="Detects slow-drift degradation patterns and transient spike events."
 good="Stable horizontal paths within metric bounds."
 bad="Rising slopes (degradation) or steep curves (runaway heating)."
 />
 </div>

 {/* Metric Selector Tabs */}
 <div className="flex items-center gap-2 bg-[#0d0f12] p-1.5 border border-border/40 rounded-lg text-xs">
 {[
 { id:"temperature", label:"Temperature" },
 { id:"degradation", label:"Degradation" },
 { id:"efficiency", label:"Efficiency" },
 { id:"power", label:"Power" },
 ].map((tab) => (
 <button
 key={tab.id}
 onClick={() => setActiveTrend(tab.id as any)}
 className={`px-3.5 py-1.5 rounded-md transition text-xs font-semibold ${
 activeTrend === tab.id
 ?"bg-[#1c222c] text-white border border-border/80 shadow-sm"
 :"text-muted-foreground hover:text-white"
 }`}
 >
 {tab.label}
 </button>
 ))}
 </div>

 {/* Window selectors */}
 <div className="flex items-center gap-2 bg-[#0d0f12] p-1.5 border border-border/40 rounded-lg text-xs">
 {["15m","1h","24h","7d"].map((win) => (
 <button
 key={win}
 onClick={() => setTwinWindow(win)}
 className={`px-3.5 py-1.5 rounded-md transition text-xs font-semibold ${
 twinWindow === win ?"bg-primary text-white font-bold" :"text-muted-foreground hover:text-white"
 }`}
 >
 {win ==="15m" ?"15 Min" : win ==="1h" ?"1 Hour" : win ==="24h" ?"24 Hours" :"7 Days"}
 </button>
 ))}
 </div>
 </div>

 {/* Recharts Area Chart */}
 <div className="h-[280px]">
 {trendChartData.length === 0 ? (
 <div className="flex h-full items-center justify-center border border-dashed border-border rounded-xl text-sm text-muted-foreground font-semibold">
 No historical data available. Waiting for data...
 </div>
 ) : (
 <ResponsiveContainer width="100%" height="100%">
 <AreaChart data={trendChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
 <defs>
 <linearGradient id="colorTrend" x1="0" y1="0" x2="0" y2="1">
 <stop offset="5%" stopColor={trendMeta.color} stopOpacity={0.2} />
 <stop offset="95%" stopColor={trendMeta.color} stopOpacity={0} />
 </linearGradient>
 </defs>
 <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
 <XAxis dataKey="time" stroke="#9ca3af" fontSize={11} style={{ fontFamily:"var(--)" }} />
 <YAxis
 stroke="#9ca3af"
 fontSize={11}
 style={{ fontFamily:"var(--)" }}
 label={{
 value: `${trendMeta.title} (${trendMeta.unit})`,
 angle: -90,
 position:"insideLeft",
 fill:"#9ca3af",
 style: { fontSize: 11, fontFamily:"var(--)" },
 }}
 />
 <Tooltip
 contentStyle={{ backgroundColor:"#14171d", borderColor:"#242b35", borderRadius:"8px" }}
 labelStyle={{ color:"#9ca3af", fontWeight:"bold" }}
 itemStyle={{ color:"#ffffff" }}
 formatter={(value: any) => [`${value} ${trendMeta.unit}`, trendMeta.title]}
 />
 <Area
 type="monotone"
 dataKey="value"
 stroke={trendMeta.color}
 fillOpacity={1}
 fill="url(#colorTrend)"
 strokeWidth={2.5}
 name={trendMeta.title}
 />
 </AreaChart>
 </ResponsiveContainer>
 )}
 </div>
 <div className="flex justify-between items-center text-xs text-muted-foreground border-t border-border/20 pt-3">
 <span className="font-medium">{trendMeta.def}</span>
 <span className="text-white font-bold">{trendMeta.expected}</span>
 </div>
 </div>

 {/* Diagnostics, Timeline & Explanations Grid */}
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
 {/* Left Column: Anomaly Explanation & Root Causes */}
 <div className="space-y-8">
 {/* ====================================================
 NEW SECTION 4 — ANOMALY EXPLANATION ENGINE
 ==================================================== */}
 <div className="bg-[#101216] border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <div className="flex justify-between items-center border-b border-border/40 pb-3">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2 text-white">
 <AlertOctagon className="h-5 w-5 text-primary" />
 Anomaly Explanation Engine
 </h3>
 <InfoTooltip
 title="Anomaly Explanation"
 definition="Translates technical sensor drifts into structural issues."
 why="Ensures technicians inspect exact parts instead of broad diagnostic steps."
 good="No active warnings (nominal condition)."
 bad="Flashing alert detailing problems and operational risks."
 />
 </div>

 {machine.active_anomaly ? (
 <div className="bg-rose-500/5 border border-rose-500/20 p-5 rounded-xl space-y-4 shadow-sm">
 <div className="flex justify-between items-center border-b border-rose-500/10 pb-3">
 <span className="font-bold text-rose-400 text-sm uppercase flex items-center gap-2">
 <span className="h-2.5 w-2.5 rounded-full bg-rose-500 animate-pulse"></span>
 Problem: {machine.active_anomaly.problem}
 </span>
 <span className="text-xs font-bold bg-rose-500/10 text-rose-400 px-3 py-1 rounded-full border border-rose-500/20 shadow-sm">
 Confidence: {Math.round(machine.active_anomaly.confidence * 100)}%
 </span>
 </div>

 <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-sm">
 <div>
 <span className="text-xs text-muted-foreground uppercase font-bold block mb-1.5">
 Possible Causes
 </span>
 <ul className="list-disc list-inside space-y-1 text-gray-300 font-semibold leading-relaxed">
 {machine.active_anomaly.possible_causes.map((c, idx) => (
 <li key={idx}>{c}</li>
 ))}
 </ul>
 </div>
 <div>
 <span className="text-xs text-muted-foreground uppercase font-bold block mb-1.5">
 Operational Impact
 </span>
 <p className="text-gray-300 leading-relaxed font-semibold">
 {machine.active_anomaly.operational_impact}
 </p>
 </div>
 </div>

 <div className="bg-rose-950/20 p-3.5 rounded-xl border border-rose-500/20 flex justify-between items-center text-sm font-semibold">
 <div>
 <span className="text-rose-400 uppercase text-[10px] block font-bold mb-0.5">
 Recommended Action
 </span>
 <span className="text-white">{machine.active_anomaly.recommended_action}</span>
 </div>
 </div>
 </div>
 ) : (
 <div className="bg-[#0d0f12] border border-dashed border-border p-8 rounded-xl text-center space-y-3 shadow-inner">
 <CheckCircle className="h-10 w-10 text-emerald-400 mx-auto" />
 <h4 className="text-sm font-bold text-white uppercase">
 All Telemetry Nominal
 </h4>
 <p className="text-xs text-muted-foreground">
 The machine is operating within expected limits. No anomalies detected.
 </p>
 </div>
 )}
 </div>

 {/* ====================================================
 NEW SECTION 5 — ROOT CAUSE INTELLIGENCE
 ==================================================== */}
 <div className="bg-[#101216] border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <div className="flex justify-between items-center border-b border-border/40 pb-3">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2 text-white">
 <ShieldAlert className="h-5 w-5 text-primary" />
 Root Cause Intelligence
 </h3>
 <InfoTooltip
 title="Root Cause Intelligence"
 definition="A ranked diagnostic assessment detailing component failure risks."
 why="Enables engineers to verify high-risk items sequentially."
 good="Low likelihood ratings across standard causes."
 bad="Highly concentrated confidence spikes (e.g. >70% cause probability)."
 />
 </div>

 <div className="space-y-4">
 {machine.root_cause_analysis.map((item, idx) => {
 const confPct = Math.round(item.confidence * 100);
 const progressColor =
 confPct >= 70 ?"bg-rose-500" : confPct >= 40 ?"bg-amber-500" :"bg-primary";
 return (
 <div key={idx} className="bg-[#0d0f12] p-4 border border-border/60 rounded-xl space-y-2.5 shadow-sm">
 <div className="flex justify-between items-center text-sm font-semibold">
 <span className="font-bold text-white">{item.cause}</span>
 <span className="font-bold text-primary">{confPct}% confidence</span>
 </div>
 <div className="h-2 bg-[#14171d] rounded-full overflow-hidden border border-border/20">
 <div
 className={`h-full rounded-full transition-all duration-300 ${progressColor}`}
 style={{ width: `${confPct}%` }}
 ></div>
 </div>
 <p className="text-xs text-muted-foreground leading-relaxed font-semibold">
 {item.explanation}
 </p>
 </div>
 );
 })}
 </div>
 </div>
 </div>

 {/* Right Column: Risk Timeline & Machine Explainability */}
 <div className="space-y-8">
 {/* ====================================================
 NEW SECTION 6 — RISK TIMELINE
 ==================================================== */}
 <div className="bg-[#101216] border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <div className="flex justify-between items-center border-b border-border/40 pb-3">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2 text-white">
 <History className="h-5 w-5 text-primary" />
 Risk Timeline
 </h3>
 <InfoTooltip
 title="Risk Timeline"
 definition="Chronological summary of warnings and faults."
 why="Analyzes whether faults are single events or recurring issues."
 good="Blank or rare single warning entries."
 bad="Persistent cluster of critical incidents."
 />
 </div>

 <div className="overflow-y-auto max-h-[350px] pr-2 space-y-4 text-xs font-semibold">
 {machine.risk_timeline.length === 0 ? (
 <div className="text-center py-12 text-sm text-muted-foreground border border-dashed border-border rounded-xl bg-[#0d0f12] shadow-inner">
 No alert records found. Historical telemetry is healthy.
 </div>
 ) : (
 <div className="relative border-l border-dashed border-border/60 pl-4 space-y-5 ml-2">
 {machine.risk_timeline.map((evt, idx) => {
 const badgeColor =
 evt.event_type ==="critical"
 ?"bg-rose-500"
 : evt.event_type ==="warning"
 ?"bg-amber-500"
 :"bg-sky-500";
 return (
 <div key={idx} className="relative">
 <span className={`absolute -left-[20.5px] top-1.5 h-1.5 w-1.5 rounded-full ${badgeColor}`}></span>
 <div className="flex justify-between items-center border-b border-border/20 pb-1.5">
 <span className="font-bold text-white uppercase text-[10px]">
 {evt.event_type}
 </span>
 <span className="text-[10px] text-gray-500 font-semibold">
 {new Date(evt.timestamp).toLocaleString()}
 </span>
 </div>
 <p className="text-xs text-gray-400 font-semibold leading-relaxed mt-1.5">
 {evt.description}
 </p>
 </div>
 );
 })}
 </div>
 )}
 </div>
 </div>

 {/* ====================================================
 NEW SECTION 8 — MACHINE EXPLAINABILITY PANEL
 ==================================================== */}
 <div className="bg-[#101216] border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <div className="flex justify-between items-center border-b border-border/40 pb-3">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2 text-white">
 <Info className="h-5 w-5 text-primary" />
 Machine Explainability Panel
 </h3>
 </div>
 <p className="text-xs text-muted-foreground leading-relaxed font-semibold">
 This card translates engineering diagnostic abbreviations and metrics into business explanations to aid non-engineers and plant managers.
 </p>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-semibold">
 <div className="bg-[#0d0f12] p-4 border border-border/40 rounded-xl shadow-sm">
 <span className="font-bold text-white block">Temperature</span>
 <span className="text-xs text-muted-foreground block mt-1.5 leading-relaxed font-medium">
 The raw thermodynamic heat levels measured at active motor casings and drive systems. Elevated levels indicate lack of grease or failing fans.
 </span>
 </div>
 <div className="bg-[#0d0f12] p-4 border border-border/40 rounded-xl shadow-sm">
 <span className="font-bold text-white block">Degradation</span>
 <span className="text-xs text-muted-foreground block mt-1.5 leading-relaxed font-medium">
 Estimated mechanical wear levels of component assemblies, computed dynamically by integrating structural friction and load coefficients.
 </span>
 </div>
 <div className="bg-[#0d0f12] p-4 border border-border/40 rounded-xl shadow-sm">
 <span className="font-bold text-white block">Availability</span>
 <span className="text-xs text-muted-foreground block mt-1.5 leading-relaxed font-medium">
 The percentage of standard operational runtime where the machine is online, validating production cycle outputs and telemetry broker handshakes.
 </span>
 </div>
 <div className="bg-[#0d0f12] p-4 border border-border/40 rounded-xl shadow-sm">
 <span className="font-bold text-white block">Anomaly Rate</span>
 <span className="text-xs text-muted-foreground block mt-1.5 leading-relaxed font-medium">
 The percentage share of telemetry records classified as abnormal by the AutoForge diagnostics rules layer, signifying potential safety risks.
 </span>
 </div>
 </div>
 </div>
 </div>
 </div>
 </div>
 );
}
