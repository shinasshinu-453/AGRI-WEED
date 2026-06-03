import React, { useState } from 'react';
import { AnalysisResult } from '../types';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Download, FileJson, FileSpreadsheet, CheckSquare, Square, Grid3x3, List } from 'lucide-react';
import { exportToCSV, exportToJSON, generateSummaryReport } from '../utils/exportUtils';
import toast from 'react-hot-toast';

interface BatchResultsPanelProps {
    results: Array<{
        id: string;
        filename: string;
        result: AnalysisResult;
        timestamp: string;
    }>;
    onClear?: () => void;
}

export const BatchResultsPanel: React.FC<BatchResultsPanelProps> = ({ results, onClear }) => {
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    const toggleSelect = (id: string) => {
        setSelectedIds((prev) => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === results.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(results.map((r) => r.id)));
        }
    };

    const handleExportCSV = () => {
        const selectedResults = results
            .filter((r) => selectedIds.has(r.id))
            .map((r) => ({ ...r.result, cropType: r.filename } as any));

        if (selectedResults.length === 0) {
            toast.error('No results selected for export');
            return;
        }

        exportToCSV(selectedResults, `batch_detections_${Date.now()}.csv`);
        toast.success(`Exported ${selectedResults.length} results to CSV`);
    };

    const handleExportJSON = () => {
        const selectedResults = results
            .filter((r) => selectedIds.has(r.id))
            .map((r) => ({ ...r.result, filename: r.filename, timestamp: r.timestamp } as any));

        if (selectedResults.length === 0) {
            toast.error('No results selected for export');
            return;
        }

        exportToJSON(selectedResults, `batch_detections_${Date.now()}.json`);
        toast.success(`Exported ${selectedResults.length} results to JSON`);
    };

    const handleDownloadSummary = () => {
        const selectedResults = results
            .filter((r) => selectedIds.has(r.id))
            .map((r) => r.result);

        if (selectedResults.length === 0) {
            toast.error('No results selected');
            return;
        }

        const summary = generateSummaryReport(selectedResults);
        const blob = new Blob([summary], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `batch_summary_${Date.now()}.txt`;
        link.click();
        URL.revokeObjectURL(url);
        toast.success('Summary report downloaded');
    };

    if (results.length === 0) {
        return (
            <Card className="p-12 text-center glass-effect border-white/20">
                <p className="text-muted-foreground">No batch results yet. Upload and process images to see results here.</p>
            </Card>
        );
    }

    const totalWeeds = results.reduce((sum, r) => sum + (r.result.weedCount || 0), 0);
    const totalCrops = results.reduce((sum, r) => sum + (r.result.cropCount || 0), 0);

    return (
        <div className="space-y-4">
            {/* Summary Header */}
            <Card className="p-4 glass-effect border-white/20">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-bold">Batch Results ({results.length} images)</h3>
                        <p className="text-sm text-muted-foreground">
                            {totalWeeds} weeds • {totalCrops} crops detected
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            size="sm"
                            variant={viewMode === 'grid' ? 'default' : 'outline'}
                            onClick={() => setViewMode('grid')}
                        >
                            <Grid3x3 size={16} />
                        </Button>
                        <Button
                            size="sm"
                            variant={viewMode === 'list' ? 'default' : 'outline'}
                            onClick={() => setViewMode('list')}
                        >
                            <List size={16} />
                        </Button>
                    </div>
                </div>

                <div className="flex flex-wrap gap-2">
                    <Button size="sm" variant="outline" onClick={toggleSelectAll} className="gap-2">
                        {selectedIds.size === results.length ? <CheckSquare size={16} /> : <Square size={16} />}
                        {selectedIds.size === results.length ? 'Deselect All' : 'Select All'}
                    </Button>
                    <Button size="sm" onClick={handleExportCSV} disabled={selectedIds.size === 0} className="gap-2">
                        <FileSpreadsheet size={16} />
                        Export CSV ({selectedIds.size})
                    </Button>
                    <Button size="sm" onClick={handleExportJSON} disabled={selectedIds.size === 0} className="gap-2">
                        <FileJson size={16} />
                        Export JSON ({selectedIds.size})
                    </Button>
                    <Button size="sm" variant="outline" onClick={handleDownloadSummary} disabled={selectedIds.size === 0} className="gap-2">
                        <Download size={16} />
                        Summary Report
                    </Button>
                    {onClear && (
                        <Button size="sm" variant="destructive" onClick={onClear}>
                            Clear All
                        </Button>
                    )}
                </div>
            </Card>

            {/* Results Grid/List */}
            <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-3'}>
                {results.map((item) => (
                    <Card
                        key={item.id}
                        className={`p-4 cursor-pointer transition-all hover:shadow-lg ${selectedIds.has(item.id) ? 'ring-2 ring-primary bg-primary/5' : 'glass-effect border-white/20'
                            }`}
                        onClick={() => toggleSelect(item.id)}
                    >
                        <div className="flex items-start gap-3">
                            <div className="mt-1">
                                {selectedIds.has(item.id) ? (
                                    <CheckSquare size={20} className="text-primary" />
                                ) : (
                                    <Square size={20} className="text-muted-foreground" />
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <h4 className="font-semibold truncate">{item.filename}</h4>
                                <p className="text-xs text-muted-foreground mb-2">
                                    {new Date(item.timestamp).toLocaleString()}
                                </p>
                                <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div className="bg-red-50 dark:bg-red-950/20 rounded px-2 py-1">
                                        <p className="text-xs text-red-600 dark:text-red-400">Weeds</p>
                                        <p className="font-bold text-red-700 dark:text-red-300">{item.result.weedCount || 0}</p>
                                    </div>
                                    <div className="bg-green-50 dark:bg-green-950/20 rounded px-2 py-1">
                                        <p className="text-xs text-green-600 dark:text-green-400">Crops</p>
                                        <p className="font-bold text-green-700 dark:text-green-300">{item.result.cropCount || 0}</p>
                                    </div>
                                </div>
                                {item.result.summary && (
                                    <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                                        {item.result.summary}
                                    </p>
                                )}
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};
