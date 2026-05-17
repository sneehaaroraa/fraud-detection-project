import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState({ total_scanned: 0, fraud_alerts: 0, risk_index: 0, recent_activity: [] });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/fraud/stats');
        setStats(res.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data");
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Live poll
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-indigo-900 text-white p-6 space-y-8 hidden md:block">
        <h2 className="text-2xl font-bold italic">FraudEye PRO</h2>
        <nav className="space-y-4">
          <div className="text-indigo-300 flex items-center bg-indigo-800 p-2 rounded cursor-pointer">
             📊 <span className="ml-3 font-bold">Dashboard</span>
          </div>
          <div className="flex items-center p-2 rounded hover:bg-indigo-800 cursor-pointer">
             🕒 <span className="ml-3">Audit Logs</span>
          </div>
          <div className="flex items-center p-2 rounded hover:bg-indigo-800 cursor-pointer">
             🛡️ <span className="ml-3">Rules Engine</span>
          </div>
          <div className="flex items-center p-2 rounded hover:bg-indigo-800 cursor-pointer">
             👤 <span className="ml-3">Profile</span>
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8">
        <header className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-gray-800">Security Analytics Overview</h1>
          <div className="flex space-x-2">
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-bold flex items-center">
              ● API ACTIVE
            </span>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <p className="text-gray-400 text-sm mb-1 uppercase tracking-wider">Total Scanned</p>
            <h3 className="text-3xl font-black text-gray-800">{stats.total_scanned.toLocaleString()}</h3>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 border-l-4 border-red-500">
            <p className="text-gray-400 text-sm mb-1 uppercase tracking-wider">Fraud Alerts</p>
            <h3 className="text-3xl font-black text-red-600">{stats.fraud_alerts}</h3>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <p className="text-gray-400 text-sm mb-1 uppercase tracking-wider">Risk Index</p>
            <h3 className="text-3xl font-black text-gray-800">{stats.risk_index}%</h3>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Live Threat Feed (with XAI Explanations)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-gray-400 text-sm border-b">
                  <th className="pb-3">TXN_ID</th>
                  <th className="pb-3">AMOUNT</th>
                  <th className="pb-3">PREDICTION</th>
                  <th className="pb-3">REASONING (XAI)</th>
                  <th className="pb-3 text-right">TIMESTAMP</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_activity.map((tx, idx) => (
                  <tr key={idx} className="border-b last:border-0 hover:bg-gray-50 transition">
                    <td className="py-4 font-mono text-xs">{tx.transaction_id}</td>
                    <td className="py-4 font-bold text-sm">${tx.amount.toLocaleString()}</td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded text-[10px] font-bold ${tx.prediction === 'FRAUD' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                        {tx.prediction}
                      </span>
                    </td>
                    <td className="py-4">
                      <div className="flex flex-wrap gap-1">
                        {tx.explanation && JSON.parse(tx.explanation).map((reason, ridx) => (
                          <span key={ridx} className="bg-gray-100 text-[9px] px-1.5 py-0.5 rounded text-gray-500 border">
                            {reason}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-4 text-right text-xs text-gray-400">
                      {new Date(tx.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
