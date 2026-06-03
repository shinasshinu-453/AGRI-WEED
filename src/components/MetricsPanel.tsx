import React from 'react';
import { AnalysisResult } from '../types';
import { AlertTriangle, Leaf, Activity } from 'lucide-react';

interface MetricsPanelProps {
  result: AnalysisResult;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ result }) => {
  const total = result.weedCount + result.cropCount;
  const weedPercentage = total > 0 ? Math.round((result.weedCount / total) * 100) : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="p-5 rounded-2xl flex items-center space-x-4" style={{ background: '#ffffff', border: '1px solid #d8ddd3' }}>
        <div className="p-3 rounded-xl" style={{ background: '#fef2f2' }}>
          <AlertTriangle size={24} className="text-red-500" />
        </div>
        <div>
          <p className="text-sm font-medium" style={{ color: '#5a7265' }}>Weeds Detected</p>
          <h4 className="text-2xl font-black" style={{ color: '#0a3d2e' }}>{result.weedCount}</h4>
        </div>
      </div>

      <div className="p-5 rounded-2xl flex items-center space-x-4" style={{ background: '#ffffff', border: '1px solid #d8ddd3' }}>
        <div className="p-3 rounded-xl" style={{ background: '#f0fdf4' }}>
          <Leaf size={24} style={{ color: '#15803d' }} />
        </div>
        <div>
          <p className="text-sm font-medium" style={{ color: '#5a7265' }}>Crops Detected</p>
          <h4 className="text-2xl font-black" style={{ color: '#0a3d2e' }}>
            {result.cropCount ? result.cropCount : ''}
          </h4>
        </div>
      </div>

      <div className="p-5 rounded-2xl flex items-center space-x-4" style={{ background: '#ffffff', border: '1px solid #d8ddd3' }}>
        <div className="p-3 rounded-xl" style={{ background: '#eef0ea' }}>
          <Activity size={24} style={{ color: '#0a3d2e' }} />
        </div>
        <div>
          <p className="text-sm font-medium" style={{ color: '#5a7265' }}>Infestation Rate</p>
          <h4 className="text-2xl font-black" style={{ color: '#0a3d2e' }}>{weedPercentage}%</h4>
        </div>
      </div>
      
      <div className="col-span-1 md:col-span-3 p-5 rounded-2xl" style={{ background: '#f3f4f1', border: '1px solid #d8ddd3' }}>
        <h5 className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: '#5a7265' }}>Analysis Summary</h5>
        <p className="text-sm leading-relaxed" style={{ color: '#0a3d2e' }}>{result.summary}</p>
      </div>

      {result.actionPlan && (
        <div className="col-span-1 md:col-span-3 p-5 rounded-2xl" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
          <h5 className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: '#15803d' }}>Weed Control Plan (Gemini)</h5>
          <p className="text-sm leading-relaxed whitespace-pre-line" style={{ color: '#0a3d2e' }}>{result.actionPlan}</p>
        </div>
      )}
    </div>
  );
};
