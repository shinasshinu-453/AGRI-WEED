import React from 'react';
import { AnalysisResult, ModelStats, Detection } from '../types';
import {
    Cpu, Globe, AlertTriangle, Leaf, Clock, CheckCircle,
    XCircle, BarChart2, TrendingUp, Zap, Activity
} from 'lucide-react';

interface ModelDashboardProps {
    result: AnalysisResult | null;
}

const ConfidenceBadge: React.FC<{ value: number }> = ({ value }) => {
    const pct = Math.round(value * 100);
    const color =
        pct >= 75 ? { bg: '#dcfce7', text: '#15803d' } :
            pct >= 50 ? { bg: '#fef9c3', text: '#a16207' } :
                { bg: '#fee2e2', text: '#dc2626' };
    return (
        <span className="px-2.5 py-1 rounded-full text-xs font-bold" style={{ background: color.bg, color: color.text }}>
            {pct}%
        </span>
    );
};

const TypeBadge: React.FC<{ type: 'weed' | 'crop' }> = ({ type }) => (
    <span className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{
        background: type === 'weed' ? '#fef2f2' : '#f0fdf4',
        color: type === 'weed' ? '#dc2626' : '#15803d',
        border: type === 'weed' ? '1px solid #fecaca' : '1px solid #bbf7d0'
    }}>
        {type === 'weed' ? '🌿 Weed' : '🌾 Crop'}
    </span>
);

