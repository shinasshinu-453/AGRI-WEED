import React from 'react';
import { Upload, Layers, Video, LogOut, Menu, X, BarChart2, Sprout } from 'lucide-react';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Button } from './ui/button';
import { WeatherWidget } from './WeatherWidget';

interface SidebarProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
    user: { name: string; email: string } | null;
    onLogout: () => void;
    isCollapsed?: boolean;
    onToggleCollapse?: () => void;
    currentLocation?: {
        latitude: number;
        longitude: number;
        locationName?: string;
    } | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
    activeTab,
    onTabChange,
    user,
    onLogout,
    isCollapsed = false,
    onToggleCollapse,
    currentLocation,
}) => {
    const navItems = [
        { id: 'realtime', icon: Video, label: 'Real-Time', description: 'Live detection' },
        { id: 'upload', icon: Upload, label: 'Upload', description: 'Single image' },
        { id: 'batch', icon: Layers, label: 'Batch Process', description: 'Multiple images' },
        { id: 'model-dashboard', icon: BarChart2, label: 'Model Dashboard', description: 'YOLOv11 vs Roboflow' },

    ];

    if (isCollapsed) {
        return (
            <div className="w-20 flex flex-col items-center py-5 space-y-3" style={{ background: '#0a3d2e' }}>
                {onToggleCollapse && (
                    <button
                        onClick={onToggleCollapse}
                        className="p-2.5 hover:bg-white/10 rounded-xl transition-colors text-white/70"
                    >
                        <Menu size={22} />
                    </button>
                )}
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onTabChange(item.id)}
                        className={`p-3 rounded-xl transition-all duration-200 ${activeTab === item.id
                            ? 'text-[#0a3d2e]'
                            : 'hover:bg-white/10 text-white/60 hover:text-white'
                            }`}
                        style={activeTab === item.id ? { background: '#d4f04d' } : {}}
                        title={item.label}
                    >
                        <item.icon size={22} />
                    </button>
                ))}
                <div className="flex-1" />
                <button
                    onClick={onLogout}
                    className="p-3 hover:bg-red-500/20 text-white/60 hover:text-red-300 rounded-xl transition-colors"
                    title="Logout"
                >
                    <LogOut size={22} />
                </button>
            </div>
        );
    }

    return (
        <div className="w-72 flex flex-col" style={{ background: '#0a3d2e' }}>
            {/* Header */}
            <div className="p-5 border-b border-white/10">
                <div className="flex items-center justify-between mb-5">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl" style={{ background: '#d4f04d' }}>
                            <Sprout size={22} style={{ color: '#0a3d2e' }} />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-white">
                                Agri<span className="serif-accent" style={{ color: '#d4f04d' }}>Vision</span>
                            </h2>
                        </div>
                    </div>
                    {onToggleCollapse && (
                        <button
                            onClick={onToggleCollapse}
                            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-white/60 lg:hidden"
                        >
                            <X size={20} />
                        </button>
                    )}
                </div>

                {user && (
                    <div className="flex items-center gap-3 p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.06)' }}>
                        <Avatar className="border-2" style={{ borderColor: '#d4f04d' }}>
                            <AvatarFallback className="text-sm font-bold" style={{ background: '#d4f04d', color: '#0a3d2e' }}>
                                {user.name?.charAt(0).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">{user.name}</p>
                            <p className="text-xs truncate" style={{ color: 'rgba(255,255,255,0.5)' }}>{user.email}</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onTabChange(item.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 ${activeTab === item.id
                            ? 'shadow-lg font-semibold'
                            : 'hover:bg-white/8 text-white/70 hover:text-white'
                            }`}
                        style={activeTab === item.id ? { background: '#d4f04d', color: '#0a3d2e' } : {}}
                    >
                        <item.icon size={20} />
                        <div className="flex-1 text-left">
                            <p className="font-medium text-sm">{item.label}</p>
                            <p className={`text-xs ${activeTab === item.id ? 'opacity-70' : 'opacity-50'}`}>
                                {item.description}
                            </p>
                        </div>
                    </button>
                ))}
            </nav>

            {/* Footer */}
            <div className="p-4 space-y-4 border-t border-white/10">
                <WeatherWidget
                    compact
                    latitude={currentLocation?.latitude}
                    longitude={currentLocation?.longitude}
                    locationName={currentLocation?.locationName}
                    userId={user?.email}
                />
                <Button
                    onClick={onLogout}
                    variant="outline"
                    className="w-full gap-2 rounded-xl border-white/15 text-white/70 hover:text-white hover:bg-white/10 hover:border-white/25"
                    size="sm"
                >
                    <LogOut size={16} />
                    Logout
                </Button>
            </div>
        </div>
    );
};
