import { useEffect, useState } from"react";
import { Link } from"react-router-dom";
import { Search, Filter, Grid, List as ListIcon, AlertTriangle } from"lucide-react";
import { machineService, type MachineHealthRecord } from"../services/machineService";

export default function FleetRegistry() {
 const [machines, setMachines] = useState<MachineHealthRecord[]>([]);
 const [search, setSearch] = useState("");
 const [statusFilter, setStatusFilter] = useState("all");
 const [typeFilter, setTypeFilter] = useState("all");
 const [sortBy, setSortBy] = useState("id");
 const [viewMode, setViewMode] = useState<"grid" |"table">("grid");
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 useEffect(() => {
 async function fetchMachines() {
 try {
 const data = await machineService.getMachines();
 setMachines(data);
 } catch (err: any) {
 setError(err.message ||"Failed to load fleet registry");
 } finally {
 setLoading(false);
 }
 }
 fetchMachines();
 }, []);

 if (loading) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-gray-400">
 <div className="text-center space-y-2">
 <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
 <p className="text-xs tracking-widest uppercase">Querying Registry Catalog...</p>
 </div>
 </div>
 );
 }

 if (error) {
 return (
 <div className="flex h-full items-center justify-center bg-[#0d0f12] text-red-400 p-6">
 <div className="max-w-md text-center border border-red-500/20 bg-red-950/10 p-6 rounded-lg">
 <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-red-500" />
 <h3 className="font-semibold text-sm mb-1">Registry Sync Failed</h3>
 <p className="text-xs text-gray-400 mb-4">{error}</p>
 </div>
 </div>
 );
 }

 // Filter & Sort logic
 const filteredMachines = machines
 .filter((m) => {
 const matchesSearch = m.machine_id.toLowerCase().includes(search.toLowerCase());
 const matchesStatus = statusFilter ==="all" || m.health_status === statusFilter;
 const matchesType = typeFilter ==="all" || m.machine_type === typeFilter;
 return matchesSearch && matchesStatus && matchesType;
 })
 .sort((a, b) => {
 switch (sortBy) {
 case"health":
 const healthMap: Record<string, number> = { critical: 1, warning: 2, healthy: 3, offline: 4 };
 return healthMap[a.health_status] - healthMap[b.health_status];
 case"anomalies":
 return b.anomaly_events - a.anomaly_events;
 case"temp":
 return (b.avg_temperature || 0) - (a.avg_temperature || 0);
 case"activity":
 return b.total_events - a.total_events;
 default:
 return a.machine_id.localeCompare(b.machine_id);
 }
 });

 const machineTypes = Array.from(new Set(machines.map((m) => m.machine_type)));

 const getHealthBadge = (status: string) => {
 switch (status) {
 case"healthy":
 return <span className="bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded text-xs font-semibold uppercase">Healthy</span>;
 case"warning":
 return <span className="bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 px-2 py-0.5 rounded text-xs font-semibold uppercase">Warning</span>;
 case"critical":
 return <span className="bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded text-xs font-semibold uppercase">Critical</span>;
 default:
 return <span className="bg-gray-500/10 text-gray-400 border border-gray-500/20 px-2 py-0.5 rounded text-xs font-semibold uppercase">Offline</span>;
 }
 };

 return (
 <div className="p-6 space-y-6 bg-[#0d0f12] min-h-screen text-gray-200 overflow-y-auto">
 {/* Page Header */}
 <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-border pb-4 gap-4">
 <div>
 <h1 className="text-2xl font-bold text-white">Machine Fleet Registry</h1>
 <p className="text-sm text-gray-400 mt-1">Inventory & Diagnostic Matrix</p>
 </div>
 <div className="flex items-center gap-4">
 <div className="flex bg-[#14171d] border border-border rounded-lg p-1">
 <button
 onClick={() => setViewMode("grid")}
 className={`p-1.5 rounded transition ${viewMode ==="grid" ?"bg-[#242b35] text-white" :"text-gray-400 hover:text-gray-200"}`}
 >
 <Grid className="h-4 w-4" />
 </button>
 <button
 onClick={() => setViewMode("table")}
 className={`p-1.5 rounded transition ${viewMode ==="table" ?"bg-[#242b35] text-white" :"text-gray-400 hover:text-gray-200"}`}
 >
 <ListIcon className="h-4 w-4" />
 </button>
 </div>
 </div>
 </div>

 {/* Filters Toolbar */}
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 bg-[#14171d] p-4 border border-border rounded-lg shadow-sm">
 <div className="relative">
 <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
 <input
 type="text"
 placeholder="Search machine ID..."
 value={search}
 onChange={(e) => setSearch(e.target.value)}
 className="w-full bg-[#0d0f12] border border-border rounded-md pl-9 pr-3 py-2 text-sm focus:border-primary focus:outline-none"
 />
 </div>

 <select
 value={statusFilter}
 onChange={(e) => setStatusFilter(e.target.value)}
 className="bg-[#0d0f12] border border-border rounded-md px-3 py-2 text-sm focus:border-primary focus:outline-none cursor-pointer"
 >
 <option value="all">ALL STATUSES</option>
 <option value="healthy">HEALTHY</option>
 <option value="warning">WARNING</option>
 <option value="critical">CRITICAL</option>
 <option value="offline">OFFLINE</option>
 </select>

 <select
 value={typeFilter}
 onChange={(e) => setTypeFilter(e.target.value)}
 className="bg-[#0d0f12] border border-border rounded-md px-3 py-2 text-sm focus:border-primary focus:outline-none cursor-pointer"
 >
 <option value="all">ALL TYPES</option>
 {machineTypes.map((t) => (
 <option key={t} value={t}>
 {t.replace(/_/g,"").toUpperCase()}
 </option>
 ))}
 </select>

 <select
 value={sortBy}
 onChange={(e) => setSortBy(e.target.value)}
 className="bg-[#0d0f12] border border-border rounded-md px-3 py-2 text-sm focus:border-primary focus:outline-none cursor-pointer"
 >
 <option value="id">SORT BY: ID</option>
 <option value="health">SORT BY: HEALTH</option>
 <option value="anomalies">SORT BY: ANOMALIES</option>
 <option value="temp">SORT BY: TEMP</option>
 <option value="activity">SORT BY: ACTIVITY</option>
 </select>
 </div>

 {filteredMachines.length === 0 && (
 <div className="text-center py-12 border border-dashed border-border rounded-lg bg-card">
 <Filter className="h-8 w-8 mx-auto text-gray-500 mb-3" />
 <p className="text-sm text-gray-400">No fleet registry assets match the filters.</p>
 </div>
 )}

 {/* Grid Mode */}
 {viewMode ==="grid" && filteredMachines.length > 0 && (
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
 {filteredMachines.map((m) => {
 const currentHealth = Math.round(100 - (m.max_degradation_level * 100));
 return (
 <div
 key={m.machine_id}
 className={`bg-card border p-4 rounded-lg hover:border-primary/50 transition-all flex flex-col justify-between space-y-4 ${
 m.health_status ==="healthy" ?"border-green-500/10" :
 m.health_status ==="warning" ?"border-yellow-500/10" :
 m.health_status ==="critical" ?"border-red-500/10" :
"border-gray-500/10"
 }`}
 >
 <div className="flex justify-between items-start">
 <div>
 <h3 className="font-bold text-white text-base">{m.machine_id}</h3>
 <span className="text-[10px] uppercase text-gray-400 font-semibold">
 {m.machine_type.replace(/_/g,"")}
 </span>
 </div>
 {getHealthBadge(m.health_status)}
 </div>

 <div className="grid grid-cols-2 gap-4 border-b border-border/50 pb-3">
 <div>
 <span className="block text-[10px] uppercase text-gray-500 font-semibold mb-1">Health</span>
 <span className={`text-xl font-bold ${
 m.health_status ==="healthy" ?"text-green-400" :
 m.health_status ==="warning" ?"text-yellow-400" :
 m.health_status ==="critical" ?"text-red-400" :"text-gray-400"
 }`}>
 {currentHealth}%
 </span>
 </div>
 <div>
 <span className="block text-[10px] uppercase text-gray-500 font-semibold mb-1">Anomalies</span>
 <span className="text-xl font-bold text-red-400">{m.anomaly_events}</span>
 </div>
 </div>

 <div className="grid grid-cols-2 gap-4 text-xs text-gray-400">
 <div>
 <span className="block text-[9px] uppercase text-gray-500">Avg Temp</span>
 <span className="text-white font-medium">{m.avg_temperature ? `${Math.round(m.avg_temperature)}°C` :"N/A"}</span>
 </div>
 <div>
 <span className="block text-[9px] uppercase text-gray-500">Total Events</span>
 <span className="text-white font-medium">{m.total_events}</span>
 </div>
 </div>

 <Link
 to={`/machine/${m.machine_id}`}
 className="w-full py-2 bg-[#1e2530] border border-border rounded text-white hover:bg-primary hover:border-primary transition font-semibold text-xs text-center"
 >
 Inspect Twin
 </Link>
 </div>
 );
 })}
 </div>
 )}

 {/* Table Mode */}
 {viewMode ==="table" && filteredMachines.length > 0 && (
 <div className="bg-card border border-border rounded-lg overflow-hidden">
 <table className="w-full text-left text-sm">
 <thead className="bg-[#14171d] text-gray-400 border-b border-border text-xs uppercase">
 <tr>
 <th className="p-4 font-semibold">Machine ID</th>
 <th className="p-4 font-semibold">Type</th>
 <th className="p-4 font-semibold text-center">Status</th>
 <th className="p-4 font-semibold text-right">Health</th>
 <th className="p-4 font-semibold text-right">Avg Temp</th>
 <th className="p-4 font-semibold text-right">Anomalies</th>
 <th className="p-4 font-semibold text-right">Events</th>
 <th className="p-4 font-semibold text-center">Actions</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-border">
 {filteredMachines.map((m) => {
 const currentHealth = Math.round(100 - (m.max_degradation_level * 100));
 return (
 <tr key={m.machine_id} className="hover:bg-[#1c222c] transition">
 <td className="p-4 font-medium text-white">{m.machine_id}</td>
 <td className="p-4 text-gray-400 text-xs uppercase">{m.machine_type.replace(/_/g,"")}</td>
 <td className="p-4 text-center">{getHealthBadge(m.health_status)}</td>
 <td className={`p-4 text-right font-bold ${
 m.health_status ==="healthy" ?"text-green-400" :
 m.health_status ==="warning" ?"text-yellow-400" :
 m.health_status ==="critical" ?"text-red-400" :"text-gray-400"
 }`}>
 {currentHealth}%
 </td>
 <td className="p-4 text-right text-gray-300">
 {m.avg_temperature ? `${m.avg_temperature.toFixed(1)}°C` :"N/A"}
 </td>
 <td className="p-4 text-right text-red-400 font-medium">{m.anomaly_events}</td>
 <td className="p-4 text-right text-gray-400">{m.total_events}</td>
 <td className="p-4 text-center">
 <Link
 to={`/machine/${m.machine_id}`}
 className="px-3 py-1.5 bg-[#1e2530] border border-border rounded text-white hover:bg-primary hover:border-primary transition text-xs font-medium"
 >
 Inspect
 </Link>
 </td>
 </tr>
 );
 })}
 </tbody>
 </table>
 </div>
 )}
 </div>
 );
}
