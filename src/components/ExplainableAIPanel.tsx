import React, { useState } from 'react';
import { XAIExplanation } from '../types';

interface ExplainableAIPanelProps {
    explanation: XAIExplanation;
}

const ExplainableAIPanel: React.FC<ExplainableAIPanelProps> = ({ explanation }) => {
    const [expandedSection, setExpandedSection] = useState<string | null>('spray');
    const [showReasons, setShowReasons] = useState<Record<string, boolean>>({});

    const toggleReason = (id: string) => {
        setShowReasons(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const { features, sprayingAngle, weatherSuitability, herbicides, featureImportance, overallConfidence } = explanation;

    // Confidence color
    const getConfColor = (conf: number) => {
        if (conf >= 0.8) return '#22c55e';
        if (conf >= 0.6) return '#f59e0b';
        if (conf >= 0.4) return '#f97316';
        return '#ef4444';
    };

    // Pattern label
    const patternLabels: Record<string, string> = {
        directional: '🎯 Directional Spray',
        broadcast: '📡 Broadcast Spray',
        'inter-row': '↔️ Inter-Row Spray',
        spot: '📍 Spot Spray',
    };

    return (
        <div style={{
            backgroundColor: '#0a3d2e',
            border: '2px solid #0f5240',
            borderRadius: '20px',
            padding: '24px',
            marginBottom: '20px',
            boxShadow: '0 8px 32px rgba(10, 61, 46, 0.15)',
            color: '#e8f0ec',
            fontFamily: "'Inter', 'Segoe UI', sans-serif",
        }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '24px',
                paddingBottom: '16px',
                borderBottom: '1px solid #0f5240',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '12px',
                        background: 'linear-gradient(135deg, #d4f04d, #a8cc3a)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '24px',
                    }}>
                        🧠
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: '20px', fontWeight: '700', color: '#f8fafc' }}>
                            Explainable AI Analysis
                        </h3>
                        <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>
                            Feature-driven recommendations from YOLO detection data
                        </p>
                    </div>
                </div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 16px',
                    borderRadius: '24px',
                    backgroundColor: `${getConfColor(overallConfidence)}15`,
                    border: `1px solid ${getConfColor(overallConfidence)}40`,
                }}>
                    <div style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        backgroundColor: getConfColor(overallConfidence),
                        boxShadow: `0 0 8px ${getConfColor(overallConfidence)}`,
                    }} />
                    <span style={{ fontSize: '14px', fontWeight: '600', color: getConfColor(overallConfidence) }}>
                        {(overallConfidence * 100).toFixed(0)}% Confidence
                    </span>
                </div>
            </div>

            {/* Feature Importance Section */}
            <SectionCard
                title="📊 Feature Importance"
                subtitle="Which YOLO features drove these recommendations"
                isOpen={expandedSection === 'importance'}
                onToggle={() => setExpandedSection(expandedSection === 'importance' ? null : 'importance')}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {featureImportance.map((fi, idx) => (
                        <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '13px', fontWeight: '600', color: '#e2e8f0' }}>{fi.feature}</span>
                                <span style={{ fontSize: '12px', color: '#94a3b8' }}>{(fi.importance * 100).toFixed(0)}%</span>
                            </div>
                            <div style={{
                                height: '8px',
                                borderRadius: '4px',
                                backgroundColor: '#0f5240',
                                overflow: 'hidden',
                            }}>
                                <div style={{
                                    height: '100%',
                                    width: `${fi.importance * 100}%`,
                                    borderRadius: '4px',
                                    background: `linear-gradient(90deg, ${getBarColor(idx)})`,
                                    transition: 'width 0.8s ease',
                                }} />
                            </div>
                            <p style={{ margin: 0, fontSize: '11px', color: '#8baa96', paddingLeft: '2px' }}>
                                {fi.description}
                            </p>
                        </div>
                    ))}
                </div>
            </SectionCard>

            {/* Spraying Angle Section */}
            <SectionCard
                title="🎯 Spraying Angle Recommendation"
                subtitle={patternLabels[sprayingAngle.pattern] || sprayingAngle.pattern}
                isOpen={expandedSection === 'spray'}
                onToggle={() => setExpandedSection(expandedSection === 'spray' ? null : 'spray')}
            >
                <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap' }}>
                    {/* SVG Spray Angle Diagram */}
                    <div style={{ flex: '0 0 auto' }}>
                        <SprayAngleDiagram
                            angle={sprayingAngle.angle}
                            pattern={sprayingAngle.pattern}
                        />
                    </div>
                    {/* Details */}
                    <div style={{ flex: 1, minWidth: '200px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                            <InfoChip label="Angle" value={`${sprayingAngle.angle}°`} color="#d4f04d" />
                            <InfoChip label="Pattern" value={sprayingAngle.pattern} color="#a8cc3a" />
                            <InfoChip label="Confidence" value={`${(sprayingAngle.confidence * 100).toFixed(0)}%`} color={getConfColor(sprayingAngle.confidence)} />
                            <InfoChip label="Nozzle" value={sprayingAngle.nozzleType.split('(')[0].trim()} color="#0ea5e9" />
                        </div>
                        <button
                            onClick={() => toggleReason('spray')}
                            style={{
                                background: 'none',
                                border: '1px solid #0f5240',
                                borderRadius: '8px',
                                padding: '8px 12px',
                                color: '#94a3b8',
                                cursor: 'pointer',
                                fontSize: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                transition: 'all 0.2s',
                            }}
                        >
                            🔍 {showReasons['spray'] ? 'Hide' : 'Show'} Reasoning
                        </button>
                        {showReasons['spray'] && (
                            <div style={{
                                marginTop: '12px',
                                padding: '12px',
                                backgroundColor: '#0f5240',
                                borderRadius: '8px',
                                borderLeft: '3px solid #d4f04d',
                            }}>
                                <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.6', color: '#c0d4c8' }}>
                                    {sprayingAngle.reasoning}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </SectionCard>

            {/* Weather Suitability Section */}
            <SectionCard
                title="🌤️ Weather Suitability"
                subtitle={`Score: ${weatherSuitability.score}/100 — ${weatherSuitability.canSpray ? '✅ OK to Spray' : '❌ Wait'}`}
                isOpen={expandedSection === 'weather'}
                onToggle={() => setExpandedSection(expandedSection === 'weather' ? null : 'weather')}
            >
                {/* Score Bar */}
                <div style={{ marginBottom: '20px' }}>
                    <div style={{
                        height: '12px',
                        borderRadius: '6px',
                        backgroundColor: '#0f5240',
                        overflow: 'hidden',
                        position: 'relative',
                    }}>
                        <div style={{
                            height: '100%',
                            width: `${weatherSuitability.score}%`,
                            borderRadius: '6px',
                            background: weatherSuitability.score >= 70
                                ? 'linear-gradient(90deg, #22c55e, #4ade80)'
                                : weatherSuitability.score >= 40
                                    ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                                    : 'linear-gradient(90deg, #ef4444, #f87171)',
                            transition: 'width 1s ease',
                        }} />
                    </div>
                </div>

                {/* Weather Factors */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                    <WeatherFactorCard
                        icon="🌡️"
                        label="Temperature"
                        value={`${weatherSuitability.temperature.value}${weatherSuitability.temperature.unit}`}
                        suitable={weatherSuitability.temperature.suitable}
                        reason={weatherSuitability.temperature.reason}
                    />
                    <WeatherFactorCard
                        icon="💨"
                        label="Wind"
                        value={`${weatherSuitability.wind.speed} km/h`}
                        suitable={weatherSuitability.wind.suitable}
                        reason={weatherSuitability.wind.reason}
                    />
                    <WeatherFactorCard
                        icon="💧"
                        label="Humidity"
                        value={`${weatherSuitability.humidity.value}%`}
                        suitable={weatherSuitability.humidity.suitable}
                        reason={weatherSuitability.humidity.reason}
                    />
                    <WeatherFactorCard
                        icon="🌧️"
                        label="Rain Risk"
                        value={`${weatherSuitability.precipitation.probability}%`}
                        suitable={weatherSuitability.precipitation.suitable}
                        reason={weatherSuitability.precipitation.reason}
                    />
                </div>

                {/* Overall Reason */}
                <div style={{
                    marginTop: '16px',
                    padding: '12px',
                    backgroundColor: weatherSuitability.canSpray ? '#22c55e10' : '#ef444410',
                    border: `1px solid ${weatherSuitability.canSpray ? '#22c55e30' : '#ef444430'}`,
                    borderRadius: '8px',
                }}>
                    <p style={{ margin: 0, fontSize: '13px', color: '#c0d4c8' }}>
                        {weatherSuitability.overallReason}
                    </p>
                </div>
            </SectionCard>

            {/* Herbicide Recommendations Section */}
            {herbicides.length > 0 && (
                <SectionCard
                    title="🧪 Herbicide Recommendations"
                    subtitle={`${herbicides.length} recommendation(s) — ranked by suitability`}
                    isOpen={expandedSection === 'herbicide'}
                    onToggle={() => setExpandedSection(expandedSection === 'herbicide' ? null : 'herbicide')}
                >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {herbicides.map((herb, idx) => (
                            <div key={idx} style={{
                                border: '1px solid #0f5240',
                                borderRadius: '12px',
                                overflow: 'hidden',
                                backgroundColor: '#083328',
                            }}>
                                {/* Herbicide Header */}
                                <div style={{
                                    padding: '16px',
                                    background: herb.safeForCrop
                                        ? 'linear-gradient(135deg, #22c55e08, #22c55e15)'
                                        : 'linear-gradient(135deg, #f5920008, #f5920015)',
                                    borderBottom: '1px solid #0f5240',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                }}>
                                    <div>
                                        <h5 style={{ margin: 0, fontSize: '15px', fontWeight: '600', color: '#f8fafc' }}>
                                            {herb.name}
                                        </h5>
                                        <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#94a3b8' }}>
                                            {herb.herbicideClass}
                                        </p>
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                        {herb.safeForCrop ? (
                                            <span style={{
                                                padding: '4px 10px',
                                                borderRadius: '12px',
                                                fontSize: '11px',
                                                fontWeight: '600',
                                                backgroundColor: '#22c55e20',
                                                color: '#4ade80',
                                                border: '1px solid #22c55e40',
                                            }}>✓ Crop Safe</span>
                                        ) : (
                                            <span style={{
                                                padding: '4px 10px',
                                                borderRadius: '12px',
                                                fontSize: '11px',
                                                fontWeight: '600',
                                                backgroundColor: '#f59e0b20',
                                                color: '#fbbf24',
                                                border: '1px solid #f59e0b40',
                                            }}>⚠ Use Caution</span>
                                        )}
                                        <span style={{
                                            padding: '4px 10px',
                                            borderRadius: '12px',
                                            fontSize: '11px',
                                            fontWeight: '600',
                                            backgroundColor: `${getConfColor(herb.confidence)}15`,
                                            color: getConfColor(herb.confidence),
                                            border: `1px solid ${getConfColor(herb.confidence)}40`,
                                        }}>
                                            {(herb.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                </div>

                                {/* Herbicide Details */}
                                <div style={{ padding: '16px' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                                        <div>
                                            <p style={{ margin: 0, fontSize: '11px', color: '#8baa96', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Active Ingredient</p>
                                            <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#e2e8f0' }}>{herb.activeIngredient}</p>
                                        </div>
                                        <div>
                                            <p style={{ margin: 0, fontSize: '11px', color: '#8baa96', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Application Rate</p>
                                            <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#e2e8f0' }}>{herb.applicationRate}</p>
                                        </div>
                                        <div style={{ gridColumn: '1 / -1' }}>
                                            <p style={{ margin: 0, fontSize: '11px', color: '#8baa96', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Mode of Action</p>
                                            <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#e2e8f0' }}>{herb.modeOfAction}</p>
                                        </div>
                                    </div>

                                    {/* Target Weeds */}
                                    {herb.targetWeeds && herb.targetWeeds.length > 0 && (
                                        <div style={{ marginBottom: '12px' }}>
                                            <p style={{ margin: '0 0 6px', fontSize: '11px', color: '#8baa96', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Target Weeds</p>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                                {herb.targetWeeds.map((w, i) => (
                                                    <span key={i} style={{
                                                        padding: '3px 10px',
                                                        borderRadius: '12px',
                                                        fontSize: '11px',
                                                        backgroundColor: '#ef444415',
                                                        color: '#fca5a5',
                                                        border: '1px solid #ef444430',
                                                    }}>🌿 {w}</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Reasoning */}
                                    <button
                                        onClick={() => toggleReason(`herb-${idx}`)}
                                        style={{
                                            background: 'none',
                                            border: '1px solid #0f5240',
                                            borderRadius: '8px',
                                            padding: '6px 12px',
                                            color: '#94a3b8',
                                            cursor: 'pointer',
                                            fontSize: '12px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '6px',
                                        }}
                                    >
                                        🔍 {showReasons[`herb-${idx}`] ? 'Hide' : 'Why this herbicide?'}
                                    </button>
                                    {showReasons[`herb-${idx}`] && (
                                        <div style={{
                                            marginTop: '10px',
                                            padding: '12px',
                                            backgroundColor: '#0f5240',
                                            borderRadius: '8px',
                                            borderLeft: '3px solid #a8cc3a',
                                        }}>
                                            <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.6', color: '#c0d4c8' }}>
                                                {herb.reasoning}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </SectionCard>
            )}

            {/* Weed Species Detected */}
            {features.weedSpecies.length > 0 && (
                <div style={{
                    marginTop: '16px',
                    padding: '16px',
                    backgroundColor: '#0f5240',
                    borderRadius: '12px',
                    border: '1px solid #0f5240',
                }}>
                    <h4 style={{ margin: '0 0 12px', fontSize: '14px', fontWeight: '600', color: '#f8fafc' }}>
                        🌿 Detected Weed Species
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {features.weedSpecies.map((sp, idx) => (
                            <div key={idx} style={{
                                padding: '8px 14px',
                                borderRadius: '8px',
                                backgroundColor: '#083328',
                                border: '1px solid #0f5240',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                            }}>
                                <span style={{ fontSize: '13px', fontWeight: '500', color: '#e2e8f0' }}>
                                    {sp.name}
                                </span>
                                <span style={{
                                    padding: '2px 8px',
                                    borderRadius: '10px',
                                    fontSize: '11px',
                                    backgroundColor: '#d4f04d20',
                                    color: '#d4f04d',
                                }}>
                                    ×{sp.count}
                                </span>
                                <span style={{ fontSize: '11px', color: '#8baa96' }}>
                                    {(sp.avgConfidence * 100).toFixed(0)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};


// ============================================================
// SUB-COMPONENTS
// ============================================================

const SectionCard: React.FC<{
    title: string;
    subtitle: string;
    isOpen: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}> = ({ title, subtitle, isOpen, onToggle, children }) => (
    <div style={{
        marginTop: '16px',
        border: '1px solid #0f5240',
        borderRadius: '16px',
        overflow: 'hidden',
        backgroundColor: '#083328',
    }}>
        <div
            onClick={onToggle}
            style={{
                padding: '16px 20px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: isOpen ? '#0f5240' : 'transparent',
                transition: 'background-color 0.2s',
            }}
        >
            <div>
                <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '600', color: '#e8f0ec' }}>{title}</h4>
                <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#8baa96' }}>{subtitle}</p>
            </div>
            <span style={{
                fontSize: '18px',
                transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.3s ease',
                color: '#8baa96',
            }}>▼</span>
        </div>
        {isOpen && (
            <div style={{ padding: '20px', borderTop: '1px solid #0f5240' }}>
                {children}
            </div>
        )}
    </div>
);


const InfoChip: React.FC<{ label: string; value: string; color: string }> = ({ label, value, color }) => (
    <div style={{
        padding: '10px 14px',
        borderRadius: '10px',
        backgroundColor: `${color}10`,
        border: `1px solid ${color}30`,
    }}>
        <p style={{ margin: 0, fontSize: '10px', color: '#8baa96', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</p>
        <p style={{ margin: '2px 0 0', fontSize: '14px', fontWeight: '700', color }}>{value}</p>
    </div>
);


const WeatherFactorCard: React.FC<{
    icon: string;
    label: string;
    value: string;
    suitable: boolean;
    reason: string;
}> = ({ icon, label, value, suitable, reason }) => {
    const [showDetail, setShowDetail] = useState(false);

    return (
        <div
            onClick={() => setShowDetail(!showDetail)}
            style={{
                padding: '14px',
                borderRadius: '10px',
                backgroundColor: suitable ? '#22c55e08' : '#ef444408',
                border: `1px solid ${suitable ? '#22c55e25' : '#ef444425'}`,
                cursor: 'pointer',
                transition: 'all 0.2s',
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>{icon}</span>
                    <div>
                        <p style={{ margin: 0, fontSize: '11px', color: '#8baa96' }}>{label}</p>
                        <p style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: '#e2e8f0' }}>{value}</p>
                    </div>
                </div>
                <span style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '14px',
                    backgroundColor: suitable ? '#22c55e20' : '#ef444420',
                }}>
                    {suitable ? '✓' : '✗'}
                </span>
            </div>
            {showDetail && (
                <p style={{
                    margin: '10px 0 0',
                    fontSize: '12px',
                    color: '#94a3b8',
                    lineHeight: '1.5',
                    paddingTop: '8px',
                    borderTop: '1px solid #0f5240',
                }}>
                    {reason}
                </p>
            )}
        </div>
    );
};


const SprayAngleDiagram: React.FC<{ angle: number; pattern: string }> = ({ angle, pattern }) => {
    const size = 160;
    const center = size / 2;
    const radius = 60;

    // Convert angle to radians for SVG (0° = right, going clockwise)
    const angleRad = (angle - 90) * (Math.PI / 180);

    const getSprayPath = () => {
        if (pattern === 'broadcast') {
            // Full circle
            return `M ${center} ${center - radius} A ${radius} ${radius} 0 1 1 ${center - 0.01} ${center - radius}`;
        }
        if (pattern === 'spot') {
            return ''; // Just a dot
        }
        // Directional / inter-row: arc ±30° from angle
        const halfArc = 30 * (Math.PI / 180);
        const startAngle = angleRad - halfArc;
        const endAngle = angleRad + halfArc;
        const sx = center + radius * Math.cos(startAngle);
        const sy = center + radius * Math.sin(startAngle);
        const ex = center + radius * Math.cos(endAngle);
        const ey = center + radius * Math.sin(endAngle);
        return `M ${center} ${center} L ${sx} ${sy} A ${radius} ${radius} 0 0 1 ${ex} ${ey} Z`;
    };

    const arrowX = center + (radius - 10) * Math.cos(angleRad);
    const arrowY = center + (radius - 10) * Math.sin(angleRad);

    return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: 'block' }}>
            {/* Background circle */}
            <circle cx={center} cy={center} r={radius + 5} fill="none" stroke="#0f5240" strokeWidth="2" />
            <circle cx={center} cy={center} r={radius} fill="none" stroke="#0f5240" strokeWidth="1" strokeDasharray="4 4" />

            {/* Spray pattern */}
            {pattern === 'broadcast' ? (
                <circle cx={center} cy={center} r={radius} fill="#d4f04d15" stroke="#d4f04d" strokeWidth="2" />
            ) : pattern === 'spot' ? (
                <circle cx={center} cy={center} r={10} fill="#d4f04d40" stroke="#d4f04d" strokeWidth="2" />
            ) : (
                <path d={getSprayPath()} fill="#d4f04d20" stroke="#d4f04d" strokeWidth="2" />
            )}

            {/* Center point (sprayer position) */}
            <circle cx={center} cy={center} r={5} fill="#a8cc3a" stroke="#d4f04d" strokeWidth="2" />

            {/* Direction arrow (for non-broadcast) */}
            {pattern !== 'broadcast' && pattern !== 'spot' && (
                <line
                    x1={center}
                    y1={center}
                    x2={arrowX}
                    y2={arrowY}
                    stroke="#d4f04d"
                    strokeWidth="2"
                    markerEnd="url(#arrowhead)"
                />
            )}

            {/* Arrowhead marker */}
            <defs>
                <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#d4f04d" />
                </marker>
            </defs>

            {/* Angle label */}
            <text
                x={center}
                y={size - 8}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="12"
                fontWeight="600"
            >
                {pattern === 'broadcast' ? '360°' : `${angle}°`}
            </text>

            {/* N/S/E/W labels */}
            <text x={center} y={12} textAnchor="middle" fill="#475569" fontSize="10">N</text>
            <text x={size - 8} y={center + 4} textAnchor="middle" fill="#475569" fontSize="10">E</text>
            <text x={center} y={size - 2} textAnchor="middle" fill="#475569" fontSize="10">S</text>
            <text x={8} y={center + 4} textAnchor="middle" fill="#475569" fontSize="10">W</text>
        </svg>
    );
};


// Color palette for feature importance bars
const getBarColor = (index: number): string => {
    const colors = [
        '#d4f04d, #a8cc3a',   // indigo → violet
        '#0ea5e9, #38bdf8',   // sky
        '#22c55e, #4ade80',   // green
        '#f59e0b, #fbbf24',   // amber
        '#ef4444, #f87171',   // red
        '#ec4899, #f472b6',   // pink
    ];
    return colors[index % colors.length];
};


export default ExplainableAIPanel;
