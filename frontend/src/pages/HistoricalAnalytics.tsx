import { useEffect, useState, useMemo } from"react";
import {
 TrendingUp,
 TrendingDown,
 AlertTriangle,
 Zap,
 BarChart2,
 Activity,
 Shield,
 Target,
 Wrench,
 CheckCircle2,
 Info,
 Minus,
 ChevronRight,
 ChevronDown,
 X,
} from"lucide-react";
import {
 AreaChart,
 Area,
 XAxis,
 YAxis,
 CartesianGrid,
 Tooltip,
 ResponsiveContainer,
 BarChart,
 Bar,
 Cell,
 Legend,
 LabelList,
} from"recharts";
import {
 analyticsService,
 type HourlyTrendRecord,
 type EnergyProfileRecord,
 type BusinessKPIResponse,
 type OperationalRecommendation,
 type AnomalyDistributionRecord,
 type TelemetryActivityResponse,
} from"../services/analyticsService";
import { diagnosticService, type RootCauseDistribution } from"../services/diagnosticService";

// ---------------------------------------------------------------------------
// Definition Types and Data
// ---------------------------------------------------------------------------

interface MetricDefinition {
 title: string;
 definition: string;
 calculation: string;
 indication: string;
 thresholds: {
 normal: string;
 warning: string;
 critical: string;
 };
}

const METRIC_DEFINITIONS: Record<string, MetricDefinition> = {
 factory_health: {
 title:"Factory Health Score",
 definition:"Percentage of machines currently operating within expected operational thresholds.",
 calculation:"(Healthy Machines / Total Machines) × 100",
 indication:"Overall structural health of the shop floor.",
 thresholds: {
 normal:"90% – 100% (Excellent)",
 warning:"75% – 90% (Acceptable / Monitor closely)",
 critical:"Below 75% (Immediate intervention required)",
 }
 },
 production_efficiency: {
 title:"Production Efficiency Score",
 definition:"Estimate of operational throughput based on fleet degradation levels and problem frequency.",
 calculation:"100 - (Average Fleet Degradation % × 0.6 + Problem Rate % × 0.4)",
 indication:"How close the plant is to operating at peak nominal capacity without friction.",
 thresholds: {
 normal:"85% – 100% (High efficiency)",
 warning:"70% – 85% (Friction present, check warning machines)",
 critical:"Below 70% (Severe speed or availability losses)",
 }
 },
 problem_rate: {
 title:"Overall Machine Problem Rate",
 definition:"The percentage of telemetry events classified as anomalies (out-of-bounds sensor readings).",
 calculation:"(Anomalous Telemetry Events / Total Telemetry Events) × 100",
 indication:"The frequency of sensor breaches and failure symptoms.",
 thresholds: {
 normal:"Below 5% (Healthy operation)",
 warning:"5% – 15% (Elevated issues, potential sensor drift or minor faults)",
 critical:"Above 15% (Systemic machine distress)",
 }
 },
 production_risk: {
 title:"Production Risk Score",
 definition:"A composite threat rating (0-100) combining critical machine status, degradation speed, and problem rates.",
 calculation:"Weighted index of active critical events, average degradation rate, and most affected machine severity.",
 indication:"Likelihood of unscheduled downtime or safety shutdowns in the next 24-48 hours.",
 thresholds: {
 normal:"0 – 30 (Low risk)",
 warning:"30 – 60 (Moderate risk, schedule inspections)",
 critical:"Above 60 (High risk of imminent failure or safety shutdown)",
 }
 },
 most_affected: {
 title:"Most Affected Machine",
 definition:"The specific machine ID experiencing the highest individual problem rate.",
 calculation:"Identifies max(anomaly_count / total_events) per machine ID.",
 indication:"The specific asset causing the most disruption or nearing failure.",
 thresholds: {
 normal:"Individual rate < 5%",
 warning:"Individual rate 5% – 20%",
 critical:"Individual rate > 20% (Prioritize for immediate service)",
 }
 },
 energy_leader: {
 title:"Energy Consumption Leader",
 definition:"The machine type drawing the highest aggregate electrical energy.",
 calculation:"Sum of power consumption across all machines of that type in the data lake (kWh).",
 indication:"Identifies where the majority of electrical utility costs are generated.",
 thresholds: {
 normal:"Within historical baseline for production volume",
 warning:"Spike of >15% above nominal baseline without increased output",
 critical:"Spike of >30% or continuous high draw indicating mechanical binding/friction",
 }
 }
};

interface RootCauseDetail {
 meaning: string;
 symptoms: string;
 likelyCauses: string;
 action: string;
}

const ROOT_CAUSE_DETAILS: Record<string, RootCauseDetail> = {
"Severe Bearing Wear": {
 meaning:"Mechanical bearings supporting rotating components have degraded due to friction or fatigue.",
 symptoms:"High frequency vibration (mm/s), elevated temperature readings, squealing or grinding noises.",
 likelyCauses:"Lubricant starvation, dirt/water contamination, or exceeding lifetime operating hours.",
 action:"Schedule machine shutdown, inspect bearing lubrication, and replace worn bearings immediately."
 },
"Spindle Shaft Misalignment": {
 meaning:"The rotation axis of the spindle motor is no longer perfectly aligned with the drive assembly.",
 symptoms:"Increased directional vibration, uneven workpiece precision, motor casing overheating.",
 likelyCauses:"Structural impact, loose mounting bolts, or thermal expansion mismatch.",
 action:"Halt high-precision work, perform laser alignment calibration, and torque mounting bolts."
 },
"Cooling System Failure": {
 meaning:"The fluid cooling loop has lost flow or heat transfer capacity.",
 symptoms:"Rapid, runaway temperature rise under normal load, coolant pressure drop, alarm triggers.",
 likelyCauses:"Pump impeller failure, coolant fluid blockage, or radiator fan motor burnout.",
 action:"Reduce motor load immediately, check coolant levels, inspect heat exchangers, and test pump motor."
 },
"Hydraulic Line Leakage": {
 meaning:"A loss of hydraulic fluid pressure due to a physical breach in seals, lines, or valve fittings.",
 symptoms:"Sluggish actuator response, drop in line pressure (PSI/bar), visible fluid pooling.",
 likelyCauses:"Seal dry-rot, pressure surges exceeding hose ratings, or physical hose abrasion.",
 action:"Depressurize the hydraulic system, identify the leaking hose/fitting, and replace the seals or hose."
 },
"Motor Coil Winding Short": {
 meaning:"Electrical insulation breakdown inside the motor windings causing current to bypass coils.",
 symptoms:"Sudden spike in power consumption (kW) at low RPM, breaker trips, thermal hot-spots.",
 likelyCauses:"Overloading/overheating history, moisture ingress, or aging insulation.",
 action:"Perform winding insulation resistance test (megger test) and replace motor or rewinding if shorted."
 },
"Mechanical Gear Binding": {
 meaning:"Interference in gear teeth mesh causing high friction resistance.",
 symptoms:"Sluggish start-up, elevated power draw (kW), gear casing vibration, metallic flakes in oil.",
 likelyCauses:"Broken gear tooth, misalignment of gear shafts, or metal debris contamination.",
 action:"Drain gear oil, inspect tooth contact pattern, clean casing of metal particles, and inspect gear alignment."
 }
};

// ---------------------------------------------------------------------------
// Shared UI Primitives
// ---------------------------------------------------------------------------

