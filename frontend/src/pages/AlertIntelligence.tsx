import { useEffect, useState } from"react";
import { Link } from"react-router-dom";
import {
 AlertTriangle,
 CheckCircle,
 Eye,
 Info,
 Calendar,
 Layers,
 BarChart2,
 Clock,
} from"lucide-react";
import {
 BarChart,
 Bar,
 XAxis,
 YAxis,
 CartesianGrid,
 Tooltip,
 ResponsiveContainer,
} from"recharts";
import { analyticsService, type AnomalyDistributionRecord } from"../services/analyticsService";
import { diagnosticService, type DiagnosticRecord } from"../services/diagnosticService";

function InfoTooltip({ content }: { content: string }) {
 return (
 <div className="relative group inline-block ml-1.5 align-middle">
 <Info className="h-4 w-4 text-muted-foreground hover:text-white cursor-help transition-colors" />
 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-3.5 w-72 bg-[#14171d] border border-border text-xs text-gray-300 p-3 rounded-lg shadow-2xl hidden group-hover:block z-50 pointer-events-none leading-relaxed normal-case font-normal text-left">
 <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-[#14171d]"></div>
 {content}
 </div>
 </div>
 );
}

export default function AlertIntelligence() {
 const [diagnostics, setDiagnostics] = useState<DiagnosticRecord[]>([]);
 const [anomalyDistribution, setAnomalyDistribution] = useState<AnomalyDistributionRecord[]>([]);
 const [selectedDiagnostic, setSelectedDiagnostic] = useState<DiagnosticRecord | null>(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 useEffect(() => {
 async function fetchData() {
 try {
 const [diagData, analyticsData] = await Promise.all([
 diagnosticService.getDiagnostics(100),
 analyticsService.getAggregatedAnalytics()
 ]);
 setDiagnostics(diagData);
 setAnomalyDistribution(analyticsData.anomaly_distribution);
 if (diagData.length > 0) {
 setSelectedDiagnostic(diagData[0]);
 }
 } catch (err: any) {
 setError(err.message ||"Failed to load alert intelligence log");
 } finally {
 setLoading(false);
 }
 }
 fetchData();
 }, []);

 if (loading) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-gray-400">
 <div className="text-center space-y-3">
 <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto"></div>
 <p className="text-sm tracking-widest uppercase font-semibold">Analyzing Alarm Logs...</p>
 </div>
 </div>
 );
 }

 if (error) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-red-400 p-8">
 <div className="max-w-md text-center border border-red-500/20 bg-red-950/10 p-8 rounded-xl">
 <AlertTriangle className="h-10 w-10 mx-auto mb-3 text-red-500" />
 <h3 className="font-bold text-base mb-2">Log Analytics Error</h3>
 <p className="text-sm text-gray-400 mb-4">{error}</p>
 </div>
 </div>
 );
 }

 // Count alerts by confidence thresholds
 const criticalCount = diagnostics.filter((d) => d.confidence >= 0.8).length;
 const warningCount = diagnostics.filter((d) => d.confidence >= 0.6 && d.confidence < 0.8).length;

 // Chart data
 const chartData = anomalyDistribution.slice(0, 5).map((ad) => ({
 name: ad.anomaly_type.replace(/_/g,""),
 anomalies: ad.anomaly_count,
 }));

 return (
 <div className="p-8 space-y-8 bg-[#0d0f12] min-h-screen text-gray-200 overflow-y-auto">
 {/* Header Banner */}
 <div className="flex justify-between items-center border-b border-border pb-6">
 <div>
 <h1 className="text-3xl font-bold text-white">Alert Intelligence Center</h1>
 <p className="text-sm text-muted-foreground mt-1">
 Proactive Warning & Fault Diagnosis Engine
 </p>
 </div>
 </div>

 {/* Overview Analytics Bar */}
 <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-md">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs font-semibold text-muted-foreground uppercase">Unhealthy Events</span>
 <InfoTooltip content="The total number of diagnosed anomaly events and system threshold violations recorded." />
 </div>
 <p className="text-xs text-muted-foreground/80 mt-1">Chronological diagnostics signals.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-3xl font-bold text-white">{diagnostics.length}</span>
 <Clock className="h-6 w-6 text-primary" />
 </div>
 </div>

 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-md">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs font-semibold text-muted-foreground uppercase">Critical Diagnostics</span>
 <InfoTooltip content="Active diagnosed anomalies classified as High or Critical urgency (confidence score >= 80%)." />
 </div>
 <p className="text-xs text-muted-foreground/80 mt-1">Severe faults requiring immediate actions.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-3xl font-bold text-rose-500">{criticalCount}</span>
 <AlertTriangle className="h-6 w-6 text-rose-500 animate-pulse" />
 </div>
 </div>

 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-md">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs font-semibold text-muted-foreground uppercase">Warning Diagnostics</span>
 <InfoTooltip content="Active diagnosed anomalies classified as Medium status (confidence scores between 60% and 80%)." />
 </div>
 <p className="text-xs text-muted-foreground/80 mt-1">Mild deviations requiring operational monitoring.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-3xl font-bold text-amber-500">{warningCount}</span>
 <AlertTriangle className="h-6 w-6 text-amber-500" />
 </div>
 </div>

 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-md">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs font-semibold text-muted-foreground uppercase">Active Diagnosticians</span>
 <InfoTooltip content="Current analytical engines processing machine health in real-time." />
 </div>
 <p className="text-xs text-muted-foreground/80 mt-1">Athena query engine status.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-xl font-bold text-emerald-400">Athena Ingest</span>
 <CheckCircle className="h-6 w-6 text-emerald-500" />
 </div>
 </div>
 </div>

 {/* Main Split Layout */}
 <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
 {/* Left column: Alerts log */}
 <div className="bg-card border border-border p-6 rounded-xl lg:col-span-2 space-y-6 flex flex-col justify-between shadow-lg">
 <div className="flex justify-between items-center pb-3 border-b border-border">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2">
 <Layers className="h-5 w-5 text-primary" />
 Chronological Diagnostics List
 </h3>
 <span className="text-xs text-muted-foreground font-semibold">Latest 100 diagnostics</span>
 </div>

 <div className="overflow-y-auto max-h-[560px] space-y-3 pr-2 flex-1">
 {diagnostics.length === 0 ? (
 <div className="text-center py-24 text-base text-muted-foreground border border-dashed border-border rounded-xl bg-[#0d0f12]">
 No diagnostics available yet. The system is waiting for telemetry anomalies.
 </div>
 ) : (
 diagnostics.map((a) => {
 const confPercent = Math.round(a.confidence * 100);
 const label = confPercent >= 80 ?"Critical" : confPercent >= 60 ?"High" : confPercent >= 40 ?"Medium" :"Low";
 return (
 <div
 key={a.event_id}
 onClick={() => setSelectedDiagnostic(a)}
 className={`p-4 border rounded-xl transition cursor-pointer flex justify-between items-center ${selectedDiagnostic?.event_id === a.event_id ?"bg-[#1c222c] border-primary shadow-sm" :"bg-[#14171d] border-border hover:border-gray-500/40"}`}
 >
 <div className="space-y-1">
 <div className="flex items-center gap-2.5">
 <span className="font-bold text-white text-base">{a.machine_id}</span>
 <span className="text-xs uppercase font-semibold text-muted-foreground">
 {a.machine_type.replace(/_/g,"")}
 </span>
 </div>
 <p className="text-gray-300 text-sm font-semibold uppercase">
 {a.anomaly_type.replace(/_/g,"")}
 </p>
 </div>
 <div className="flex items-center gap-4 text-right">
 <div>
 <p className={`font-bold text-sm ${
 label ==="Critical" ?"text-rose-500 animate-pulse" :
 label ==="High" ?"text-rose-400" :
 label ==="Medium" ?"text-amber-400" :
"text-sky-400"
 }`}>
 {label} ({confPercent}%)
 </p>
 <p className="text-xs text-muted-foreground mt-0.5">
 {new Date(a.timestamp).toLocaleTimeString()}
 </p>
 </div>
 <Eye className="h-5 w-5 text-gray-400 hover:text-white" />
 </div>
 </div>
 );
 })
 )}
 </div>
 </div>

 {/* Right column: Split Details Drill-down Panel */}
 <div className="space-y-6">
 {/* Selected Diagnostic Details */}
 {selectedDiagnostic && (
 <div className="bg-card border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <h3 className="text-lg font-bold uppercase flex items-center gap-2 pb-3 border-b border-border">
 <Info className="h-5 w-5 text-primary" />
 Diagnostic Console
 </h3>
 <div className="space-y-5">
 <div className="grid grid-cols-2 gap-4 bg-[#0d0f12] p-4 rounded-xl border border-border/60">
 <div>
 <span className="text-xs text-muted-foreground uppercase font-bold">Machine</span>
 <p className="font-bold text-white text-base mt-1">{selectedDiagnostic.machine_id}</p>
 <span className="text-xs text-muted-foreground uppercase block mt-2.5 font-bold">Class</span>
 <p className="text-gray-300 text-xs font-semibold uppercase truncate mt-1">
 {selectedDiagnostic.machine_type.replace(/_/g,"")}
 </p>
 </div>
 <div>
 <span className="text-xs text-muted-foreground uppercase font-bold">Confidence</span>
 <p className={`font-bold text-base mt-1 ${
 selectedDiagnostic.confidence >= 0.8 ? 'text-rose-500' :
 selectedDiagnostic.confidence >= 0.6 ? 'text-amber-500' :
 'text-sky-400'
 }`}>
 {Math.round(selectedDiagnostic.confidence * 100)}%
 </p>
 <span className="text-xs text-muted-foreground uppercase block mt-2.5 font-bold">Severity</span>
 <p className="text-gray-400 text-xs mt-1 uppercase font-semibold">
 {selectedDiagnostic.confidence >= 0.8 ?"Critical" : selectedDiagnostic.confidence >= 0.6 ?"Warning" :"Minor"}
 </p>
 </div>
 </div>

 <div className="space-y-1.5">
 <span className="text-xs text-muted-foreground uppercase block font-bold">Alert Title</span>
 <p className="text-white bg-[#0d0f12] p-3 rounded-lg border border-border uppercase text-xs font-bold">
 {selectedDiagnostic.anomaly_type.replace(/_/g,"")}
 </p>
 </div>

 <div className="space-y-1.5">
 <span className="text-xs text-muted-foreground uppercase block font-bold">Evidence</span>
 <p className="text-amber-400 bg-[#0d0f12] p-3 rounded-lg border border-border/80 text-xs font-bold leading-relaxed">
 {selectedDiagnostic.evidence}
 </p>
 </div>

 <div className="space-y-1.5">
 <span className="text-xs text-muted-foreground uppercase block font-bold">Why was this triggered?</span>
 <p className="text-gray-300 bg-[#0d0f12] p-3.5 rounded-lg border border-border text-sm leading-relaxed">
 {selectedDiagnostic.explanation}
 </p>
 </div>

 <div className="space-y-1.5">
 <span className="text-xs text-muted-foreground uppercase block font-bold">Likely Causes</span>
 <div className="bg-[#0d0f12] p-3.5 rounded-lg border border-border space-y-2">
 {selectedDiagnostic.probable_causes.map((cause, idx) => (
 <div key={idx} className="flex justify-between items-center text-xs">
 <span className="text-gray-300 font-medium">{cause.split('(')[0].trim()}</span>
 <span className="text-primary font-bold">{cause.includes('(') ? cause.split('(')[1].replace(')', '') : ''}</span>
 </div>
 ))}
 </div>
 </div>

 <div className="space-y-1.5">
 <span className="text-xs text-muted-foreground uppercase block font-bold">Recommended Action</span>
 <div className="text-emerald-400 bg-[#0d0f12] p-3.5 rounded-lg border border-emerald-500/20 text-sm leading-relaxed font-semibold space-y-1.5">
 {selectedDiagnostic.recommendations.map((action, idx) => (
 <div key={idx} className="flex items-start gap-2">
 <span className="text-emerald-500 font-bold">•</span>
 <span>{action}</span>
 </div>
 ))}
 </div>
 </div>

 <div className="bg-[#0d0f12] p-3.5 rounded-lg border border-border text-xs leading-relaxed">
 <div className="flex items-center gap-1.5 text-muted-foreground mb-1 font-semibold">
 <Calendar className="h-4 w-4" />
 <span>TIMELOG RECORDED</span>
 </div>
 <span className="text-gray-300 font-medium">
 {new Date(selectedDiagnostic.timestamp).toLocaleString()}
 </span>
 </div>

 <div className="pt-2 flex gap-4">
 <Link
 to={`/machine/${selectedDiagnostic.machine_id}`}
 className="flex-1 text-center py-3 bg-primary text-white rounded-lg hover:bg-primary/95 hover:shadow-lg transition text-sm font-bold uppercase"
 >
 Open Digital Twin
 </Link>
 </div>
 </div>
 </div>
 )}

 {/* Alarm Distribution Chart */}
 <div className="bg-card border border-border p-6 rounded-xl space-y-4 shadow-lg">
 <h3 className="text-base font-bold uppercase flex items-center gap-2">
 <BarChart2 className="h-5 w-5 text-primary" />
 Categorized Alarm Volume
 </h3>
 <div className="h-[180px]">
 {chartData.length === 0 ? (
 <div className="flex h-full items-center justify-center border border-dashed border-border rounded-lg text-sm text-muted-foreground bg-[#0d0f12]">
 No data available yet.
 </div>
 ) : (
 <ResponsiveContainer width="100%" height="100%">
 <BarChart data={chartData} layout="vertical">
 <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
 <XAxis type="number" stroke="#9ca3af" fontSize={11} style={{ fontFamily: 'var(--)' }} />
 <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={10} style={{ fontFamily: 'var(--)' }} width={90} />
 <Tooltip contentStyle={{ backgroundColor:"#14171d", borderColor:"#242b35", borderRadius:"8px" }} />
 <Bar dataKey="anomalies" fill="#d97706" radius={[0, 4, 4, 0]} />
 </BarChart>
 </ResponsiveContainer>
 )}
 </div>
 </div>
 </div>
 </div>
 </div>
 );
}
