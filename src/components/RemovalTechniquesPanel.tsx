import React, { useState } from 'react';
import { RemovalTechniques } from '../types';

interface RemovalTechniquesPanelProps {
    techniques: RemovalTechniques;
}

const RemovalTechniquesPanel: React.FC<RemovalTechniquesPanelProps> = ({ techniques }) => {
    const [expandedMethod, setExpandedMethod] = useState<string | null>(techniques.priority);

    const methodIcons: Record<string, string> = {
        manual: '✋',
        chemical: '🧪',
        organic: '🌱',
        mechanical: '🚜'
    };

    const methodColors: Record<string, string> = {
        manual: '#3b82f6',
        chemical: '#ef4444',
        organic: '#22c55e',
        mechanical: '#f59e0b'
    };

    const methodLabels: Record<string, string> = {
        manual: 'Manual Removal',
        chemical: 'Chemical Treatment',
        organic: 'Organic Methods',
        mechanical: 'Mechanical Removal'
    };

    const methods = ['manual', 'chemical', 'organic', 'mechanical'] as const;

    return (
        <div className="removal-techniques-panel" style={{
            backgroundColor: '#ffffff',
            border: '1px solid #d8ddd3',
            borderRadius: '20px',
            padding: '20px',
            marginBottom: '20px',
            boxShadow: '0 2px 16px rgba(10, 61, 46, 0.06)'
        }}>
            <div style={{ marginBottom: '16px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#0a3d2e' }}>
                    🌿 Weed Removal Techniques
                </h3>
                {techniques.timing && (
                    <div style={{
                        backgroundColor: '#fef3c7',
                        border: '1px solid #fbbf24',
                        borderRadius: '8px',
                        padding: '10px',
                        marginTop: '12px'
                    }}>
                        <p style={{ margin: 0, fontSize: '14px', color: '#92400e' }}>
                            <strong>⏰ Optimal Timing:</strong> {techniques.timing}
                        </p>
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {methods.map((method) => {
                    const content = techniques[method];
                    if (!content) return null;

                    const isPriority = method === techniques.priority;
                    const isExpanded = expandedMethod === method;

                    return (
                        <div
                            key={method}
                            style={{
                                border: isPriority ? `3px solid ${methodColors[method]}` : '2px solid #e5e7eb',
                                borderRadius: '8px',
                                overflow: 'hidden',
                                transition: 'all 0.2s ease',
                                backgroundColor: isPriority ? `${methodColors[method]}10` : '#ffffff'
                            }}
                        >
                            <div
                                onClick={() => setExpandedMethod(isExpanded ? null : method)}
                                style={{
                                    padding: '14px 16px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    backgroundColor: isPriority ? `${methodColors[method]}20` : 'transparent'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <span style={{ fontSize: '24px' }}>{methodIcons[method]}</span>
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <span style={{
                                                fontSize: '16px',
                                                fontWeight: '600',
                                                color: methodColors[method]
                                            }}>
                                                {methodLabels[method]}
                                            </span>
                                            {isPriority && (
                                                <span style={{
                                                    backgroundColor: methodColors[method],
                                                    color: 'white',
                                                    padding: '2px 8px',
                                                    borderRadius: '12px',
                                                    fontSize: '12px',
                                                    fontWeight: '600'
                                                }}>
                                                    RECOMMENDED
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <span style={{
                                    fontSize: '20px',
                                    transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                                    transition: 'transform 0.2s ease'
                                }}>
                                    ▼
                                </span>
                            </div>

                            {isExpanded && (
                                <div style={{
                                    padding: '16px',
                                    borderTop: `1px solid ${isPriority ? methodColors[method] : '#e5e7eb'}`,
                                    backgroundColor: '#f9fafb'
                                }}>
                                    <p style={{
                                        margin: 0,
                                        fontSize: '14px',
                                        lineHeight: '1.6',
                                        color: '#374151'
                                    }}>
                                        {content}
                                    </p>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default RemovalTechniquesPanel;