const ModelCard: React.FC<{
    stats: ModelStats;
    icon: React.ReactNode;
    title: string;
    accentColor: string;
    badgeLabel: string;
}> = ({ stats, icon, title, accentColor, badgeLabel }) => {
    const total = stats.weedCount + stats.cropCount;
    const weedPct = total > 0 ? Math.round((stats.weedCount / total) * 100) : 0;
    const cropPct = total > 0 ? Math.round((stats.cropCount / total) * 100) : 0;

    return (
        <div className="rounded-2xl p-6 flex flex-col gap-4 transition-all duration-300 hover:shadow-md" style={{ background: '#ffffff', border: '1px solid #d8ddd3' }}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                    {icon}
                    <span className="font-bold text-sm" style={{ color: '#0a3d2e' }}>{title}</span>
                </div>
                <span className="text-[11px] font-semibold px-3 py-1 rounded-full" style={{ background: '#eef0ea', color: '#5a7265', border: '1px solid #d8ddd3' }}>
                    {badgeLabel}
                </span>
            </div>

            {/* Error state */}
            {stats.error && (
                <div className="flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs" style={{ background: '#fef2f2', color: '#dc2626' }}>
                    <XCircle size={14} />
                    <span>{stats.error}</span>
                </div>
            )}

            {/* Stat row */}
            <div className="grid grid-cols-3 gap-3">
                <div className="rounded-xl p-3.5 text-center" style={{ background: '#fef2f2' }}>
                    <p className="text-2xl font-black" style={{ color: '#dc2626' }}>{stats.weedCount}</p>
                    <p className="text-[11px] mt-0.5" style={{ color: '#5a7265' }}>Weeds</p>
                </div>
                <div className="rounded-xl p-3.5 text-center" style={{ background: '#f0fdf4' }}>
                    <p className="text-2xl font-black" style={{ color: '#15803d' }}>{stats.cropCount}</p>
                    <p className="text-[11px] mt-0.5" style={{ color: '#5a7265' }}>Crops</p>
                </div>
                <div className="rounded-xl p-3.5 text-center" style={{ background: '#eef0ea' }}>
                    <p className="text-2xl font-black" style={{ color: '#0a3d2e' }}>{stats.count}</p>
                    <p className="text-[11px] mt-0.5" style={{ color: '#5a7265' }}>Total</p>
                </div>
            </div>

            {/* Progress bars */}
            {total > 0 && (
                <div className="space-y-2.5">
                    <div>
                        <div className="flex justify-between text-[11px] mb-1">
                            <span className="font-medium" style={{ color: '#dc2626' }}>Weeds</span>
                            <span style={{ color: '#5a7265' }}>{weedPct}%</span>
                        </div>
                        <div className="h-2 rounded-full overflow-hidden" style={{ background: '#eef0ea' }}>
                            <div
                                className="h-full rounded-full transition-all duration-700"
                                style={{ width: `${weedPct}%`, background: 'linear-gradient(90deg, #ef4444, #f87171)' }}
                            />
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-[11px] mb-1">
                            <span className="font-medium" style={{ color: '#15803d' }}>Crops</span>
                            <span style={{ color: '#5a7265' }}>{cropPct}%</span>
                        </div>
                        <div className="h-2 rounded-full overflow-hidden" style={{ background: '#eef0ea' }}>
                            <div
                                className="h-full rounded-full transition-all duration-700"
                                style={{ width: `${cropPct}%`, background: 'linear-gradient(90deg, #22c55e, #4ade80)' }}
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Inference time */}
            <div className="flex items-center gap-1.5 text-xs mt-auto pt-3" style={{ borderTop: '1px solid #eef0ea', color: '#5a7265' }}>
                <Clock size={12} />
                <span>Inference: <span className="font-medium" style={{ color: '#0a3d2e' }}>{stats.inferenceTime?.toFixed(3)}s</span></span>
            </div>
        </div>
    );
};

const DetectionTable: React.FC<{ detections: Detection[]; model: string }> = ({ detections, model }) => {
    if (!detections || detections.length === 0) return null;
    return (
        <div>
            <h5 className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: '#5a7265' }}>
                {model} — {detections.length} detection{detections.length !== 1 ? 's' : ''}
            </h5>
            <div className="rounded-xl overflow-hidden" style={{ border: '1px solid #d8ddd3' }}>
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-xs" style={{ background: '#eef0ea', color: '#5a7265' }}>
                            <th className="text-left px-4 py-2.5 font-semibold">Label</th>
                            <th className="text-left px-4 py-2.5 font-semibold">Type</th>
                            <th className="text-right px-4 py-2.5 font-semibold">Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {detections.map((det, i) => (
                            <tr
                                key={i}
                                className="transition-colors hover:bg-[#f8f9f6]"
                                style={{ borderTop: '1px solid #eef0ea' }}
                            >
                                <td className="px-4 py-2.5 font-medium text-xs" style={{ color: '#0a3d2e' }}>{det.label}</td>
                                <td className="px-4 py-2.5">
                                    <TypeBadge type={det.type} />
                                </td>
                                <td className="px-4 py-2.5 text-right">
                                    <ConfidenceBadge value={det.confidence} />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const EmptyState: React.FC = () => (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
        <div className="relative">
            <div className="w-20 h-20 rounded-full flex items-center justify-center" style={{ background: '#eef0ea' }}>
                <BarChart2 size={36} style={{ color: '#5a9e6f' }} />
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center" style={{ background: '#d4f04d' }}>
                <Activity size={12} style={{ color: '#0a3d2e' }} />
            </div>
        </div>
        <div>
            <p className="font-bold text-lg" style={{ color: '#0a3d2e' }}>No Analysis Yet</p>
            <p className="text-sm mt-1 max-w-xs" style={{ color: '#5a7265' }}>
                Run a detection from <strong>Camera Capture</strong> or <strong>Upload</strong> to see the dual-model breakdown here.
            </p>
        </div>
    </div>
);

const ModelDashboard: React.FC<ModelDashboardProps> = ({ result }) => {
    const dual = result?._dualModel;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl" style={{ background: '#d4f04d' }}>
                    <BarChart2 size={22} style={{ color: '#0a3d2e' }} />
                </div>
                <div>
                    <h2 className="text-xl font-bold" style={{ color: '#0a3d2e' }}>Model <span className="serif-accent">Dashboard</span></h2>
                    <p className="text-xs" style={{ color: '#5a7265' }}>YOLOv11 vs Roboflow — side-by-side comparison</p>
                </div>
                {dual && (
                    <div className="ml-auto flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full" style={{ background: '#f0fdf4', color: '#15803d', border: '1px solid #bbf7d0' }}>
                        <CheckCircle size={12} />
                        <span className="font-medium">Analysis complete</span>
                    </div>
                )}
            </div>

            {!dual ? (
                <div className="rounded-2xl" style={{ background: '#f3f4f1', border: '1px solid #d8ddd3' }}>
                    <EmptyState />
                </div>
            ) : (
                <>
                    {/* Summary strip */}
                    <div className="grid grid-cols-3 gap-4">
                        <div className="rounded-2xl p-5 flex items-center gap-3" style={{ background: '#eef0ea', border: '1px solid #d8ddd3' }}>
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: '#d4f04d' }}>
                                <TrendingUp size={18} style={{ color: '#0a3d2e' }} />
                            </div>
                            <div>
                                <p className="text-xs" style={{ color: '#5a7265' }}>Total Detections</p>
                                <p className="text-2xl font-black" style={{ color: '#0a3d2e' }}>{result.detections.length}</p>
                            </div>
                        </div>
                        <div className="rounded-2xl p-5 flex items-center gap-3" style={{ background: '#fef2f2', border: '1px solid #fecaca' }}>
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: '#fee2e2' }}>
                                <AlertTriangle size={18} style={{ color: '#dc2626' }} />
                            </div>
                            <div>
                                <p className="text-xs" style={{ color: '#5a7265' }}>Weeds Found</p>
                                <p className="text-2xl font-black" style={{ color: '#dc2626' }}>{result.weedCount}</p>
                            </div>
                        </div>
                        <div className="rounded-2xl p-5 flex items-center gap-3" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: '#dcfce7' }}>
                                <Leaf size={18} style={{ color: '#15803d' }} />
                            </div>
                            <div>
                                <p className="text-xs" style={{ color: '#5a7265' }}>Crops Found</p>
                                <p className="text-2xl font-black" style={{ color: '#15803d' }}>{result.cropCount}</p>
                            </div>
                        </div>
                    </div>

                    {/* Speed comparison */}
                    {(dual.yolo.inferenceTime != null || dual.roboflow.inferenceTime != null) && (
                        <div className="rounded-2xl p-5" style={{ background: '#ffffff', border: '1px solid #d8ddd3' }}>
                            <div className="flex items-center gap-2 mb-4">
                                <Zap size={14} style={{ color: '#d4a040' }} />
                                <span className="text-xs font-bold uppercase tracking-widest" style={{ color: '#5a7265' }}>Inference Speed</span>
                            </div>
                            <div className="space-y-3">
                                {/* YOLO bar */}
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="font-medium flex items-center gap-1" style={{ color: '#0a3d2e' }}>
                                            <Cpu size={11} /> YOLOv11
                                        </span>
                                        <span style={{ color: '#5a7265' }}>{dual.yolo.inferenceTime?.toFixed(3)}s</span>
                                    </div>
                                    <div className="h-3 rounded-full overflow-hidden" style={{ background: '#eef0ea' }}>
                                        <div
                                            className="h-full rounded-full transition-all duration-700"
                                            style={{ width: `${Math.min(100, (dual.yolo.inferenceTime / Math.max(dual.yolo.inferenceTime, dual.roboflow.inferenceTime)) * 100)}%`, background: 'linear-gradient(90deg, #0a3d2e, #5a9e6f)' }}
                                        />
                                    </div>
                                </div>
                                {/* Roboflow bar */}
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="font-medium flex items-center gap-1" style={{ color: '#0a3d2e' }}>
                                            <Globe size={11} /> Roboflow
                                        </span>
                                        <span style={{ color: '#5a7265' }}>{dual.roboflow.inferenceTime?.toFixed(3)}s</span>
                                    </div>
                                    <div className="h-3 rounded-full overflow-hidden" style={{ background: '#eef0ea' }}>
                                        <div
                                            className="h-full rounded-full transition-all duration-700"
                                            style={{ width: `${Math.min(100, (dual.roboflow.inferenceTime / Math.max(dual.yolo.inferenceTime, dual.roboflow.inferenceTime)) * 100)}%`, background: 'linear-gradient(90deg, #d4f04d, #a8cc3a)' }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Model cards side by side */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <ModelCard
                            stats={dual.yolo}
                            icon={<Cpu size={18} style={{ color: '#0a3d2e' }} />}
                            title="YOLOv11 — Local Model"
                            accentColor="border-primary/30 text-primary"
                            badgeLabel="12 Weed Classes"
                        />
                        <ModelCard
                            stats={dual.roboflow}
                            icon={<Globe size={18} style={{ color: '#5a9e6f' }} />}
                            title="Roboflow — Cloud API"
                            accentColor="border-violet-500/30 text-violet-400"
                            badgeLabel="crop / weed"
                        />
                    </div>

                    {/* Detection tables */}
                    <div className="rounded-2xl p-6 space-y-6" style={{ background: '#ffffff', border: '1px solid #d8ddd3' }}>
                        <div className="flex items-center gap-2">
                            <Activity size={14} style={{ color: '#5a7265' }} />
                            <span className="text-xs font-bold uppercase tracking-widest" style={{ color: '#5a7265' }}>Detection Breakdown</span>
                        </div>
                        <DetectionTable detections={dual.yolo.detections} model="🎯 YOLOv11" />
                        <DetectionTable detections={dual.roboflow.detections} model="🌐 Roboflow" />
                    </div>
                </>
            )}
        </div>
    );
};

export default ModelDashboard;
