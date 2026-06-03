import { AnalysisResult } from '../types';

export const exportToCSV = (results: AnalysisResult[], filename: string = 'detections.csv'): void => {
    // CSV Headers
    const headers = [
        'Filename',
        'Timestamp',
        'Weeds Detected',
        'Crops Detected',
        'Location',
        'Crop Type',
        'Summary',
    ];

    // Convert results to CSV rows
    const rows = results.map((result, index) => {
        const location = (result as any).location
            ? `"${(result as any).location.latitude},${(result as any).location.longitude}"`
            : 'N/A';

        const timestamp = new Date().toISOString();
        const filename = `image_${index + 1}.jpg`;

        return [
            filename,
            timestamp,
            result.weedCount || 0,
            result.cropCount || 0,
            location,
            (result as any).cropType || 'Unknown',
            `"${result.summary || 'No summary'}"`,
        ].join(',');
    });

    // Combine headers and rows
    const csv = [headers.join(','), ...rows].join('\n');

    // Create and download file
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

export const exportToJSON = (results: AnalysisResult[], filename: string = 'detections.json'): void => {
    const data = {
        exportDate: new Date().toISOString(),
        totalResults: results.length,
        results: results.map((result, index) => ({
            id: index + 1,
            weedCount: result.weedCount || 0,
            cropCount: result.cropCount || 0,
            detections: result.detections || [],
            summary: result.summary || '',
            identifiedCrop: result.identifiedCrop || null,
            removalTechniques: result.removalTechniques || null,
            actionPlan: result.actionPlan || '',
            location: (result as any).location || null,
            cropType: (result as any).cropType || 'Unknown',
        })),
    };

    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

export const exportToExcel = (results: AnalysisResult[], filename: string = 'detections.xlsx'): void => {
    // For future implementation with a library like xlsx or exceljs
    console.warn('Excel export not yet implemented, falling back to CSV');
    exportToCSV(results, filename.replace('.xlsx', '.csv'));
};

export const generateSummaryReport = (results: AnalysisResult[]): string => {
    const totalWeeds = results.reduce((sum, r) => sum + (r.weedCount || 0), 0);
    const totalCrops = results.reduce((sum, r) => sum + (r.cropCount || 0), 0);
    const avgWeedsPerImage = (totalWeeds / results.length).toFixed(1);
    const avgCropsPerImage = (totalCrops / results.length).toFixed(1);

    return `
Batch Analysis Summary Report
Generated: ${new Date().toLocaleString()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Images Analyzed: ${results.length}
Total Weeds Detected: ${totalWeeds}
Total Crops Detected: ${totalCrops}

Average Weeds per Image: ${avgWeedsPerImage}
Average Crops per Image: ${avgCropsPerImage}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`.trim();
};
