import { useQuery } from "@tanstack/react-query";
import { Link } from"react-router-dom";
import {
 Activity,
 AlertTriangle,
 CheckCircle,
 Cpu,
 TrendingUp,
 Info,
 Database,
 RefreshCw,
} from"lucide-react";
import {
 XAxis,
 YAxis,
 Tooltip,
 ResponsiveContainer,
 BarChart,
 Bar,
 Cell,
 LabelList,
} from"recharts";
import { analyticsService } from "../services/analyticsService";
import { machineService } from "../services/machineService";
import { diagnosticService } from "../services/diagnosticService";

// Human-friendly structured tooltips
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
 <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-white cursor-help transition-colors" />
 <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-72 bg-[#14171d] border border-border text-[11px] text-gray-300 p-3 rounded shadow-2xl hidden group-hover:block z-50 pointer-events-none leading-relaxed normal-case font-normal text-left">
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

export default function ExecutiveDashboard() {
  const { data: summary, isLoading: loadingSummary, error: errSummary } = useQuery({
    queryKey: ['factorySummary'],
    queryFn: () => analyticsService.getFactorySummary(),
  });

  const { data: diagnostics = [], isLoading: loadingDiag } = useQuery({
    queryKey: ['diagnostics'],
    queryFn: () => diagnosticService.getDiagnostics(8),
  });

  const { data: machines = [], isLoading: loadingMachines } = useQuery({
    queryKey: ['machines'],
    queryFn: () => machineService.getMachines(),
  });

  const { data: histData, isLoading: loadingHist } = useQuery({
    queryKey: ['aggregatedAnalytics'],
    queryFn: () => analyticsService.getAggregatedAnalytics(),
  });

  const anomalies = histData?.anomaly_distribution || [];
  const loading = loadingSummary || loadingDiag || loadingMachines || loadingHist;
  const error = errSummary ? "Failed to retrieve dashboard analytics" : null;

  // Real-Time Ops Center — REST polling replaces WebSocket
  const { data: pipelineMetrics } = useQuery({
    queryKey: ['pipelineMetrics'],
    queryFn: () => analyticsService.getPipelineMetrics(),
    refetchInterval: 10000,
    staleTime: 8000,
  });

  if (loading) {
    return (
      <div className="p-8 space-y-8 bg-[#0d0f12] min-h-screen text-gray-200">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-border pb-6 gap-6">
          <div className="space-y-3">
            <div className="h-8 w-64 bg-[#14171d] animate-pulse rounded" />
            <div className="h-4 w-96 bg-[#14171d] animate-pulse rounded" />
          </div>
          <div className="h-10 w-48 bg-[#14171d] animate-pulse rounded-lg" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="h-32 bg-[#14171d] animate-pulse rounded border border-border/50" />)}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 bg-[#14171d] animate-pulse rounded border border-border/50" />
          <div className="h-96 bg-[#14171d] animate-pulse rounded border border-border/50" />
        </div>
      </div>
    );
  }

 if (error || !summary) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-red-400 p-6">
 <div className="max-w-md text-center border border-red-500/20 bg-red-950/10 p-6 rounded-lg">
 <AlertTriangle className="h-10 w-10 mx-auto mb-3 text-red-500" />
 <h3 className="font-semibold text-lg mb-1">System Communication Failure</h3>
 <p className="text-sm text-gray-400 mb-4">{error ||"Connection timed out"}</p>
 <button
 onClick={() => window.location.reload()}
 className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded text-sm hover:bg-red-500/30 transition"
 >
 Retry Connection
 </button>
 </div>
 </div>
 );
 }

 // Calculate Operational Metrics
 const total = summary.total_machines || 1;
 const healthScore = Math.round(((summary.healthy + summary.warning * 0.5) / total) * 100);

 // Group anomalies by type for bar chart
 const totalAnomaliesCount = anomalies.slice(0, 5).reduce((acc, curr) => acc + curr.anomaly_count, 0) || 1;
 const anomalyChartData = anomalies.slice(0, 5).map((a) => ({
 name: a.anomaly_type.replace(/_/g,""),
 count: a.anomaly_count,
 percentage: Math.round((a.anomaly_count / totalAnomaliesCount) * 100),
 }));

  const getPipelineHealthBadge = () => {
    const health = pipelineMetrics?.pipeline_health || 'healthy';
    if (!pipelineMetrics) {
      return (
        <span className="bg-gray-500/10 text-gray-400 border border-border px-2 py-0.5 rounded text-[10px] uppercase font-bold flex items-center gap-1">
          <RefreshCw className="h-2 w-2 animate-spin" /> Syncing...
        </span>
      );
    }
    if (health === 'healthy') {
      return (
        <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded text-[10px] uppercase font-bold flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
          Healthy
        </span>
      );
    }
    if (health === 'warning') {
      return (
        <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded text-[10px] uppercase font-bold">
          Warning
        </span>
      );
    }
    return (
      <span className="bg-red-500/10 text-red-400 border border-red-500/20 px-2.5 py-0.5 rounded text-[10px] uppercase font-bold animate-pulse">
        Critical
      </span>
    );
  };

  const calculateLag = (timestamp: string) => {
    if (!timestamp) return 0;
    const now = new Date().getTime();
    const then = new Date(timestamp).getTime();
    return Math.max(0, (now - then) / 1000); // seconds
  };
  
  const rawLag = pipelineMetrics ? calculateLag(pipelineMetrics.latest_raw_event_timestamp) : 0;
  const curatedLag = pipelineMetrics ? calculateLag(pipelineMetrics.latest_curated_event_timestamp) : 0;

 return (
 <div className="p-8 space-y-8 bg-[#0d0f12] min-h-screen text-gray-200 overflow-y-auto">
 {/* Top Operations Banner */}
 <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-border pb-6 gap-6">
 <div>
 <h1 className="text-3xl font-bold text-white flex items-center gap-2">
 <Cpu className="h-6 w-6 text-primary" />
 Executive Operations Center
 </h1>
 <p className="text-xs text-muted-foreground mt-1">
 System status: ACTIVE | Node: ingestion-node-01 | Region: ap-south-1
 </p>
 </div>
 <div className="flex items-center gap-4 bg-[#14171d] px-4 py-2.5 border border-border rounded-lg text-xs font-semibold shadow-sm">
 <div className="flex items-center gap-1.5">
 <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
 <span className="text-gray-300">FastAPI API Key Authorized</span>
 </div>
 </div>
 </div>



 {/* KPI Section */}
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
 {/* Total Machines */}
 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-lg hover:border-primary/30 transition duration-200">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs text-muted-foreground uppercase font-semibold">Total Machines</span>
 <InfoTooltip
 title="Total Machines"
 definition="Total active machine nodes currently registered."
 why="Confirms count of factory assets connected to AutoForge."
 good="Steady state matching plant inventories."
 bad="Disconnect of assets from data broker."
 />
 </div>
 <p className="text-xs text-muted-foreground mt-1.5">All registered machine assets.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-3xl font-bold text-white">{summary.total_machines}</span>
 <span className="text-xs text-muted-foreground font-semibold mr-1 mb-1">assets</span>
 <Activity className="h-6 w-6 text-blue-500 mb-1" />
 </div>
 </div>

 {/* Healthy Machines */}
 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-lg hover:border-primary/30 transition duration-200">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs text-muted-foreground uppercase font-semibold">Healthy Machines</span>
 <InfoTooltip
 title="Healthy Machines"
 definition="Count of assets operating fully within safety limits."
 why="Validates general fleet operation without alerts."
 good="Maximize (near 100% is ideal)."
 bad="Under 70% indicates heavy fleet-wide degradation."
 />
 </div>
 <p className="text-xs text-muted-foreground mt-1.5">Machines operating normally.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-3xl font-bold text-emerald-400">{summary.healthy}</span>
 <span className="text-xs text-muted-foreground font-semibold mr-1 mb-1">assets</span>
 <CheckCircle className="h-6 w-6 text-emerald-500 mb-1" />
 </div>
 </div>

 {/* Machines Requiring Attention */}
 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-lg hover:border-primary/30 transition duration-200">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs text-muted-foreground uppercase font-semibold">Attention Required</span>
 <InfoTooltip
 title="Attention Required"
 definition="Assets operating in warning thresholds."
 why="Highlights assets experiencing degradation or minor alerts."
 good="Under 15% of fleet."
 bad="Above 30% indicates maintenance backlogs."
 />
 </div>
 <p className="text-xs text-muted-foreground mt-1.5">Machines requiring monitoring.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-3xl font-bold text-amber-400">{summary.warning}</span>
 <span className="text-xs text-muted-foreground font-semibold mr-1 mb-1">assets</span>
 <AlertTriangle className="h-6 w-6 text-amber-500 mb-1" />
 </div>
 </div>

 {/* Critical Machines */}
 <div className="bg-card border border-border p-6 rounded-xl flex flex-col justify-between shadow-lg hover:border-primary/30 transition duration-200">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs text-muted-foreground uppercase font-semibold">Critical Machines</span>
 <InfoTooltip
 title="Critical Machines"
 definition="Assets with active severe alerts or failures."
 why="Triggers immediate dispatch of repair technician crew."
 good="0 critical failures."
 bad="Any value above 0 indicates active shutdown risk."
 />
 </div>
 <p className="text-xs text-muted-foreground mt-1.5">Severe anomalies active.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <span className="text-3xl font-bold text-rose-500">{summary.critical}</span>
 <span className="text-xs text-muted-foreground font-semibold mr-1 mb-1">assets</span>
 <AlertTriangle className="h-6 w-6 text-rose-500 mb-1 animate-pulse" />
 </div>
 </div>

 {/* Overall Factory Health */}
 <div className="bg-card border border-border p-6 rounded-xl col-span-1 md:col-span-2 lg:col-span-1 flex flex-col justify-between shadow-lg hover:border-primary/30 transition duration-200">
 <div>
 <div className="flex items-center justify-between">
 <span className="text-xs text-muted-foreground uppercase font-semibold">Overall Health</span>
 <InfoTooltip
 title="Overall Health Score"
 definition="Weighted condition of all active assets in the plant."
 why="Summarizes plant availability and production readiness."
 good="Above 85%"
 bad="Below 70% (requires immediate maintenance plan)"
 />
 </div>
 <p className="text-xs text-muted-foreground mt-1.5">Fleet-wide weighted health score.</p>
 </div>
 <div className="flex justify-between items-end mt-4">
 <div className="space-y-1">
 <span className={`text-3xl font-bold ${
 healthScore >= 80 ?"text-emerald-400" : healthScore >= 60 ?"text-amber-400" :"text-rose-400"
 }`}>{healthScore}%</span>
 <div className="text-[10px] text-muted-foreground leading-tight font-semibold">
 Factory health score
 </div>
 </div>
 <TrendingUp className="h-6 w-6 text-primary mb-1" />
 </div>
 </div>
 </div>

  {/* ====================================================
      PART 2 — REAL-TIME OBSERVABILITY CONSOLE
      ==================================================== */}
  <div className="bg-[#101216] border border-border p-8 rounded-xl space-y-6 shadow-xl relative overflow-hidden">
    {/* Background accent */}
    <div className="absolute top-0 right-0 p-32 bg-primary/5 rounded-full blur-[120px] pointer-events-none -mr-16 -mt-16"></div>

    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-border/60 pb-4 gap-4 relative z-10">
      <div className="flex items-center gap-2.5">
        <div className={`h-3 w-3 rounded-full ${pipelineMetrics ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500 animate-pulse'}`}></div>
        <h2 className="text-lg font-bold uppercase text-white tracking-wide">
          Real-Time Pipeline Observability Console
        </h2>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground ml-3 bg-[#14171d] px-2 py-1 rounded border border-border">
          <Activity className="h-3.5 w-3.5 text-primary" />
          <span className="font-medium">REST Polling Active (10s)</span>
        </div>
      </div>
    </div>

    {/* Real-time Ingestion KPI Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
      {/* A. S3 Raw Data */}
      <div className="bg-[#14171d]/80 border border-border p-5 rounded-xl flex flex-col justify-between shadow-md backdrop-blur-sm group hover:border-primary/40 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider group-hover:text-gray-300 transition">Raw S3 Data Lake</span>
          <Database className="h-4 w-4 text-sky-400" />
        </div>
        <div className="mt-4">
          <p className="text-2xl font-bold text-white tracking-tight">
            {pipelineMetrics ? pipelineMetrics.raw_records_total.toLocaleString() : '---'} <span className="text-xs text-muted-foreground font-normal">records</span>
          </p>
          <span className="text-[11px] text-muted-foreground block mt-1.5 font-medium">
            {pipelineMetrics ? `${pipelineMetrics.raw_files_total.toLocaleString()} objects / ${pipelineMetrics.raw_data_gb.toFixed(2)} GB` : 'Loading...'}
          </span>
        </div>
      </div>

      {/* B. S3 Curated Data */}
      <div className="bg-[#14171d]/80 border border-border p-5 rounded-xl flex flex-col justify-between shadow-md backdrop-blur-sm group hover:border-primary/40 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider group-hover:text-gray-300 transition">Curated S3 Records</span>
          <Database className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="mt-4">
          <p className="text-2xl font-bold text-white tracking-tight">
            {pipelineMetrics ? pipelineMetrics.curated_records_total.toLocaleString() : '---'} <span className="text-xs text-muted-foreground font-normal">records</span>
          </p>
          <span className="text-[11px] text-muted-foreground block mt-1.5 font-medium">
            {pipelineMetrics ? `${pipelineMetrics.compression_ratio}% compression ratio` : 'Loading...'}
          </span>
        </div>
      </div>

      {/* C. Kinesis Ingestion Velocity */}
      <div className="bg-[#14171d]/80 border border-border p-5 rounded-xl flex flex-col justify-between shadow-md backdrop-blur-sm group hover:border-primary/40 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider group-hover:text-gray-300 transition">Ingestion Velocity</span>
          <Activity className="h-4 w-4 text-blue-400" />
        </div>
        <div className="mt-4">
          <p className="text-2xl font-bold text-sky-400 tracking-tight">
            {pipelineMetrics ? pipelineMetrics.ingestion_events_per_second : '---'} <span className="text-xs text-sky-500/60 font-normal">events/sec</span>
          </p>
          <span className="text-[11px] text-muted-foreground block mt-1.5 font-medium">
            {pipelineMetrics ? `${pipelineMetrics.ingestion_events_per_minute.toLocaleString()} events/min` : 'Loading...'}
          </span>
        </div>
      </div>

      {/* D. Lambda Processing */}
      <div className="bg-[#14171d]/80 border border-border p-5 rounded-xl flex flex-col justify-between shadow-md backdrop-blur-sm group hover:border-primary/40 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider group-hover:text-gray-300 transition">Lambda Processing</span>
          <Cpu className="h-4 w-4 text-amber-400" />
        </div>
        <div className="mt-4">
          <p className="text-2xl font-bold text-white tracking-tight">
            {pipelineMetrics ? pipelineMetrics.lambda_invocations_per_minute.toLocaleString() : '---'} <span className="text-xs text-muted-foreground font-normal">invocations/min</span>
          </p>
          <span className="text-[11px] text-muted-foreground block mt-1.5 font-medium">
             {pipelineMetrics ? `${pipelineMetrics.lambda_errors_per_minute} errors/min` : 'Loading...'}
          </span>
        </div>
      </div>
    </div>

    {/* Live Pipeline Flow & Data Lag Visualization */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-2 relative z-10">
      
      {/* Node-based Visualization */}
      <div className="bg-[#14171d]/50 border border-border p-6 rounded-xl shadow-inner flex flex-col justify-between">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase mb-6 tracking-widest">Live Pipeline Throughput</h3>
        
        <div className="flex flex-col space-y-6 relative">
           {/* Vertical Line Connector */}
           <div className="absolute left-[23px] top-6 bottom-6 w-0.5 bg-border/40 z-0"></div>

           {/* Kinesis Node */}
           <div className="flex items-center gap-4 relative z-10 group">
             <div className="h-12 w-12 rounded-full bg-[#0d0f12] border border-blue-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.1)] group-hover:border-blue-400 transition-colors">
               <Activity className="h-5 w-5 text-blue-400" />
             </div>
             <div className="flex-1">
               <div className="flex justify-between items-end">
                 <span className="font-bold text-gray-200 text-sm">Kinesis Data Streams</span>
                 <span className="text-xs font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">{pipelineMetrics?.ingestion_events_per_second || 0} eps</span>
               </div>
               <div className="text-[11px] text-muted-foreground mt-1">Ingesting raw telemetry from factory floor</div>
             </div>
           </div>

           {/* Lambda Node */}
           <div className="flex items-center gap-4 relative z-10 group">
             <div className="h-12 w-12 rounded-full bg-[#0d0f12] border border-amber-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(245,158,11,0.1)] group-hover:border-amber-400 transition-colors">
               <Cpu className="h-5 w-5 text-amber-400" />
             </div>
             <div className="flex-1">
               <div className="flex justify-between items-end">
                 <span className="font-bold text-gray-200 text-sm">Lambda Validator</span>
                 <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">{pipelineMetrics?.processed_per_second || 0} eps</span>
               </div>
               <div className="text-[11px] text-muted-foreground mt-1">Schema validation, anomaly detection routing</div>
             </div>
           </div>

           {/* S3 Node */}
           <div className="flex items-center gap-4 relative z-10 group">
             <div className="h-12 w-12 rounded-full bg-[#0d0f12] border border-emerald-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.1)] group-hover:border-emerald-400 transition-colors">
               <Database className="h-5 w-5 text-emerald-400" />
             </div>
             <div className="flex-1">
               <div className="flex justify-between items-end">
                 <span className="font-bold text-gray-200 text-sm">S3 Data Lake</span>
                 <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">{pipelineMetrics?.raw_files_total.toLocaleString() || 0} files</span>
               </div>
               <div className="text-[11px] text-muted-foreground mt-1">Persistent storage for analytics pipeline</div>
             </div>
           </div>

        </div>
      </div>

      {/* Freshness / Lag Display */}
      <div className="bg-[#14171d]/50 border border-border p-6 rounded-xl shadow-inner flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Data Freshness & Pipeline Health</h3>
          {getPipelineHealthBadge()}
        </div>

        <div className="space-y-6 flex-1">
           {/* Raw Freshness */}
           <div>
             <div className="flex justify-between text-sm mb-1">
               <span className="text-gray-300 font-medium">Raw Data Arrival</span>
               <span className="font-mono text-sky-400">{Math.round(rawLag)}s ago</span>
             </div>
             <div className="h-2 w-full bg-border/40 rounded-full overflow-hidden">
               <div className={`h-full rounded-full ${rawLag < 15 ? 'bg-sky-400' : rawLag < 60 ? 'bg-amber-400' : 'bg-red-400'}`} style={{ width: `${Math.min(100, Math.max(5, 100 - (rawLag/60)*100))}%` }}></div>
             </div>
             <div className="text-[10px] text-muted-foreground mt-1.5 flex justify-between">
                <span>Lag from generator</span>
                <span>{pipelineMetrics?.latest_raw_event_timestamp ? new Date(pipelineMetrics.latest_raw_event_timestamp).toLocaleTimeString() : '--:--:--'}</span>
             </div>
           </div>

           {/* Curated Freshness */}
           <div>
             <div className="flex justify-between text-sm mb-1">
               <span className="text-gray-300 font-medium">Curated Data (ETL)</span>
               <span className="font-mono text-emerald-400">{Math.round(curatedLag)}s ago</span>
             </div>
             <div className="h-2 w-full bg-border/40 rounded-full overflow-hidden">
               <div className={`h-full rounded-full ${curatedLag < 3600 ? 'bg-emerald-400' : 'bg-amber-400'}`} style={{ width: `${Math.min(100, Math.max(5, 100 - (curatedLag/3600)*100))}%` }}></div>
             </div>
             <div className="text-[10px] text-muted-foreground mt-1.5 flex justify-between">
                <span>Lag from raw transformation</span>
                <span>{pipelineMetrics?.latest_curated_event_timestamp ? new Date(pipelineMetrics.latest_curated_event_timestamp).toLocaleTimeString() : '--:--:--'}</span>
             </div>
           </div>

           {/* Health Reasons */}
           <div className="bg-[#0d0f12] p-4 rounded-lg border border-border mt-auto">
             <span className="text-[10px] uppercase font-bold text-muted-foreground block mb-2">Diagnostics:</span>
             <ul className="text-xs space-y-1.5 text-gray-400">
               {pipelineMetrics?.health_reasons?.map((r: string, i: number) => (
                 <li key={i} className="flex items-start gap-2">
                   <div className={`h-1.5 w-1.5 rounded-full mt-1 shrink-0 ${pipelineMetrics.pipeline_health === 'healthy' ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                   <span>{r}</span>
                 </li>
               )) || <li>Awaiting diagnostics...</li>}
             </ul>
           </div>
        </div>
      </div>

    </div>
  </div>

  {/* Fleet and Alert Logs Grid */}
 <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
 {/* Fleet Registry Matrix */}
 <div className="bg-card border border-border p-6 rounded-xl lg:col-span-2 space-y-5 shadow-lg">
 <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-border pb-4 gap-4">
 <div className="flex items-center gap-2">
 <h3 className="text-lg font-bold uppercase text-white">Fleet Registry Matrix</h3>
 <InfoTooltip
 title="Fleet Registry"
 definition="Grid summary of connected industrial assets."
 why="Select any machine node to inspect its live Digital Twin stream."
 good="All assets are Healthy (green)."
 bad="Any Critical (red) or Warning (yellow) badges."
 />
 </div>
 <div className="flex flex-wrap items-center gap-3 text-xs font-semibold text-muted-foreground">
 <span className="text-muted-foreground uppercase mr-1">Legend:</span>
 <span className="flex items-center gap-1.5">
 <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span> Healthy
 </span>
 <span className="flex items-center gap-1.5">
 <span className="h-2.5 w-2.5 rounded-full bg-amber-500"></span> Warning
 </span>
 <span className="flex items-center gap-1.5">
 <span className="h-2.5 w-2.5 rounded-full bg-rose-500 animate-pulse"></span> Critical
 </span>
 <span className="flex items-center gap-1.5">
 <span className="h-2.5 w-2.5 rounded-full bg-slate-500"></span> Offline
 </span>
 </div>
 </div>

 {machines.length === 0 ? (
 <div className="text-center py-12 text-sm text-muted-foreground border border-dashed border-border rounded-xl">
 No data available yet. The system is waiting for telemetry data.
 </div>
 ) : (
 <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
 {machines.map((m) => {
 const currentHealth = m.health_score ? Math.round(m.health_score) : Math.round(100 - m.max_degradation_level * 100);
 const charSum = m.machine_id.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
 const lastSeenSec = (charSum % 8) + 2;
 return (
 <Link
 key={m.machine_id}
 to={`/machine/${m.machine_id}`}
 className={`border p-5 rounded-xl transition-all duration-300 cursor-pointer flex flex-col justify-between gap-4 bg-[#0d0f12] hover:bg-[#14171d] hover:border-primary/40 shadow-sm ${
 m.health_status ==="healthy"
 ?"border-emerald-500/20 hover:shadow-emerald-500/5"
 : m.health_status ==="warning"
 ?"border-amber-500/20 hover:shadow-amber-500/5"
 : m.health_status ==="critical"
 ?"border-rose-500/20 hover:shadow-rose-500/5 animate-pulse"
 :"border-slate-500/20 hover:shadow-slate-500/5"
 }`}
 >
 <div className="flex justify-between items-start">
 <div>
 <span className="text-base font-bold text-white block">{m.machine_id}</span>
 <span className="text-xs text-muted-foreground uppercase font-semibold">
 {m.machine_type.replace(/_/g,"")}
 </span>
 </div>
 <span
 className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
 m.health_status ==="healthy"
 ?"bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
 : m.health_status ==="warning"
 ?"bg-amber-500/10 text-amber-400 border-amber-500/20"
 : m.health_status ==="critical"
 ?"bg-rose-500/10 text-rose-400 border-rose-500/20"
 :"bg-slate-500/10 text-slate-400 border-slate-500/20"
 }`}
 >
 {m.health_status}
 </span>
 </div>

 <div className="border-t border-border/40 pt-3 flex justify-between items-end text-xs">
 <div>
 <span className="text-muted-foreground uppercase block text-[9px] font-bold">Asset Health</span>
 <span
 className={`font-bold text-sm ${
 currentHealth > 70
 ?"text-emerald-400"
 : currentHealth > 40
 ?"text-amber-400"
 :"text-rose-400"
 }`}
 >
 {currentHealth}%
 </span>
 </div>
 <div className="text-right">
 <span className="text-muted-foreground uppercase block text-[9px] font-bold">Last Packet</span>
 <span className="text-gray-400 font-semibold">{lastSeenSec}s ago</span>
 </div>
 </div>
 </Link>
 );
 })}
 </div>
 )}
 </div>

 {/* Real-time Alert Feed */}
 <div className="bg-card border border-border p-6 rounded-xl flex flex-col space-y-5 shadow-lg">
 <div className="flex justify-between items-center border-b border-border pb-3">
 <div className="flex items-center gap-2">
 <h3 className="text-lg font-bold uppercase text-white">Operational Alert Log</h3>
 <InfoTooltip
 title="Operational Alert Log"
 definition="Chronological events of detected warnings and failures."
 why="Pinpoints recent failures requiring root cause diagnostics."
 good="Empty feed or nominal status logs."
 bad="Flashing critical events with high severity scores."
 />
 </div>
 <span className="h-2.5 w-2.5 rounded-full bg-rose-500 animate-pulse"></span>
 </div>
 <div className="flex-1 space-y-4 overflow-y-auto max-h-[460px] pr-2">
 {diagnostics.length === 0 ? (
 <div className="text-center text-muted-foreground py-12 text-sm border border-dashed border-border rounded-xl">
 No active diagnostics logs available.
 </div>
 ) : (
 diagnostics.map((a) => {
 const confPercent = Math.round(a.confidence * 100);
 const confColor =
 confPercent >= 80
 ?"text-rose-400 border-rose-500/20 bg-rose-500/10"
 : confPercent >= 60
 ?"text-amber-400 border-amber-500/20 bg-amber-500/10"
 :"text-sky-400 border-sky-500/20 bg-sky-500/10";
 return (
 <div
 key={a.event_id}
 className="bg-[#14171d] border border-border p-5 rounded-xl text-sm space-y-4 hover:border-primary/40 transition duration-300 shadow-md"
 >
 <div className="flex justify-between items-center border-b border-border/40 pb-3">
 <span className="font-bold text-white flex items-center gap-2">
 <span
 className={`h-2 w-2 rounded-full ${
 confPercent >= 80 ?"bg-rose-500" :"bg-amber-500"
 }`}
 ></span>
 {a.machine_id}
 </span>
 <span className="text-xs text-muted-foreground font-semibold">
 {new Date(a.timestamp).toLocaleTimeString()}
 </span>
 </div>

 <div className="space-y-2">
 <div className="flex justify-between items-center">
 <span className="text-gray-300 font-bold uppercase text-xs">
 {a.anomaly_type.replace(/_/g,"")}
 </span>
 <div className="relative group">
 <span
 className={`text-xs font-semibold px-2 py-0.5 rounded cursor-help border ${confColor}`}
 >
 Conf: {confPercent}%
 </span>
 </div>
 </div>

 <div className="text-xs text-gray-300 space-y-2">
 <div>
 <span className="text-muted-foreground text-[9px] uppercase block font-bold mt-2">
 Trigger Reason
 </span>
 <p className="leading-relaxed text-gray-200 mt-0.5">{a.explanation}</p>
 </div>
 <div>
 <span className="text-muted-foreground text-[9px] uppercase block font-bold mt-2">
 Evidence
 </span>
 <p className="text-amber-400 font-semibold bg-[#0d0f12] px-2.5 py-1.5 rounded border border-border/40 mt-1 inline-block">
 {a.evidence}
 </p>
 </div>
 <div>
 <span className="text-muted-foreground text-[9px] uppercase block font-bold mt-2">
 Likely Causes
 </span>
 <ul className="list-none space-y-1 mt-1 text-gray-400 font-medium">
 {a.probable_causes.map((c, idx) => (
 <li key={idx} className="flex items-center gap-2 text-xs">
 <span className="text-primary font-bold">•</span>
 <span>{c}</span>
 </li>
 ))}
 </ul>
 </div>
 </div>
 </div>

 <div className="bg-[#0d0f12] p-3.5 rounded-lg border border-emerald-500/10 space-y-1">
 <span className="text-[9px] text-muted-foreground uppercase font-bold block">
 Recommended Action
 </span>
 <ul className="list-decimal list-inside space-y-1 text-xs text-emerald-400 leading-relaxed font-semibold">
 {a.recommendations.map((rec, idx) => (
 <li key={idx}>{rec}</li>
 ))}
 </ul>
 </div>
 </div>
 );
 })
 )}
 </div>
 </div>
 </div>

 {/* Bottom Row - Anomaly Distribution chart */}
 <div className="grid grid-cols-1 gap-6">
 {/* Most Common Machine Issues Chart */}
 <div className="bg-card border border-border p-6 rounded-xl space-y-5 shadow-lg">
 <div>
 <div className="flex items-center gap-2">
 <h3 className="text-lg font-bold uppercase text-white">
 Fleet Anomaly Distribution Profile
 </h3>
 <InfoTooltip
 title="Common Issues Profile"
 definition="Aggregated distribution profile of anomalies categorized by failure type."
 why="Analyzes historical patterns to target component reinforcement."
 good="Low height on bar profiles."
 bad="Tall profiles indicating persistent engineering flaws."
 />
 </div>
 <p className="text-sm text-muted-foreground mt-1">
 Shows which problems occur most frequently across the factory.
 </p>
 </div>
 <div className="h-[280px]">
 {anomalyChartData.length === 0 ? (
 <div className="flex h-full items-center justify-center border border-dashed border-border rounded-xl text-sm text-muted-foreground">
 No data available yet.
 </div>
 ) : (
 <ResponsiveContainer width="100%" height="100%">
 <BarChart data={anomalyChartData} margin={{ top: 20, right: 10, left: -20, bottom: 5 }}>
 <XAxis dataKey="name" stroke="#9ca3af" fontSize={11} style={{ fontFamily:"var(--)" }} />
 <YAxis stroke="#9ca3af" fontSize={11} style={{ fontFamily:"var(--)" }} />
 <Tooltip
 contentStyle={{ backgroundColor:"#14171d", borderColor:"#242b35", borderRadius:"8px" }}
 itemStyle={{ color:"#ffffff" }}
 formatter={(value: any, _name: any, props: any) => [
 `${value} incidents (${props.payload.percentage}%)`,
"Occurrence Count",
 ]}
 />
 <Bar dataKey="count" fill="#e11d48" radius={[4, 4, 0, 0]}>
 {anomalyChartData.map((_, index) => (
 <Cell key={`cell-${index}`} fill="#e11d48" opacity={0.8} />
 ))}
 <LabelList
 dataKey="percentage"
 position="top"
 formatter={(val: any) => `${val}%`}
 style={{ fill:"#e11d48", fontSize: 11, fontFamily:"var(--)", fontWeight:"bold" }}
 />
 </Bar>
 </BarChart>
 </ResponsiveContainer>
 )}
 </div>
 </div>
 </div>
 </div>
 );
}

