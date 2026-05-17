import React from 'react';
import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="min-h-screen bg-indigo-900 text-white font-sans">
      <nav class="p-6 flex justify-between items-center max-w-7xl mx-auto">
        <div class="text-2xl font-bold flex items-center">
          <span class="mr-2">🛡️</span> FraudEye Pro
        </div>
        <div class="space-x-4">
          <Link to="/login" class="px-4 py-2 rounded hover:bg-indigo-800">Login</Link>
          <Link to="/login" class="px-6 py-2 bg-indigo-500 rounded-full font-bold hover:bg-indigo-400">Get Started</Link>
        </div>
      </nav>

      <main class="max-w-7xl mx-auto px-6 py-20 text-center">
        <h1 class="text-6xl font-black mb-6">Real-time Fraud Intelligence <br/><span class="text-indigo-400">for the Next Generation.</span></h1>
        <p class="text-xl text-indigo-200 mb-10 max-w-3xl mx-auto">
          Protect your financial ecosystem with advanced ML risk scoring, SIEM-integrated alerts, 
          and production-ready cybersecurity monitoring.
        </p>
        <div class="flex justify-center space-x-6">
          <button class="px-10 py-4 bg-white text-indigo-900 rounded-lg font-bold text-lg hover:bg-indigo-100">Live Demo</button>
          <button class="px-10 py-4 border-2 border-indigo-400 rounded-lg font-bold text-lg hover:bg-indigo-800">API Documentation</button>
        </div>
        
        <div class="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="p-8 bg-indigo-800 rounded-2xl">
            <div class="text-4xl mb-4">🧠</div>
            <h3 class="text-xl font-bold mb-2">Hybrid-ML Engine</h3>
            <p class="text-indigo-200">Combining deep learning with heuristic fraud rules for maximum coverage.</p>
          </div>
          <div class="p-8 bg-indigo-800 rounded-2xl">
            <div class="text-4xl mb-4">⚡</div>
            <h3 class="text-xl font-bold mb-2">Sub-40ms Latency</h3>
            <p class="text-indigo-200">Blazing fast prediction endpoints designed for high-frequency trading.</p>
          </div>
          <div class="p-8 bg-indigo-800 rounded-2xl">
            <div class="text-4xl mb-4">📜</div>
            <h3 class="text-xl font-bold mb-2">Compliance Ready</h3>
            <p class="text-indigo-200">Automated audit logging mapped to PCI-DSS and RBI guidelines.</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Landing;
