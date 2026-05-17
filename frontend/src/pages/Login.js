import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const res = await axios.post('/api/auth/login', formData);
      localStorage.setItem('token', res.data.access_token);
      navigate('/dashboard');
    } catch (err) {
      alert("Login Failed: Check your credentials");
    }
  };

  return (
    <div className="min-h-screen bg-indigo-900 flex items-center justify-center p-6">
      <div className="bg-white p-10 rounded-3xl shadow-2xl w-full max-w-md">
        <h2 className="text-3xl font-black text-indigo-900 mb-2">Welcome Back</h2>
        <p className="text-gray-500 mb-8">Login to your FraudEye Pro account</p>
        
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase">Email Address</label>
            <input 
              type="email" 
              className="w-full p-4 bg-gray-50 border border-gray-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
              placeholder="admin@fraudeye.pro"
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase">Password</label>
            <input 
              type="password" 
              className="w-full p-4 bg-gray-50 border border-gray-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
              placeholder="••••••••"
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button className="w-full py-4 bg-indigo-600 text-white rounded-xl font-black text-lg hover:bg-indigo-700 transition shadow-lg shadow-indigo-200">
            Authorize Access
          </button>
        </form>
        
        <p className="mt-8 text-center text-gray-400 text-sm">
          Protected by AES-256 Encryption & ML Sentinel
        </p>
      </div>
    </div>
  );
};

export default Login;
