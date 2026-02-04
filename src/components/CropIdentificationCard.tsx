import React from 'react';
import { CropIdentification } from '../types';

interface CropIdentificationCardProps {
    cropData: CropIdentification;
}

const CropIdentificationCard: React.FC<CropIdentificationCardProps> = ({ cropData }) => {
    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.8) return '#22c55e'; // green
        if (confidence >= 0.6) return '#eab308'; // yellow
        return '#ef4444'; // red
    };

    const getConfidenceLabel = (confidence: number) => {
        if (confidence >= 0.8) return 'High';
        if (confidence >= 0.6) return 'Medium';
        return 'Low';
    };

    return (
        <div className="crop-identification-card" style={{
            backgroundColor: '#ffffff',
            border: '2px solid #e5e7eb',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '24px', marginRight: '12px' }}>🌾</span>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                    Identified Crop
                </h3>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                    <p style={{ margin: 0, fontSize: '24px', fontWeight: '700', color: '#1f2937' }}>
                        {cropData.cropName}
                    </p>
                </div>
                <div style={{
                    backgroundColor: getConfidenceColor(cropData.confidence),
                    color: 'white',
                    padding: '6px 12px',
                    borderRadius: '20px',
                    fontSize: '14px',
                    fontWeight: '600'
                }}>
                    {getConfidenceLabel(cropData.confidence)} ({(cropData.confidence * 100).toFixed(0)}%)
                </div>
            </div>

            {cropData.characteristics && (
                <div style={{
                    backgroundColor: '#f9fafb',
                    padding: '12px',
                    borderRadius: '8px',
                    marginTop: '12px'
                }}>
                    <p style={{
                        margin: 0,
                        fontSize: '14px',
                        color: '#6b7280',
                        lineHeight: '1.6'
                    }}>
                        <strong>Characteristics:</strong> {cropData.characteristics}
                    </p>
                </div>
            )}
        </div>
    );
};

export default CropIdentificationCard;