function InfoTooltip({ content }: { content: React.ReactNode }) {
 return (
 <div className="relative group inline-block ml-1.5 align-middle">
 <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-white cursor-pointer transition-colors" />
 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-72 bg-[#0d0f12] border border-border text-[11px] text-gray-300 p-3 rounded-lg shadow-2xl hidden group-hover:block z-50 pointer-events-none leading-relaxed normal-case font-normal text-left font-medium">
 <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-[#0d0f12]"></div>
 {content}
 </div>
 </div>
 );
}

function SectionHeader({
 question,
 title,
 icon: Icon,
 tooltip,
 insight,
 timeContext,
}: {
 question: string;
 title: string;
 icon: React.ElementType;
 tooltip: React.ReactNode;
 insight?: string;
 timeContext?: string;
}) {
 return (
 <div className="space-y-1">
 <div className="flex justify-between items-center gap-2">
 <span className="text-[10px] text-primary uppercase tracking-widest block font-semibold">
 {question}
 </span>
 {timeContext && (
 <span className="text-[9px] text-muted-foreground bg-[#0d0f12]/40 border border-border/50 px-1.5 py-0.2 rounded">
 {timeContext}
 </span>
 )}
 </div>
 <div className="flex items-start justify-between gap-2">
 <div className="flex items-center gap-2">
 <h3 className="text-sm font-semibold text-white flex items-center gap-2" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
 <Icon className="h-4 w-4 text-primary flex-shrink-0" />
 {title}
 </h3>
 <InfoTooltip content={tooltip} />
 </div>
 </div>
 {insight && (
 <p className="text-[11px] text-amber-400/90 leading-snug bg-amber-500/5 border border-amber-500/15 rounded px-3 py-2 mt-1">
 ⚡ {insight}
 </p>
 )}
 </div>
 );
}

// ---------------------------------------------------------------------------
// Metric Definition Modal
// ---------------------------------------------------------------------------

function MetricDefinitionModal({ isOpen, metricKey, onClose }: { isOpen: boolean; metricKey: string | null; onClose: () => void }) {
 if (!isOpen || !metricKey) return null;
 const def = METRIC_DEFINITIONS[metricKey];
 if (!def) return null;

 return (
 <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
 <div className="bg-[#11141a] border border-border rounded-xl p-6 max-w-md w-full space-y-4 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
 <button
 onClick={onClose}
 className="absolute top-4 right-4 text-muted-foreground hover:text-white transition-colors"
 >
 <X className="h-4 w-4" />
 </button>
 <div className="flex items-center gap-2 border-b border-border pb-3">
 <Info className="h-5 w-5 text-primary" />
 <h3 className="text-base font-bold text-white">{def.title}</h3>
 </div>
 <div className="space-y-3.5 text-xs text-gray-300">
 <div>
 <h4 className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">What is this metric?</h4>
 <p className="leading-relaxed">{def.definition}</p>
 </div>
 <div>
 <h4 className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">How is it calculated?</h4>
 <div className="bg-[#080a0d] border border-border rounded px-2.5 py-1.5 text-[10px] text-primary-foreground select-all">
 {def.calculation}
 </div>
 </div>
 <div>
 <h4 className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">What does it indicate?</h4>
 <p className="leading-relaxed">{def.indication}</p>
 </div>
 <div>
 <h4 className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">Target Health Thresholds</h4>
 <div className="space-y-1 mt-1.5 text-[10px]">
 <div className="flex justify-between border-b border-border/30 pb-0.5">
 <span className="text-emerald-400 font-semibold">Normal Range:</span>
 <span className="text-white">{def.thresholds.normal}</span>
 </div>
 <div className="flex justify-between border-b border-border/30 pb-0.5">
 <span className="text-amber-400 font-semibold">Warning Range:</span>
 <span className="text-white">{def.thresholds.warning}</span>
 </div>
 <div className="flex justify-between">
 <span className="text-red-400 font-semibold">Critical Range:</span>
 <span className="text-white">{def.thresholds.critical}</span>
 </div>
 </div>
 </div>
 </div>
 </div>
 </div>
 );
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

interface KPICardProps {
 label: string;
 value: string;
 sub?: string;
 trend?:"up" |"down" |"neutral";
 trendLabel?: string;
 color?: string;
 icon: React.ElementType;
 tooltip: React.ReactNode;
 pulse?: boolean;
 metricKey: string;
 onInfoClick: (key: string) => void;
}

function KPICard({
 label,
 value,
 sub,
 trend,
 trendLabel,
 color ="text-white",
 icon: Icon,
 tooltip,
 pulse,
 metricKey,
 onInfoClick,
}: KPICardProps) {
 const TrendIcon = trend ==="up" ? TrendingUp : trend ==="down" ? TrendingDown : Minus;
 const trendColor = trend ==="up" ?"text-emerald-400" : trend ==="down" ?"text-red-400" :"text-gray-500";

 return (
 <div className="bg-card border border-border rounded-lg p-4 flex flex-col justify-between hover:border-primary/30 transition-colors group relative">
 <div className="flex items-start justify-between">
 <div>
 <div className="flex items-center gap-1">
 <span className="text-[10px] text-muted-foreground uppercase">{label}</span>
 <button
 onClick={() => onInfoClick(metricKey)}
 className="text-muted-foreground hover:text-white cursor-pointer transition-colors p-0.5"
 title="Click to view metric formulas and health thresholds"
 >
 <Info className="h-3.5 w-3.5" />
 </button>
 <InfoTooltip content={tooltip} />
 </div>
 </div>
 <div className={`p-1.5 rounded bg-primary/10 ${pulse ?"animate-pulse" :""}`}>
 <Icon className="h-3.5 w-3.5 text-primary" />
 </div>
 </div>
 <div className="mt-3">
 <span className={`text-2xl font-bold ${color}`} style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
 {value}
 </span>
 {sub && <p className="text-[10px] text-muted-foreground mt-0.5 leading-snug">{sub}</p>}
 </div>
 {trendLabel && (
 <div className={`flex items-center gap-1 mt-2 ${trendColor} text-[10px] `}>
 <TrendIcon className="h-3 w-3" />
 <span>{trendLabel}</span>
 </div>
 )}
 </div>
 );
}

// ---------------------------------------------------------------------------
// Custom Tooltip for charts
// ---------------------------------------------------------------------------

function CustomTooltipContent({ active, payload, label }: any) {
 if (!active || !payload?.length) return null;
 return (
 <div className="bg-[#0d0f12] border border-border rounded-lg p-3 shadow-2xl text-[11px] min-w-[180px] space-y-1.5">
 <p className="text-muted-foreground border-b border-border/50 pb-1 text-[10px] truncate">{label}</p>
 {payload.map((entry: any, i: number) => {
 let displayVal = entry.value;
 const name = entry.name?.toLowerCase() ||"";
 if (typeof entry.value ==="number") {
 if (name.includes("rate") || name.includes("pct") || name.includes("share") || name.includes("confidence") || name.includes("severity")) {
 displayVal = `${entry.value.toFixed(1)}%`;
 } else if (name.includes("energy")) {
 displayVal = `${entry.value.toLocaleString()} kWh`;
 } else if (name.includes("power")) {
 displayVal = `${entry.value.toLocaleString()} kW`;
 } else if (name.includes("events") || name.includes("activity") || name.includes("healthy") || name.includes("warning") || name.includes("critical")) {
 displayVal = `${entry.value.toLocaleString()} events`;
 } else if (name.includes("problems") || name.includes("incidents") || name.includes("occurrences")) {
 displayVal = `${entry.value.toLocaleString()} incidents`;
 } else {
 displayVal = entry.value.toLocaleString();
 }
 }
 return (
 <div key={i} className="flex justify-between items-center gap-4">
 <span style={{ color: entry.color }} className="text-[10px]">{entry.name}</span>
 <span className="text-white font-semibold">{displayVal}</span>
 </div>
 );
 })}
 </div>
 );
}

// ---------------------------------------------------------------------------
// Insufficient data placeholder
// ---------------------------------------------------------------------------

function InsufficientData({ message ="No sufficient historical data yet. Additional telemetry collection required." }: { message?: string }) {
 return (
 <div className="flex h-full items-center justify-center border border-dashed border-border rounded-lg text-[11px] text-muted-foreground text-center px-6 bg-[#0d0f12]/50 py-12">
 <div>
 <Activity className="h-6 w-6 mx-auto mb-2 text-muted-foreground/40" />
 {message}
 </div>
 </div>
 );
}

// ---------------------------------------------------------------------------
// Priority Badge
// ---------------------------------------------------------------------------

function PriorityBadge({ priority }: { priority: string }) {
 const styles = {
 critical:"bg-red-500/10 text-red-400 border-red-500/20",
 warning:"bg-amber-500/10 text-amber-400 border-amber-500/20",
 info:"bg-blue-500/10 text-blue-400 border-blue-500/20",
 } as Record<string, string>;
 return (
 <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${styles[priority] || styles.info}`}>
 {priority}
 </span>
 );
}

// ---------------------------------------------------------------------------
// Confidence Score Interpretation
// ---------------------------------------------------------------------------

const getConfidenceInterpretation = (conf: number) => {
 const pct = conf * 100;
 if (pct < 40) {
 return {
 label:"Weak evidence",
 style:"text-red-400 bg-red-500/10 border-red-500/20",
 desc:"Telemetry signature does not fully match. Manual verification is recommended."
 };
 }
 if (pct < 70) {
 return {
 label:"Moderate evidence",
 style:"text-amber-400 bg-amber-500/10 border-amber-500/20",
 desc:"Key sensors show alignment with failure symptoms. Prioritize vibration/hardware inspection."
 };
 }
 return {
 label:"Strong evidence",
 style:"text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
 desc:"Highly matches known failure signatures. Take immediate corrective action."
 };
};

// ---------------------------------------------------------------------------
// Executive Operational Briefing Card
// ---------------------------------------------------------------------------

function ExecutiveSummary({
 kpis,
 recommendations,
 timeContext,
}: {
 kpis: BusinessKPIResponse | null;
 recommendations: OperationalRecommendation[];
 timeContext: string;
}) {
 const healthVal = kpis ? kpis.factory_health_score : 100;
 const status = healthVal >= 90 ?"Stable" : healthVal >= 75 ?"At Risk" :"Critical";
 const statusColor =
 healthVal >= 90
 ?"text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
 : healthVal >= 75
 ?"text-amber-400 bg-amber-500/10 border-emerald-500/20"
 :"text-red-400 bg-red-500/10 border-red-500/20";

 const mostAffected = kpis ? kpis.most_affected_machine_id ||"None" :"None";
 const riskScore = kpis ? kpis.production_risk_score : 0;
 const riskLevel = riskScore < 30 ?"Low" : riskScore < 60 ?"Moderate" :"High";
 const riskColor = riskScore < 30 ?"text-emerald-400" : riskScore < 60 ?"text-amber-400" :"text-red-400";

 const mostSignificantIssue = useMemo(() => {
 if (recommendations.length > 0) {
 const criticals = recommendations.filter((r) => r.priority ==="critical");
 if (criticals.length > 0) return criticals[0].recommendation;
 return recommendations[0].recommendation;
 }
 return"No active machine distress detected.";
 }, [recommendations]);

 const recommendedAction = useMemo(() => {
 if (recommendations.length > 0) {
 const criticals = recommendations.filter((r) => r.priority ==="critical");
 if (criticals.length > 0) {
 return `Schedule mechanical/electrical service for asset ${criticals[0].machine_id} immediately. Focus: ${criticals[0].reason}.`;
 }
 return `Schedule inspection for machine ${recommendations[0].machine_id} within 48 hours. Focus: ${recommendations[0].reason}.`;
 }
 return"Continue regular operational monitoring. Maintain standard sensor inspection interval.";
 }, [recommendations]);

 return (
 <div className="bg-card border border-border rounded-xl p-5 space-y-4 shadow-lg">
 <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-border pb-3 gap-3">
 <h2 className="text-sm font-bold text-white uppercase flex items-center gap-2">
 <Activity className="h-4 w-4 text-primary" />
 Executive Operational Briefing
 </h2>
 <span className="text-[10px] text-muted-foreground bg-[#0d0f12] border border-border px-2 py-0.5 rounded">
 {timeContext}
 </span>
 </div>
 <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
 <div className="lg:col-span-3 space-y-3">
 <p className="text-xs leading-relaxed text-gray-300">
 The factory is currently operating in a{""}
 <strong className={healthVal >= 90 ?"text-emerald-400 font-semibold" : healthVal >= 75 ?"text-amber-400 font-semibold" :"text-red-400 font-semibold"}>
 {status.toLowerCase()}
 </strong>{""}
 state with an overall health score of <strong className="text-white font-semibold">{healthVal.toFixed(1)}%</strong>. 
 The most significant issue identified on the shop floor is <span className="text-amber-300 font-medium">"{mostSignificantIssue}"</span>. 
 The asset showing the highest rate of anomaly events is <strong className="text-white font-semibold">{mostAffected}</strong>, while the composite production risk index is calculated as <strong className={riskColor}>{riskLevel.toUpperCase()}</strong>.
 </p>
 <div className="bg-primary/5 border border-primary/10 rounded-lg p-3 flex gap-2 items-start">
 <span className="text-[10px] text-primary uppercase font-bold mt-0.5 flex-shrink-0">
 Recommended Action Plan:
 </span>
 <p className="text-xs text-primary-foreground/90 leading-relaxed">
 {recommendedAction}
 </p>
 </div>
 </div>
 <div className="grid grid-cols-2 gap-3 lg:border-l lg:border-border lg:pl-6">
 <div className="space-y-1">
 <span className="text-[9px] uppercase text-muted-foreground block">Factory Health</span>
 <div className={`text-[11px] font-bold px-2.5 py-1 rounded border inline-block ${statusColor}`}>
 {healthVal.toFixed(0)}% {status}
 </div>
 </div>
 <div className="space-y-1">
 <span className="text-[9px] uppercase text-muted-foreground block">Production Risk</span>
 <div className={`text-xs font-bold ${riskColor}`}>
 {riskScore.toFixed(0)}/100 ({riskLevel})
 </div>
 </div>
 <div className="space-y-1">
 <span className="text-[9px] uppercase text-muted-foreground block">Most Distressed Asset</span>
 <div className="text-[11px] font-bold text-white bg-[#0d0f12] border border-border px-2.5 py-1 rounded inline-block">
 {mostAffected}
 </div>
 </div>
 <div className="space-y-1">
 <span className="text-[9px] uppercase text-muted-foreground block">Briefing Status</span>
 <div className="text-[10px] text-gray-300 leading-snug">
 Live updates via Athena
 </div>
 </div>
 </div>
 </div>
 </div>
 );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function HistoricalAnalytics() {
 const [trends, setTrends] = useState<HourlyTrendRecord[]>([]);
 const [energy, setEnergy] = useState<EnergyProfileRecord[]>([]);
 const [kpis, setKpis] = useState<BusinessKPIResponse | null>(null);
 const [recommendations, setRecommendations] = useState<OperationalRecommendation[]>([]);
 const [rootCauses, setRootCauses] = useState<RootCauseDistribution[]>([]);
 const [anomalyDist, setAnomalyDist] = useState<AnomalyDistributionRecord[]>([]);
 
 // Primary page loading states
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 // Redesigned Telemetry Activity state variables
 const [selectedWindow, setSelectedWindow] = useState<string>("24h");
 const [activityData, setActivityData] = useState<TelemetryActivityResponse | null>(null);
 const [activityLoading, setActivityLoading] = useState(true);
 const [activityError, setActivityError] = useState<string | null>(null);
 const [hasAutoSelected, setHasAutoSelected] = useState(false);
 
 // Interactive definitions modal state
 const [activeMetricDef, setActiveMetricDef] = useState<string | null>(null);
 
 // Expandable root causes table state
 const [expandedRootCauses, setExpandedRootCauses] = useState<Record<string, boolean>>({});

 // 1. Initial Load of secondary tables/KPIs
 useEffect(() => {
 async function fetchInitial() {
 try {
 const [trendsData, energyData, kpisData, recsData, rootData, aggData] = await Promise.all([
 analyticsService.getHourlyTrends(),
 analyticsService.getEnergyProfile(),
 analyticsService.getBusinessKPIs(),
 analyticsService.getRecommendations(),
 diagnosticService.getRootCauses(),
 analyticsService.getAggregatedAnalytics(),
 ]);
 setTrends(trendsData);
 setEnergy(energyData);
 setKpis(kpisData);
 setRecommendations(recsData);
 setRootCauses(rootData);
 setAnomalyDist(aggData.anomaly_distribution);
 } catch (err: any) {
 setError(err.message ||"Failed to load initial analytics data");
 } finally {
 setLoading(false);
 }
 }
 fetchInitial();
 }, []);

 // 2. Fetch Telemetry Activity data (fires on selectedWindow changes)
 useEffect(() => {
 async function fetchActivity() {
 setActivityLoading(true);
 try {
 const data = await analyticsService.getTelemetryActivity(selectedWindow);
 setActivityData(data);
 if (!hasAutoSelected && data.auto_suggested_window) {
 setSelectedWindow(data.auto_suggested_window);
 setHasAutoSelected(true);
 }
 } catch (err: any) {
 setActivityError(err.message ||"Failed to load telemetry activity");
 } finally {
 setActivityLoading(false);
 }
 }
 fetchActivity();
 }, [selectedWindow, hasAutoSelected]);

 // Overall page time context
 const timeContext = useMemo(() => {
 if (!trends.length) return"Last 24 Hours";
 const start = trends[0].time_label;
 const end = trends[trends.length - 1].time_label;
 return `Last 24 Hours (${start} to ${end})`;
 }, [trends]);

 // Energy insight calculation
 const energyInsight = useMemo(() => {
 if (!energy.length) return null;
 const totalEnergyFleet = energy.reduce((a, r) => a + r.total_energy, 0);
 const top = energy[0];
 const percentage = ((top.total_energy / (totalEnergyFleet || 1)) * 100).toFixed(0);
 const label = top.machine_type.replace(/_/g,"").replace(/\b\w/g, c => c.toUpperCase());
 
 return `${label} machines consumed ${top.total_energy.toLocaleString()} kWh during the selected period, accounting for approximately ${percentage}% of total factory energy usage. Spindles and hydraulic pumps make up the remaining share. Continuous monitoring of ${label} wear could yield the highest cost-reduction opportunities.`;
 }, [energy]);

 // Root cause insight calculation
 const rootCauseInsight = useMemo(() => {
 if (!rootCauses.length) return null;
 const top = rootCauses[0];
 const totalIncidents = rootCauses.reduce((a, r) => a + r.count, 0) || 1;
 const percentage = ((top.count / totalIncidents) * 100).toFixed(0);
 const confLabel = getConfidenceInterpretation(top.avg_confidence).label.toLowerCase();
 
 return `"${top.cause}" is the leading source of machine distress, accounting for {top.count} incidents (${percentage}% of total diagnosed cases) with ${confLabel} (${(top.avg_confidence * 100).toFixed(0)}% confidence). Prioritizing repair orders for this failure mode will yield the highest drop in production risk.`;
 }, [rootCauses]);

 const totalRootCauseCount = useMemo(
 () => rootCauses.reduce((a, r) => a + r.count, 0) || 1,
 [rootCauses]
 );

 const toggleRootCauseExpand = (cause: string) => {
 setExpandedRootCauses(prev => ({
 ...prev,
 [cause]: !prev[cause]
 }));
 };

 const ROOT_CAUSE_COLORS = ["#ef4444","#f59e0b","#3b82f6","#10b981","#8b5cf6","#06b6d4"];
 const ENERGY_COLORS = ["#3b82f6","#f59e0b","#10b981","#ef4444","#8b5cf6"];

 if (loading) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] min-h-screen">
 <div className="text-center space-y-3">
 <div className="relative">
 <div className="h-10 w-10 rounded-full border-2 border-primary/20 mx-auto" />
 <div className="h-10 w-10 rounded-full border-t-2 border-primary animate-spin absolute inset-0" />
 </div>
 <p className="text-xs tracking-widest uppercase text-muted-foreground">
 Compiling Manufacturing Briefing...
 </p>
 </div>
 </div>
 );
 }

 if (error) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-red-400 p-6 min-h-screen">
 <div className="max-w-md text-center border border-red-500/20 bg-red-950/10 p-6 rounded-lg">
 <AlertTriangle className="h-8 w-8 mx-auto mb-3 text-red-500" />
 <h3 className="font-semibold text-sm mb-1">Analytics Engine Offline</h3>
 <p className="text-gray-400 text-xs">{error}</p>
 </div>
 </div>
 );
 }

 const healthColor = kpis
 ? kpis.factory_health_score >= 90
 ?"text-emerald-400"
 : kpis.factory_health_score >= 75
 ?"text-amber-400"
 :"text-red-400"
 :"text-gray-400";

 const riskColor = kpis
 ? kpis.production_risk_score >= 60
 ?"text-red-400"
 : kpis.production_risk_score >= 30
 ?"text-amber-400"
 :"text-emerald-400"
 :"text-gray-400";



 return (
 <div
 className="p-8 space-y-8 bg-[#0d0f12] min-h-screen text-gray-200 overflow-y-auto"
 >
 {/* ------------------------------------------------------------------ */}
 {/* Page Header */}
 {/* ------------------------------------------------------------------ */}
 <div className="flex justify-between items-center border-b border-border pb-6">
 <div>
 <h1 className="text-3xl font-bold text-white flex items-center gap-2.5">
 <BarChart2 className="h-6 w-6 text-primary" />
 Manufacturing Intelligence Center
 </h1>
 <p className="text-sm text-muted-foreground mt-1 uppercase font-semibold">
 Executive Analytics & Decision Support Portal · Athena-powered
 </p>
 </div>
 <div className="flex items-center gap-2.5 bg-[#14171d] border border-border rounded-lg px-4 py-2 text-xs font-semibold shadow-sm">
 <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
 <span className="text-gray-300">Live Telemetry · Cost: &lt; $0.01 USD</span>
 </div>
 </div>

 {/* ------------------------------------------------------------------ */}
 {/* Executive Operational Briefing */}
 {/* ------------------------------------------------------------------ */}
 <ExecutiveSummary
 kpis={kpis}
 recommendations={recommendations}
 timeContext={timeContext}
 />

 {/* ------------------------------------------------------------------ */}
 {/* Business KPI Row */}
 {/* ------------------------------------------------------------------ */}
 {kpis && (
 <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
 <KPICard
 label="Factory Health Score"
 value={`${kpis.factory_health_score.toFixed(1)}%`}
 sub={`${kpis.healthy_count} normal · ${kpis.warning_count} warning · ${kpis.critical_count} critical`}
 trend={kpis.factory_health_score >= 90 ?"up" :"down"}
 trendLabel={kpis.factory_health_score >= 90 ?"Excellent" :"Needs attention"}
 color={healthColor}
 icon={Shield}
 metricKey="factory_health"
 onInfoClick={setActiveMetricDef}
 tooltip={
 <div className="space-y-1">
 <span className="font-semibold text-white">Factory Health Score</span>
 <p>Represents the ratio of healthy machines to distressed ones. Under 75% requires immediate engineer dispatch.</p>
 </div>
 }
 />
 <KPICard
 label="Production Efficiency"
 value={`${kpis.production_efficiency_score.toFixed(1)}%`}
 sub="Based on degradation metrics and problem frequency"
 trend={kpis.production_efficiency_score >= 85 ?"up" :"down"}
 trendLabel={kpis.production_efficiency_score >= 85 ?"High performance" :"Friction present"}
 color={kpis.production_efficiency_score >= 85 ?"text-emerald-400" :"text-amber-400"}
 icon={Target}
 metricKey="production_efficiency"
 onInfoClick={setActiveMetricDef}
 tooltip={
 <div className="space-y-1">
 <span className="font-semibold text-white">Production Efficiency</span>
 <p>Estimates relative throughput speed based on mechanical degradation and sensor anomalies.</p>
 </div>
 }
 />
 <KPICard
 label="Overall Machine Problem Rate"
 value={`${kpis.overall_anomaly_rate_pct.toFixed(1)}%`}
 sub="Percentage of events flagged as sensor anomalies"
 trend={kpis.overall_anomaly_rate_pct <= 5 ?"up" :"down"}
 trendLabel={kpis.overall_anomaly_rate_pct <= 5 ?"Optimal" :"Elevated Problems"}
 color={kpis.overall_anomaly_rate_pct <= 5 ?"text-emerald-400" : kpis.overall_anomaly_rate_pct <= 15 ?"text-amber-400" :"text-red-400"}
 icon={Activity}
 metricKey="problem_rate"
 onInfoClick={setActiveMetricDef}
 tooltip={
 <div className="space-y-1">
 <span className="font-semibold text-white">Problem Rate</span>
 <p>The share of telemetry events containing values outside nominal sensor ranges.</p>
 </div>
 }
 />
 <KPICard
 label="Production Risk Score"
 value={`${kpis.production_risk_score.toFixed(0)}/100`}
 sub="Threat ranking of active machine distress"
 trend={kpis.production_risk_score <= 30 ?"up" :"down"}
 trendLabel={kpis.production_risk_score >= 60 ?"CRITICAL RISK" : kpis.production_risk_score >= 30 ?"Moderate risk" :"Low risk"}
 color={riskColor}
 icon={AlertTriangle}
 pulse={kpis.production_risk_score >= 60}
 metricKey="production_risk"
 onInfoClick={setActiveMetricDef}
 tooltip={
 <div className="space-y-1">
 <span className="font-semibold text-white">Production Risk</span>
 <p>Threat metric calculating probability of unpredicted shutdown. Values above 60 indicate imminent failure risk.</p>
 </div>
 }
 />
 <KPICard
 label="Most Distressed Machine"
 value={kpis.most_affected_machine_id ??"None"}
 sub={kpis.most_affected_machine_type ? kpis.most_affected_machine_type.replace(/_/g,"") :"No anomalies"}
 trendLabel={kpis.most_affected_anomaly_rate > 0 ? `${kpis.most_affected_anomaly_rate.toFixed(1)}% problem rate` : undefined}
 trend={kpis.most_affected_anomaly_rate > 15 ?"down" :"neutral"}
 color={kpis.most_affected_anomaly_rate > 15 ?"text-red-400" :"text-amber-400"}
 icon={Wrench}
 metricKey="most_affected"
 onInfoClick={setActiveMetricDef}
 tooltip={
 <div className="space-y-1">
 <span className="font-semibold text-white">Most Distressed Machine</span>
 <p>The asset recording the highest error frequency. Immediate preventative inspection recommended.</p>
 </div>
 }
 />
 <KPICard
 label="Energy Consumption Leader"
 value={kpis.energy_leader_type ? kpis.energy_leader_type.replace(/_/g,"").replace(/\b\w/g, c => c.toUpperCase()) :"None"}
 sub={kpis.energy_leader_value > 0 ? `${kpis.energy_leader_value.toLocaleString()} kWh total` :"No energy records"}
 color="text-blue-400"
 icon={Zap}
 metricKey="energy_leader"
 onInfoClick={setActiveMetricDef}
 tooltip={
 <div className="space-y-1">
 <span className="font-semibold text-white">Energy Consumption Leader</span>
 <p>The asset class drawing the highest total utility power. Look for spikes indicating mechanical friction.</p>
 </div>
 }
 />
 </div>
 )}

 {/* ------------------------------------------------------------------ */}
 {/* Section: Telemetry Activity & Ingestion Health */}
 {/* ------------------------------------------------------------------ */}
 <div className="bg-card border border-border rounded-xl p-5 space-y-4 shadow-lg">
 <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-border pb-3 gap-3">
 <div>
 <h2 className="text-sm font-bold text-white uppercase flex items-center gap-2">
 <Activity className="h-4 w-4 text-primary" />
 Telemetry Activity & Ingestion Health
 </h2>
 <p className="text-[10px] text-muted-foreground">
 Active transmission rates and data pipeline verification
 </p>
 </div>
 
 <div className="flex bg-[#14171d] border border-border rounded p-0.5 text-[10px]">
 {["15m","1h","24h","7d"].map((win) => (
 <button
 key={win}
 onClick={() => setSelectedWindow(win)}
 className={`px-2.5 py-1 rounded transition cursor-pointer ${selectedWindow === win ?"bg-[#242b35] text-white font-bold" :"text-gray-400 hover:text-white"}`}
 >
 {win.toUpperCase()}
 </button>
 ))}
 </div>
 </div>

 {activityError ? (
 <div className="text-red-400 text-xs py-8 text-center border border-dashed border-red-500/20 rounded-lg">
 Failed to load activity statistics: {activityError}
 </div>
 ) : activityLoading && !activityData ? (
 <div className="flex h-[240px] items-center justify-center border border-dashed border-border rounded-lg bg-[#0d0f12]/50">
 <div className="text-center space-y-2">
 <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
 <p className="text-[10px] text-muted-foreground uppercase tracking-widest">Querying Data Lake...</p>
 </div>
 </div>
 ) : activityData ? (
 <>
 {/* Dynamic Progress indicator if data span is too low */}
 {activityData.collection_progress_pct < 100.0 && (
 <div className="bg-[#11141a] border border-dashed border-amber-500/20 rounded-lg p-4 space-y-2 text-xs text-amber-400 bg-amber-500/5">
 <div className="flex justify-between text-[10px]">
 <span>Data Ingestion Progress Baseline</span>
 <span>{activityData.collection_progress_pct}% complete</span>
 </div>
 <div className="w-full bg-[#0d0f12] h-2 rounded-full overflow-hidden border border-border/30">
 <div className="h-full bg-amber-500 rounded-full transition-all duration-500" style={{ width: `${activityData.collection_progress_pct}%` }}></div>
 </div>
 <p className="text-[10px] text-gray-400 leading-relaxed">
 Historical trend data is still being collected. Continue running the simulator to generate richer analytics. Estimated {activityData.estimated_time_remaining_minutes.toFixed(0)} minutes remaining until full 24h baseline.
 </p>
 </div>
 )}

 {/* KPI Cards Row */}
 <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
 {/* Card 1: Telemetry Events */}
 <div className="bg-[#0d0f12]/50 border border-border/60 p-3 rounded-lg space-y-1">
 <div className="flex justify-between items-center text-[9px] text-muted-foreground uppercase">
 <span>Telemetry Events</span>
 <InfoTooltip content="Total raw events ingested and processed in this period." />
 </div>
 <p className="text-lg font-bold text-white">{activityData.kpis.total_events.toLocaleString()} events</p>
 <span className="text-[9px] text-gray-400 block">Ingested packets</span>
 </div>

 {/* Card 2: Telemetry Rate */}
 <div className="bg-[#0d0f12]/50 border border-border/60 p-3 rounded-lg space-y-1">
 <div className="flex justify-between items-center text-[9px] text-muted-foreground uppercase">
 <span>Telemetry Rate</span>
 <InfoTooltip content="Average number of events processed per minute." />
 </div>
 <p className="text-lg font-bold text-white">{activityData.kpis.telemetry_rate_per_min} /min</p>
 <span className="text-[9px] text-gray-400 block">Avg system rate</span>
 </div>

 {/* Card 3: Peak Activity */}
 <div className="bg-[#0d0f12]/50 border border-border/60 p-3 rounded-lg space-y-1">
 <div className="flex justify-between items-center text-[9px] text-muted-foreground uppercase">
 <span>Peak Activity</span>
 <InfoTooltip content="Highest recorded single-bucket events rate normalized to events/minute." />
 </div>
 <p className="text-lg font-bold text-white">{activityData.kpis.peak_rate_per_min} /min</p>
 <span className="text-[9px] text-gray-400 block">Ingestion burst spike</span>
 </div>

 {/* Card 4: Anomaly Rate */}
 <div className="bg-[#0d0f12]/50 border border-border/60 p-3 rounded-lg space-y-1">
 <div className="flex justify-between items-center text-[9px] text-muted-foreground uppercase">
 <span>Anomaly Rate</span>
 <InfoTooltip content="Percentage of anomalous events identified in this window." />
 </div>
 <p className="text-lg font-bold text-red-400">{activityData.kpis.anomaly_rate_pct}%</p>
 <span className="text-[9px] text-gray-400 block">Invalid sensor signals</span>
 </div>

 {/* Card 5: Trend */}
 <div className="bg-[#0d0f12]/50 border border-border/60 p-3 rounded-lg space-y-1">
 <div className="flex justify-between items-center text-[9px] text-muted-foreground uppercase">
 <span>Volume Trend</span>
 <InfoTooltip content="Telemetry count compared with the preceding period of the same length." />
 </div>
 <div className="flex items-center gap-1">
 <span className={activityData.kpis.trend_pct >= 0 ?"text-emerald-400" :"text-red-400"}>
 {activityData.kpis.trend_pct >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
 </span>
 <p className="text-lg font-bold text-white">
 {activityData.kpis.trend_pct >= 0 ?"+" :""}{activityData.kpis.trend_pct}%
 </p>
 </div>
 <span className="text-[9px] text-gray-400 block">vs previous period</span>
 </div>
 </div>

 {/* Main Grid: Chart + breakdown */}
 <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
 {/* Stacked Area Chart */}
 <div className="lg:col-span-3 space-y-3">
 <div className="h-[240px]">
 <ResponsiveContainer width="100%" height="100%">
 <AreaChart data={activityData.series} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
 <defs>
 <linearGradient id="colorHealthy" x1="0" y1="0" x2="0" y2="1">
 <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
 <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
 </linearGradient>
 <linearGradient id="colorWarning" x1="0" y1="0" x2="0" y2="1">
 <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
 <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
 </linearGradient>
 <linearGradient id="colorCritical" x1="0" y1="0" x2="0" y2="1">
 <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
 <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
 </linearGradient>
 </defs>
 <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
 <XAxis dataKey="time_label" stroke="#4b5563" fontSize={9} tickLine={false} style={{ fontFamily:"IBM Plex Mono, monospace" }} />
 <YAxis stroke="#4b5563" fontSize={9} tickLine={false} style={{ fontFamily:"IBM Plex Mono, monospace" }} />
 <Tooltip content={<CustomTooltipContent />} />
 <Legend wrapperStyle={{ fontSize: 9, fontFamily:"IBM Plex Mono, monospace" }} iconType="circle" iconSize={6} />
 <Area type="monotone" dataKey="healthy_count" name="Healthy events" stroke="#10b981" fill="url(#colorHealthy)" strokeWidth={1.5} dot={false} stackId="activity" />
 <Area type="monotone" dataKey="warning_count" name="Warning events" stroke="#f59e0b" fill="url(#colorWarning)" strokeWidth={1.5} dot={false} stackId="activity" />
 <Area type="monotone" dataKey="critical_count" name="Anomalous events" stroke="#ef4444" fill="url(#colorCritical)" strokeWidth={1.5} dot={false} stackId="activity" />
 </AreaChart>
 </ResponsiveContainer>
 </div>

 {/* Activity Insights */}
 <div className="bg-[#14171d]/60 border border-border rounded-lg p-3.5 space-y-2">
 <span className="text-[10px] text-amber-400 uppercase font-semibold block">⚡ Factory Ingestion Insights</span>
 <ul className="list-none space-y-1 text-xs text-gray-300">
 {activityData.insights.map((ins, i) => (
 <li key={i} className="flex items-start gap-1.5 leading-relaxed">
 <span className="text-amber-400 font-bold">•</span>
 <span>{ins}</span>
 </li>
 ))}
 </ul>
 </div>
 </div>

 {/* Breakdown & Health column */}
 <div className="space-y-4">
 {/* Active Machine Breakdown */}
 <div className="bg-[#0d0f12]/30 border border-border rounded-lg p-3.5 space-y-3">
 <h3 className="text-xs font-semibold text-white uppercase">Top Active Machines</h3>
 {activityData.machine_breakdown.length === 0 ? (
 <p className="text-[10px] text-muted-foreground">No active assets registered in this window.</p>
 ) : (
 <div className="space-y-3">
 {activityData.machine_breakdown.map((m, idx) => (
 <div key={idx} className="space-y-1 text-xs">
 <div className="flex justify-between text-[11px] text-gray-300">
 <span className="font-medium">{m.machine_type}</span>
 <span className="text-muted-foreground font-semibold">{m.percentage}%</span>
 </div>
 <div className="w-full bg-[#11141a] h-1.5 rounded-full overflow-hidden border border-border/20">
 <div
 className="h-full rounded-full"
 style={{
 width: `${m.percentage}%`,
 backgroundColor: idx === 0 ?"#3b82f6" : idx === 1 ?"#f59e0b" : idx === 2 ?"#10b981" :"#8b5cf6"
 }}
 />
 </div>
 </div>
 ))}
 </div>
 )}
 </div>

 {/* Diagnostics Pipeline Health */}
 <div className="bg-[#0d0f12]/30 border border-border rounded-lg p-3.5 space-y-3">
 <div className="flex justify-between items-center">
 <h3 className="text-xs font-semibold text-white uppercase">Pipeline Health</h3>
 <span className="text-[9px] text-muted-foreground bg-[#0d0f12] px-1.5 py-0.5 rounded border border-border/50">
 Sync latency: {activityData.pipeline_health.freshness_seconds}s
 </span>
 </div>
 <div className="space-y-2 text-[10px]">
 {[
 { name:"Simulator", status: activityData.pipeline_health.simulator },
 { name:"Kinesis", status: activityData.pipeline_health.kinesis },
 { name:"Lambda", status: activityData.pipeline_health.lambda_validator },
 { name:"Glue ETL", status: activityData.pipeline_health.glue_etl },
 { name:"Athena", status: activityData.pipeline_health.athena_engine }
 ].map((comp, i) => {
 const colors = {
 active:"bg-emerald-500",
 streaming:"bg-emerald-500",
 processing:"bg-emerald-500",
 operational:"bg-emerald-500",
 queryable:"bg-emerald-500",
 idle:"bg-amber-500",
 warning:"bg-amber-500",
 inactive:"bg-gray-500",
 offline:"bg-gray-500"
 } as Record<string, string>;
 const dotColor = colors[comp.status] ||"bg-red-500";
 return (
 <div key={i} className="flex justify-between items-center border-b border-border/10 pb-1">
 <span className="text-gray-400">{comp.name}</span>
 <div className="flex items-center gap-1.5">
 <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
 <span className="text-white text-[9px] uppercase font-bold">{comp.status}</span>
 </div>
 </div>
 );
 })}
 </div>
 </div>
 </div>
 </div>
 </>
 ) : null}
 </div>

 {/* ------------------------------------------------------------------ */}
 {/* Fleet Health & Performance Analytics Grid */}
 {/* ------------------------------------------------------------------ */}
 <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
 {/* Chart 2: Fleet Health Status Over Time */}
 <div className="bg-card border border-border rounded-lg p-5 space-y-4">
 <SectionHeader
 question="How is overall fleet health trending?"
 title="Fleet Health Status Over Time"
 icon={Shield}
 timeContext={timeContext}
 tooltip={
 <div className="space-y-1 text-gray-300">
 <span className="font-semibold text-white block">Visual Explanation</span>
 <p>Shows the hourly breakdown of healthy, warning, and critical telemetry signals across all machines.</p>
 <p className="text-[10px] text-amber-400">A growing critical (red) or warning (yellow) band means systemic wear is rising on the shop floor, requiring immediate team briefing.</p>
 </div>
 }
 insight={
 trends.length > 0 
 ? `Healthy operations represented ${((trends.reduce((a, r) => a + r.healthy_count, 0) / (trends.reduce((a, r) => a + r.total_events, 0) || 1)) * 100).toFixed(1)}% of all fleet activity. Warning/critical events accounted for the rest, indicating active equipment stress.`
 : undefined
 }
 />
 
 <div className="grid grid-cols-3 gap-2 border border-border bg-[#0d0f12]/50 p-2.5 rounded text-[10px] text-gray-400">
 <div>
 <span className="font-semibold text-white">QUESTION:</span> How do we define warning vs. critical states?
 </div>
 <div>
 <span className="font-semibold text-white">ANSWER:</span> Warning indicates a parameter has crossed the normal limit. Critical means it exceeds safety bounds.
 </div>
 <div>
 <span className="font-semibold text-white">BUSINESS MEANING:</span> Shifting from reactive repairs to predictive tuning prevents costly unexpected shutdowns.
 </div>
 </div>

 <div className="h-[260px]">
 {trends.length < 2 ? (
 <InsufficientData />
 ) : (
 <ResponsiveContainer width="100%" height="100%">
 <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
 <defs>
 <linearGradient id="gradHealthy" x1="0" y1="0" x2="0" y2="1">
 <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
 <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
 </linearGradient>
 <linearGradient id="gradWarning" x1="0" y1="0" x2="0" y2="1">
 <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
 <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
 </linearGradient>
 <linearGradient id="gradCritical" x1="0" y1="0" x2="0" y2="1">
 <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
 <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
 </linearGradient>
 </defs>
 <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
 <XAxis
 dataKey="time_label"
 stroke="#4b5563"
 fontSize={9}
 tickLine={false}
 style={{ fontFamily:"IBM Plex Mono, monospace" }}
 tickFormatter={(v) => v.slice(-5)}
 interval="preserveStartEnd"
 />
 <YAxis stroke="#4b5563" fontSize={9} tickLine={false} style={{ fontFamily:"IBM Plex Mono, monospace" }} />
 <Tooltip content={<CustomTooltipContent />} />
 <Legend
 wrapperStyle={{ fontSize: 10, fontFamily:"IBM Plex Mono, monospace" }}
 iconType="circle"
 iconSize={6}
 />
 <Area type="monotone" dataKey="healthy_count" name="Healthy (events)" stroke="#10b981" fill="url(#gradHealthy)" strokeWidth={1.5} dot={false} stackId="health" />
 <Area type="monotone" dataKey="warning_count" name="Warning (events)" stroke="#f59e0b" fill="url(#gradWarning)" strokeWidth={1.5} dot={false} stackId="health" />
 <Area type="monotone" dataKey="critical_count" name="Critical (events)" stroke="#ef4444" fill="url(#gradCritical)" strokeWidth={1.5} dot={false} stackId="health" />
 </AreaChart>
 </ResponsiveContainer>
 )}
 </div>
 </div>

 {/* Chart 3: Energy Consumption by Machine Type */}
 <div className="bg-card border border-border rounded-lg p-5 space-y-4">
 <SectionHeader
 question="Which machine types consume the most energy?"
 title="Energy Consumption by Machine Type"
 icon={Zap}
 timeContext={timeContext}
 tooltip={
 <div className="space-y-1 text-gray-300">
 <span className="font-semibold text-white block">Visual Explanation</span>
 <p>Aggregates energy consumption metrics (power_consumption + energy_usage) from the Athena database, grouped by equipment class.</p>
 <p className="text-[10px] text-amber-400">Identifies the highest electrical loads on the shop floor. Unexplained rises in energy draw suggest mechanical binding or friction.</p>
 </div>
 }
 insight={energyInsight ?? undefined}
 />
 
 <div className="grid grid-cols-3 gap-2 border border-border bg-[#0d0f12]/50 p-2.5 rounded text-[10px] text-gray-400">
 <div>
 <span className="font-semibold text-white">QUESTION:</span> Why does energy drawing vary?
 </div>
 <div>
 <span className="font-semibold text-white">ANSWER:</span> Industrial turbines and CNC spindle motors draw significantly more power than pneumatic systems.
 </div>
 <div>
 <span className="font-semibold text-white">BUSINESS MEANING:</span> Tracking energy draw allows spotting inefficiencies and predicting motor binding before failure.
 </div>
 </div>

 <div className="h-[260px]">
 {energy.length === 0 ? (
 <InsufficientData />
 ) : (
 <ResponsiveContainer width="100%" height="100%">
 <BarChart
 data={energy}
 layout="vertical"
 margin={{ top: 5, right: 50, left: 10, bottom: 5 }}
 >
 <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" horizontal={false} />
 <XAxis
 type="number"
 stroke="#4b5563"
 fontSize={9}
 tickLine={false}
 style={{ fontFamily:"IBM Plex Mono, monospace" }}
 tickFormatter={(v) => `${v.toLocaleString()} kWh`}
 />
 <YAxis
 type="category"
 dataKey="machine_type"
 stroke="#4b5563"
 fontSize={9}
 tickLine={false}
 width={90}
 style={{ fontFamily:"IBM Plex Mono, monospace" }}
 tickFormatter={(v) => v.replace(/_/g,"")}
 />
 <Tooltip content={<CustomTooltipContent />} />
 <Bar dataKey="total_energy" name="Total Energy (kWh)" radius={[0, 4, 4, 0]}>
 {energy.map((_, index) => (
 <Cell key={index} fill={ENERGY_COLORS[index % ENERGY_COLORS.length]} fillOpacity={0.85} />
 ))}
 <LabelList
 dataKey="total_energy"
 position="right"
 style={{ fill:"#9ca3af", fontSize: 9, fontFamily:"IBM Plex Mono, monospace" }}
 formatter={(v: any) => typeof v ==="number" ? `${v.toLocaleString()} kWh` : v}
 />
 </Bar>
 </BarChart>
 </ResponsiveContainer>
 )}
 </div>
 </div>
 </div>

 {/* ------------------------------------------------------------------ */}
 {/* Causes & Distribution Analytics Grid */}
 {/* ------------------------------------------------------------------ */}
 <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
 {/* Chart 4: Most Common Causes of Machine Problems */}
 <div className="bg-card border border-border rounded-lg p-5 space-y-4">
 <SectionHeader
 question="What are the most common causes of machine problems?"
 title="Most Common Causes of Machine Problems"
 icon={Wrench}
 timeContext={timeContext}
 tooltip={
 <div className="space-y-1 text-gray-300">
 <span className="font-semibold text-white block">Visual Explanation</span>
 <p>Diagnostic distributions identifying potential root causes compiled from anomalous machine sensor events.</p>
 <p className="text-[10px] text-amber-400">Enables maintenance managers to understand what physical components are wearing out most frequently across the fleet.</p>
 </div>
 }
 insight={rootCauseInsight ?? undefined}
 />
 
 <div className="grid grid-cols-3 gap-2 border border-border bg-[#0d0f12]/50 p-2.5 rounded text-[10px] text-gray-400">
 <div>
 <span className="font-semibold text-white">QUESTION:</span> How are causes diagnosed?
 </div>
 <div>
 <span className="font-semibold text-white">ANSWER:</span> Through rules matching specific patterns of temperature, pressure, vibration, and energy.
 </div>
 <div>
 <span className="font-semibold text-white">BUSINESS MEANING:</span> Knowing the leading causes helps adjust preventive maintenance intervals for seals, bearings, and shafts.
 </div>
 </div>

 <div className="h-[240px]">
 {rootCauses.length === 0 ? (
 <InsufficientData />
 ) : (
 <ResponsiveContainer width="100%" height="100%">
 <BarChart
 data={rootCauses.slice(0, 7)}
 layout="vertical"
 margin={{ top: 5, right: 50, left: 10, bottom: 5 }}
 >
 <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" horizontal={false} />
 <XAxis type="number" stroke="#4b5563" fontSize={9} tickLine={false} style={{ fontFamily:"IBM Plex Mono, monospace" }} tickFormatter={(v) => `${v.toLocaleString()} incidents`} />
 <YAxis
 type="category"
 dataKey="cause"
 stroke="#4b5563"
 fontSize={8}
 tickLine={false}
 width={110}
 style={{ fontFamily:"IBM Plex Mono, monospace" }}
 tickFormatter={(v: string) => v.length > 18 ? v.slice(0, 18) +"…" : v}
 />
 <Tooltip content={<CustomTooltipContent />} />
 <Bar dataKey="count" name="Occurrences (incidents)" radius={[0, 4, 4, 0]}>
 {rootCauses.slice(0, 7).map((_, index) => (
 <Cell key={index} fill={ROOT_CAUSE_COLORS[index % ROOT_CAUSE_COLORS.length]} fillOpacity={0.85} />
 ))}
 <LabelList
 dataKey="count"
 position="right"
 style={{ fill:"#9ca3af", fontSize: 9, fontFamily:"IBM Plex Mono, monospace" }}
 formatter={(v: any) => typeof v ==="number" ? `${v.toLocaleString()} incidents` : v}
 />
 </Bar>
 </BarChart>
 </ResponsiveContainer>
 )}
 </div>
 </div>

 {/* Chart 5: Types of Machine Problems by Machine Type */}
 <div className="bg-card border border-border rounded-lg p-5 space-y-4">
 <SectionHeader
 question="Which machine types experience the most problems?"
 title="Types of Machine Problems by Machine Type"
 icon={AlertTriangle}
 timeContext={timeContext}
 tooltip={
 <div className="space-y-1 text-gray-300">
 <span className="font-semibold text-white block">Visual Explanation</span>
 <p>A granular matrix breakdown of specific failure types grouped by machine class.</p>
 <p className="text-[10px] text-amber-400">Helps allocate maintenance team skillsets and target spare parts inventory.</p>
 </div>
 }
 />
 <div className="overflow-y-auto max-h-[295px]">
 {anomalyDist.length === 0 ? (
 <InsufficientData message="No anomaly data available yet. Telemetry collection is in progress." />
 ) : (
 <table className="w-full text-left text-[11px]">
 <thead className="bg-[#0d0f12] text-muted-foreground border-b border-border text-[9px] uppercase sticky top-0 z-10">
 <tr>
 <th className="p-2.5">Problem Type</th>
 <th className="p-2.5">Machine Class</th>
 <th className="p-2.5 text-right">Occurrences (incidents)</th>
 <th className="p-2.5 text-right">Severity (%)</th>
 <th className="p-2.5 text-center">Status</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-border">
 {anomalyDist.map((ad, i) => {
 const sev = ad.avg_anomaly_severity;
 const sevColor = sev >= 0.7 ?"text-red-400" : sev >= 0.4 ?"text-amber-400" :"text-emerald-400";
 const sevLabel = sev >= 0.7 ?"CRITICAL" : sev >= 0.4 ?"WARNING" :"NOMINAL";
 const sevBg = sev >= 0.7 ?"bg-red-500/10 border-red-500/20 text-red-400" : sev >= 0.4 ?"bg-amber-500/10 border-amber-500/20 text-amber-400" :"bg-emerald-500/10 border-emerald-500/20 text-emerald-400";
 return (
 <tr key={i} className="hover:bg-[#14171d]/60 transition-colors">
 <td className="p-2.5 font-semibold text-white uppercase text-[10px]">
 {ad.anomaly_type.replace(/_/g,"")}
 </td>
 <td className="p-2.5 text-gray-400 uppercase text-[9px]">
 {ad.machine_type.replace(/_/g,"")}
 </td>
 <td className="p-2.5 text-right font-bold text-red-400">{ad.anomaly_count.toLocaleString()}</td>
 <td className={`p-2.5 text-right font-bold ${sevColor}`}>
 {(sev * 100).toFixed(1)}%
 </td>
 <td className="p-2.5 text-center">
 <span className={`text-[8px] font-bold px-1.5 py-0.2 rounded border ${sevBg}`}>
 {sevLabel}
 </span>
 </td>
 </tr>
 );
 })}
 </tbody>
 </table>
 )}
 </div>
 </div>
 </div>

 {/* ------------------------------------------------------------------ */}
 {/* Root Cause Details Expandable Table */}
 {/* ------------------------------------------------------------------ */}
 {rootCauses.length > 0 && (
 <div className="bg-card border border-border rounded-lg p-5 space-y-4">
 <SectionHeader
 question="Why are problems occurring — machine problem explanations"
 title="Machine Problem Explanations & Actions"
 icon={Wrench}
 timeContext={timeContext}
 tooltip={
 <div className="space-y-1 text-gray-300">
 <span className="font-semibold text-white block">Visual Explanation</span>
 <p>Lists root causes diagnosed by the rules engine. Confidence displays strength of evidence matching the rule signature.</p>
 <p className="text-[10px] text-amber-400">⚡ Click on any row to expand complete Meanings, Symptoms, Likely Causes, and Actions.</p>
 </div>
 }
 />
 
 <div className="overflow-x-auto">
 <table className="w-full text-left text-xs">
 <thead className="bg-[#0d0f12] text-muted-foreground border-b border-border text-[10px]">
 <tr>
 <th className="p-3">Status</th>
 <th className="p-3">Cause / Problem</th>
 <th className="p-3 text-right">Count (incidents)</th>
 <th className="p-3 text-right">Fleet Share (%)</th>
 <th className="p-3 text-right">Diagnostic Confidence</th>
 <th className="p-3 text-right">Actions</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-border">
 {rootCauses.map((rc, i) => {
 const share = ((rc.count / totalRootCauseCount) * 100).toFixed(1);
 const color = ROOT_CAUSE_COLORS[i % ROOT_CAUSE_COLORS.length];
 
 // Root Cause Details mapping
 const details: RootCauseDetail = Object.entries(ROOT_CAUSE_DETAILS).find(([k]) =>
 rc.cause.toLowerCase().includes(k.toLowerCase())
 )?.[1] || {
 meaning:"Unclassified diagnostic pattern identified by telemetry thresholds.",
 symptoms:"Sensor values exceeding standard thresholds.",
 likelyCauses:"Sensor calibration drift or minor component wear.",
 action:"Verify sensor operation, clear fault, and review recent maintenance reports."
 };

 const isExpanded = !!expandedRootCauses[rc.cause];
 const confInfo = getConfidenceInterpretation(rc.avg_confidence);

 return (
 <tbody key={`body-${i}`} className="border-b border-border/40">
 <tr 
 className="hover:bg-[#14171d]/60 transition-colors cursor-pointer"
 onClick={() => toggleRootCauseExpand(rc.cause)}
 >
 <td className="p-3">
 <button className="text-muted-foreground hover:text-white transition-colors cursor-pointer">
 <ChevronDown className={`h-4 w-4 transform transition-transform ${isExpanded ?"rotate-180" :""}`} />
 </button>
 </td>
 <td className="p-3">
 <div className="flex items-center gap-2">
 <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: color }} />
 <span className="font-semibold text-white text-[11px]">{rc.cause}</span>
 </div>
 </td>
 <td className="p-3 text-right font-bold" style={{ color }}>{rc.count.toLocaleString()} incidents</td>
 <td className="p-3 text-right">
 <div className="flex items-center justify-end gap-2">
 <div className="w-16 h-1.5 bg-border rounded-full overflow-hidden">
 <div className="h-full rounded-full" style={{ width: `${share}%`, background: color }} />
 </div>
 <span className="text-[10px] text-gray-300">{share}%</span>
 </div>
 </td>
 <td className="p-3 text-right">
 <div className="flex flex-col items-end">
 <span className="text-[10px] font-bold text-white">{(rc.avg_confidence * 100).toFixed(0)}%</span>
 <span className={`text-[8px] font-bold px-1.5 py-0.2 rounded mt-0.5 border ${confInfo.style}`} title={confInfo.desc}>
 {confInfo.label}
 </span>
 </div>
 </td>
 <td className="p-3 text-right">
 <span className="text-[10px] text-primary hover:underline">
 {isExpanded ?"Hide Details" :"View Details"}
 </span>
 </td>
 </tr>
 {isExpanded && (
 <tr className="bg-[#11141a]/60">
 <td colSpan={6} className="p-4">
 <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
 <div className="space-y-1">
 <span className="text-[9px] uppercase text-muted-foreground block font-bold">Meaning</span>
 <p className="text-gray-200 leading-relaxed text-[11px]">{details.meaning}</p>
 </div>
 <div className="space-y-1">
 <span className="text-[9px] uppercase text-muted-foreground block font-bold">Symptoms</span>
 <p className="text-gray-200 leading-relaxed text-[11px]">{details.symptoms}</p>
 </div>
 <div className="space-y-1">
 <span className="text-[9px] uppercase text-muted-foreground block font-bold">Likely Causes</span>
 <p className="text-gray-200 leading-relaxed text-[11px]">{details.likelyCauses}</p>
 </div>
 <div className="space-y-1 bg-primary/5 border border-primary/10 rounded-lg p-2.5 animate-in fade-in duration-200">
 <span className="text-[9px] uppercase text-primary block font-bold">Recommended Action</span>
 <p className="text-primary-foreground/90 leading-relaxed text-[11px] font-medium">{details.action}</p>
 </div>
 </div>
 </td>
 </tr>
 )}
 </tbody>
 );
 })}
 </tbody>
 </table>
 </div>
 </div>
 )}

 {/* ------------------------------------------------------------------ */}
 {/* Recommended Actions for Operations Team */}
 {/* ------------------------------------------------------------------ */}
 <div className="bg-card border border-border rounded-lg p-5 space-y-4">
 <SectionHeader
 question="What actions should the operations team take right now?"
 title="Recommended Actions for Operations Team"
 icon={CheckCircle2}
 timeContext={timeContext}
 tooltip={
 <div className="space-y-1 text-gray-300">
 <span className="font-semibold text-white block">Visual Explanation</span>
 <p>Actionable, prioritized directives generated dynamically based on active machine warnings, degradation speed, and sensor anomalies.</p>
 <p className="text-[10px] text-amber-400">Purely threshold-driven rules designed to provide plant engineers with clear targets.</p>
 </div>
 }
 />
 {recommendations.length === 0 ? (
 <div className="text-center py-8 text-xs text-muted-foreground border border-dashed border-border rounded-lg">
 <CheckCircle2 className="h-6 w-6 mx-auto mb-2 text-emerald-500/50" />
 No critical recommendations at this time. All machines appear to be operating within nominal bounds.
 </div>
 ) : (
 <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
 {recommendations.map((rec, i) => (
 <div
 key={i}
 className={`rounded-lg border p-4 space-y-2 transition-colors ${
 rec.priority ==="critical"
 ?"border-red-500/20 bg-red-950/10 hover:border-red-500/35"
 : rec.priority ==="warning"
 ?"border-amber-500/20 bg-amber-950/10 hover:border-amber-500/35"
 :"border-blue-500/15 bg-blue-950/5 hover:border-blue-500/25"
 }`}
 >
 <div className="flex items-start justify-between gap-2">
 <div className="flex items-center gap-2">
 <PriorityBadge priority={rec.priority} />
 {rec.machine_id && (
 <span className="text-[10px] text-muted-foreground">{rec.machine_id}</span>
 )}
 </div>
 {rec.metric_value !== null && rec.metric_name && (
 <span className="text-[9px] text-muted-foreground bg-[#0d0f12] px-1.5 py-0.5 rounded border border-border flex-shrink-0">
 {rec.metric_name.replace(/_/g,"")}: {rec.metric_value.toFixed(1)} {
 rec.metric_name.toLowerCase().includes("temp") ?"°C" :
 rec.metric_name.toLowerCase().includes("press") ?"bar" :
 rec.metric_name.toLowerCase().includes("rpm") ?"revolutions/minute" :
 rec.metric_name.toLowerCase().includes("vib") ?"mm/s" :
"%"
 }
 </span>
 )}
 </div>
 <p className="text-[12px] text-white leading-snug font-medium">
 {rec.recommendation}
 </p>
 <div className="flex items-start gap-1.5 text-[10px] text-muted-foreground">
 <ChevronRight className="h-3 w-3 flex-shrink-0 mt-0.5 text-muted-foreground/50" />
 <span className="leading-snug">{rec.reason}</span>
 </div>
 </div>
 ))}
 </div>
 )}
 </div>

 {/* ------------------------------------------------------------------ */}
 {/* Metric Dictionary Definition Modal */}
 {/* ------------------------------------------------------------------ */}
 <MetricDefinitionModal
 isOpen={activeMetricDef !== null}
 metricKey={activeMetricDef}
 onClose={() => setActiveMetricDef(null)}
 />
 </div>
 );
}
