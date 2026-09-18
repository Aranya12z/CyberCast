import React from 'react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  CartesianGrid 
} from 'recharts';

export const RiskDistributionChart = ({ predictions = [] }) => {
  if (!predictions || predictions.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-500 font-mono">
        No candidate data to display on distribution chart.
      </div>
    );
  }

  const chartData = predictions.map((p, index) => ({
    name: p.bank ? p.bank.split(' ')[0] : `Rank ${index + 1}`,
    fullName: `${p.bank || p.atm_id} (${p.area || ''})`,
    atm_id: p.atm_id,
    risk: Math.round(p.risk_score * 100),
    confidence: Math.round(p.confidence * 100)
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass-panel p-3 rounded-xl border border-slate-700 font-sans shadow-xl text-xs space-y-1">
          <div className="font-bold text-white">{data.fullName}</div>
          <div className="text-[11px] font-mono text-slate-400">{data.atm_id}</div>
          <div className="pt-1 text-red-400 font-mono font-semibold">
            Risk Likelihood: {data.risk}%
          </div>
          <div className="text-indigo-400 font-mono font-semibold">
            Model Certainty: {data.confidence}%
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis 
            dataKey="name" 
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
          />
          <YAxis 
            domain={[0, 100]} 
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            unit="%"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: '10px', fontSize: '11px', fontFamily: 'monospace' }} 
          />
          <Bar 
            dataKey="risk" 
            name="Risk Likelihood (%)" 
            fill="#ef4444" 
            radius={[4, 4, 0, 0]} 
          />
          <Bar 
            dataKey="confidence" 
            name="Model Certainty (%)" 
            fill="#6366f1" 
            radius={[4, 4, 0, 0]} 
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
