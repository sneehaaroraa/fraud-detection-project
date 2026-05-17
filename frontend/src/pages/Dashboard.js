import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState({ total_scanned: 0, fraud_alerts: 0, risk_index: 0, recent_activity: [] });
  const [anomalies, setAnomalies] = useState([]);
  const [view, setView] = useState('overview'); // overview or threats

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('/api/fraud/stats');
        setStats(res.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data");
      }
    };
    const fetchThreats = async () => {
      try {
        const res = await axios.get('/api/fraud/insider-threats');
        setAnomalies(res.data.anomalies);
      } catch (err) {
        console.error("Failed to fetch threat data");
      }
    };
    fetchStats();
    fetchThreats();
    const interval = setInterval(() => { fetchStats(); fetchThreats(); }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (txId, action) => {
    try {
      await axios.post('http://localhost:8000/api/fraud/action', { transaction_id: txId, action });
      alert(`Successfully applied ${action} to ${txId}`);
    } catch (err) {
      alert("Action failed");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar - Midnight SOC Style */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 p-6 space-y-8 hidden md:block">
        <h2 className="text-xl font-black tracking-tighter text-indigo-400">FRAUDEYE <span className="text-slate-100">PRO</span></h2>
        <nav className="space-y-2">
          <div onClick={() => setView('overview')} className={`flex items-center p-3 rounded-lg cursor-pointer transition ${view === 'overview' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50' : 'text-slate-400 hover:bg-slate-800'}`}>
             <span className="mr-3 text-lg">📊</span> <span className="font-semibold">Security Overview</span>
          </div>
          <div onClick={() => setView('threats')} className={`flex items-center p-3 rounded-lg cursor-pointer transition ${view === 'threats' ? 'bg-red-600 text-white shadow-lg shadow-red-900/50' : 'text-slate-400 hover:bg-slate-800'}`}>
             <span className="mr-3 text-lg">🚨</span> <span className="font-semibold">Insider Threats</span>
          </div>
          <div className="flex items-center p-3 rounded-lg text-slate-400 hover:bg-slate-800 cursor-pointer transition">
             <span className="mr-3 text-lg">🛡️</span> <span className="font-semibold">Access Control</span>
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 space-y-8">
        <header className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-black">{view === 'overview' ? 'SOC Operations Center' : 'Threat Intelligence Module'}</h1>
            <p className="text-slate-500 text-sm">Real-time surveillance active • {new Date().toLocaleTimeString()}</p>
          </div>
          <div className="flex space-x-4">
            <span className="px-4 py-1.5 bg-slate-900 border border-slate-800 rounded-full text-[10px] font-bold text-indigo-400 animate-pulse">
              ● SENTINEL ACTIVE
            </span>
          </div>
        </header>

        {view === 'overview' ? (
          <>
            {/* High-Impact Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-2">Network Throughput</p>
                <h3 className="text-4xl font-black">{stats.total_scanned.toLocaleString()}</h3>
                <div className="mt-4 h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 w-3/4"></div>
                </div>
              </div>
              <div className="bg-slate-900 border border-red-900/30 p-6 rounded-2xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-red-600"></div>
                <p className="text-red-500 text-[10px] font-bold uppercase tracking-widest mb-2">Critical Anomalies</p>
                <h3 className="text-4xl font-black text-red-500">{stats.fraud_alerts}</h3>
                <p className="text-[10px] text-red-900 mt-2 font-bold">INTERVENTION REQUIRED</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-2">Aggregate Risk</p>
                <h3 className="text-4xl font-black">{stats.risk_index}%</h3>
                <p className="text-[10px] text-slate-600 mt-2">Within safe operational limits</p>
              </div>
            </div>

            {/* Threat Feed */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="p-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                <h2 className="font-bold">Automated Threat Feed</h2>
                <div className="flex space-x-2">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-ping"></div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase">Live Updates</span>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="text-[10px] text-slate-500 font-black uppercase tracking-widest border-b border-slate-800">
                    <tr>
                      <th className="p-6">Origin ID</th>
                      <th className="p-6">Value</th>
                      <th className="p-6">XAI Rationale</th>
                      <th className="p-6">Resolution Status</th>
                      <th className="p-6 text-right">Rapid Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {stats.recent_activity.map((tx, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition group">
                        <td className="p-6 font-mono text-xs text-indigo-400">{tx.transaction_id}</td>
                        <td className="p-6 font-black text-sm">${tx.amount.toLocaleString()}</td>
                        <td className="p-6">
                          <div className="flex flex-wrap gap-1">
                            {tx.explanation && JSON.parse(tx.explanation).map((reason, ridx) => (
                              <span key={ridx} className="bg-slate-950 text-[8px] px-2 py-0.5 rounded border border-slate-800 text-slate-400">
                                {reason}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="p-6">
                           <span className={`px-2 py-0.5 rounded-full text-[9px] font-black ${tx.status === 'BLOCKED' ? 'bg-red-900/30 text-red-500' : tx.prediction === 'FRAUD' ? 'bg-red-500 text-white' : 'bg-green-900/30 text-green-500'}`}>
                            {tx.status === 'BLOCKED' ? 'TERMINATED' : tx.prediction}
                           </span>
                        </td>
                        <td className="p-6 text-right space-x-2 opacity-0 group-hover:opacity-100 transition">
                           <button onClick={() => handleAction(tx.transaction_id, 'BLOCK')} className="p-2 bg-red-600 rounded text-xs hover:bg-red-500" title="Block TXN">🚫</button>
                           <button onClick={() => handleAction(tx.transaction_id, 'FREEZE_USER')} className="p-2 bg-slate-700 rounded text-xs hover:bg-slate-600" title="Freeze Account">❄️</button>
                           <button onClick={() => handleAction(tx.transaction_id, 'CLEAR')} className="p-2 bg-green-600 rounded text-xs hover:bg-green-500" title="Clear TXN">✅</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          /* Insider Threats View */
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {anomalies.map((anomaly, idx) => (
                <div key={idx} className={`p-8 rounded-2xl border ${anomaly.severity === 'HIGH' ? 'bg-red-950/20 border-red-900/30' : 'bg-slate-900 border-slate-800'}`}>
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-bold">{anomaly.type}</h3>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${anomaly.severity === 'HIGH' ? 'bg-red-600' : 'bg-orange-500'}`}>{anomaly.severity}</span>
                  </div>
                  <p className="text-slate-400 mb-6">{anomaly.details}</p>
                  <button className="w-full py-3 bg-slate-800 rounded-xl text-sm font-bold hover:bg-slate-700 transition">Investigate User Activity</button>
                </div>
              ))}
            </div>
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl">
              <h3 className="text-xl font-bold mb-4">Heuristic Analysis Model</h3>
              <p className="text-slate-400 text-sm mb-6">Our algorithms identify "Insider Threats" by correlating login location, transaction frequency, and administrative access patterns. The current feed shows low-level anomalies that require human triage.</p>
              <div className="h-40 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center italic text-slate-700">
                 Waveform Analytics Placeholder (Live Visualization)
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
