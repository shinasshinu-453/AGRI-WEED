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
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
        <div className="p-3 bg-red-100 text-red-600 rounded-lg">
          <AlertTriangle size={24} />
        </div>
        <div>
          <p className="text-sm text-slate-500 font-medium">Weeds Detected</p>
          <h4 className="text-2xl font-bold text-slate-800">{result.weedCount}</h4>
        </div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
        <div className="p-3 bg-emerald-100 text-emerald-600 rounded-lg">
          <Leaf size={24} />
        </div>
        <div>
          <p className="text-sm text-slate-500 font-medium">Crops Detected</p>
          <h4 className="text-2xl font-bold text-slate-800">
            {result.cropCount ? result.cropCount : ''}
          </h4>
        </div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
        <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
          <Activity size={24} />
        </div>
        <div>
          <p className="text-sm text-slate-500 font-medium">Infestation Rate</p>
          <h4 className="text-2xl font-bold text-slate-800">{weedPercentage}%</h4>
        </div>
      </div>
      
      <div className="col-span-1 md:col-span-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
        <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Analysis Summary</h5>
        <p className="text-slate-700 text-sm leading-relaxed">{result.summary}</p>
      </div>

      {result.actionPlan && (
        <div className="col-span-1 md:col-span-3 bg-emerald-50 p-4 rounded-xl border border-emerald-200">
          <h5 className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-2">Weed Control Plan (Gemini)</h5>
          <p className="text-slate-800 text-sm leading-relaxed whitespace-pre-line">{result.actionPlan}</p>
        </div>
      )}
    </div>
  );
};
