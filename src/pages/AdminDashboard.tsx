import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import {
  Sprout, Shield, LogOut, BarChart3, Image as ImageIcon,
  CheckCircle2, Circle, Trash2, Plus, TrendingUp, Users, Camera,
  Download, Search, Filter, RefreshCw, Activity, Clock, AlertCircle
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format, subDays, startOfDay } from 'date-fns';
import toast, { Toaster } from 'react-hot-toast';
import { WeatherWidget } from '../components/WeatherWidget';
import {
  subscribeToStatistics,
  subscribeToDetections,
  subscribeToActivities,
  exportDetectionsToCSV,
  searchDetections,
  deleteDetection,
  Detection,
  Activity as ActivityType,
  Statistics,
} from '../services/firebaseService';

interface TodoItem {
  id: string;
  text: string;
  completed: boolean;
}

export const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  // State
  const [stats, setStats] = useState<Statistics>({
    totalDetections: 0,
    weedsDetected: 0,
    photosUploaded: 0,
    activeUsers: 0,
    cropsDetected: 0,
  });
  const [detections, setDetections] = useState<Detection[]>([]);
  const [activities, setActivities] = useState<ActivityType[]>([]);
  const [filteredDetections, setFilteredDetections] = useState<Detection[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedCard, setSelectedCard] = useState<string | null>(null);

  const [todos, setTodos] = useState<TodoItem[]>([
    { id: '1', text: 'Review pending weed detections', completed: false },
    { id: '2', text: 'Update YOLO model weights', completed: false },
    { id: '3', text: 'Generate monthly detection report', completed: true },
    { id: '4', text: 'Check camera calibration settings', completed: false },
  ]);
  const [newTodo, setNewTodo] = useState('');

  // Chart data
  const [chartData, setChartData] = useState<any[]>([]);
  const [pieData, setPieData] = useState<any[]>([]);

  // Real-time subscriptions
  useEffect(() => {
    // Subscribe to statistics
    const unsubStats = subscribeToStatistics((newStats) => {
      setStats(newStats);
    });

    // Subscribe to detections
    const unsubDetections = subscribeToDetections((newDetections) => {
      setDetections(newDetections);
      setFilteredDetections(newDetections);

      // Generate chart data
      generateChartData(newDetections);
    }, { limit: 50 });

    // Subscribe to activities
    const unsubActivities = subscribeToActivities((newActivities) => {
      setActivities(newActivities);
    }, 10);

    return () => {
      unsubStats();
      unsubDetections();
      unsubActivities();
    };
  }, []);

  // Generate chart data from detections
  const generateChartData = (detectionsList: Detection[]) => {
    // Last 7 days data
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = startOfDay(subDays(new Date(), 6 - i));
      return {
        date: format(date, 'MMM dd'),
        weeds: 0,
        crops: 0,
        total: 0,
      };
    });

    detectionsList.forEach(detection => {
      const detectionDate = detection.timestamp.toDate();
      const dayIndex = last7Days.findIndex(day => {
        const dayDate = new Date(day.date + ', ' + new Date().getFullYear());
        return format(startOfDay(detectionDate), 'MMM dd') === day.date;
      });

      if (dayIndex !== -1) {
        last7Days[dayIndex].weeds += detection.weedsDetected;
        last7Days[dayIndex].crops += detection.cropsDetected;
        last7Days[dayIndex].total += 1;
      }
    });

    setChartData(last7Days);

    // Pie chart data
    const totalWeeds = detectionsList.reduce((sum, d) => sum + d.weedsDetected, 0);
    const totalCrops = detectionsList.reduce((sum, d) => sum + d.cropsDetected, 0);

    setPieData([
      { name: 'Weeds', value: totalWeeds, color: '#ef4444' },
      { name: 'Crops', value: totalCrops, color: '#10b981' },
    ]);
  };

  // Filter detections
  useEffect(() => {
    let filtered = detections;

    if (statusFilter !== 'all') {
      filtered = filtered.filter(d => d.status === statusFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(d =>
        d.filename.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredDetections(filtered);
  }, [searchTerm, statusFilter, detections]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    toast.success('Data refreshed!');
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const handleExport = () => {
    exportDetectionsToCSV(filteredDetections);
    toast.success('Exported to CSV!');
  };

  const handleDeleteDetection = async (id: string) => {
    try {
      await deleteDetection(id);
      toast.success('Detection deleted!');
    } catch (error) {
      toast.error('Failed to delete detection');
    }
  };

  const toggleTodo = (id: string) => {
    setTodos(todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
    toast.success('Task updated!');
  };

  const addTodo = () => {
    if (newTodo.trim()) {
      setTodos([...todos, {
        id: Date.now().toString(),
        text: newTodo,
        completed: false,
      }]);
      setNewTodo('');
      toast.success('Task added!');
    }
  };

  const deleteTodo = (id: string) => {
    setTodos(todos.filter(todo => todo.id !== id));
    toast.success('Task deleted!');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processed':
        return 'bg-primary/20 text-primary border-primary/30';
      case 'pending':
        return 'bg-secondary/20 text-secondary border-secondary/30';
      case 'failed':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const StatCard = ({
    title,
    value,
    icon: Icon,
    trend,
    color,
    onClick
  }: {
    title: string;
    value: number;
    icon: any;
    trend: string;
    color: string;
    onClick: () => void;
  }) => (
    <Card
      className="glass-effect border-white/20 hover:border-primary/30 transition-all cursor-pointer hover:scale-105"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Icon size={16} />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold ${color}`}>{value}</div>
        <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
          <TrendingUp size={12} className={color} />
          {trend}
        </p>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-background cyber-grid">
      <Toaster position="top-right" />

      {/* Header */}
      <header className="glass-effect border-b border-white/10 sticky top-0 z-50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-accent/20 border border-accent/30">
              <Shield size={24} className="text-accent" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">AgriVision Admin</h1>
              <p className="text-xs text-muted-foreground">Real-time Dashboard</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              className="gap-2"
              disabled={isRefreshing}
            >
              <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>

            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Avatar className="border-2 border-accent/30">
                <AvatarFallback className="bg-accent/20 text-accent font-semibold">
                  {user?.name?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">
            Welcome back, <span className="gradient-text">{user?.name}</span>!
          </h2>
          <p className="text-muted-foreground">
            Monitor system performance, manage detections, and track analytics in real-time
          </p>
        </div>

        {/* Weather Widget */}
        <div className="mb-8">
          <WeatherWidget />
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Detections"
            value={stats.totalDetections}
            icon={BarChart3}
            trend="+12% from last month"
            color="text-primary"
            onClick={() => {
              setSelectedCard('detections');
              toast('Showing detection details', { icon: '📊' });
            }}
          />
          <StatCard
            title="Weeds Detected"
            value={stats.weedsDetected}
            icon={Sprout}
            trend="+8% from last month"
            color="text-destructive"
            onClick={() => {
              setStatusFilter('processed');
              toast('Filtered by processed detections', { icon: '🌿' });
            }}
          />
          <StatCard
            title="Photos Uploaded"
            value={stats.photosUploaded}
            icon={Camera}
            trend="+15% from last month"
            color="text-accent"
            onClick={() => {
              toast('Showing all photos', { icon: '📸' });
            }}
          />
          <StatCard
            title="Active Users"
            value={stats.activeUsers}
            icon={Users}
            trend="+3 new this week"
            color="text-secondary"
            onClick={() => {
              toast('User management coming soon', { icon: '👥' });
            }}
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Line Chart */}
          <Card className="glass-effect border-white/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp size={20} />
                Detection Trends (Last 7 Days)
              </CardTitle>
              <CardDescription>Daily weed and crop detection statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="date" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #333',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="weeds" stroke="#ef4444" strokeWidth={2} />
                  <Line type="monotone" dataKey="crops" stroke="#10b981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Pie Chart */}
          <Card className="glass-effect border-white/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 size={20} />
                Weed vs Crop Distribution
              </CardTitle>
              <CardDescription>Overall detection breakdown</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #333',
                      borderRadius: '8px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Detection History Table */}
          <div className="lg:col-span-2">
            <Card className="glass-effect border-white/20">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <ImageIcon size={20} />
                      Detection History
                    </CardTitle>
                    <CardDescription>Recent weed detection submissions</CardDescription>
                  </div>
                  <Button onClick={handleExport} variant="outline" size="sm" className="gap-2">
                    <Download size={16} />
                    Export CSV
                  </Button>
                </div>

                {/* Search and Filter */}
                <div className="flex gap-2 mt-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={16} />
                    <Input
                      placeholder="Search by filename..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 bg-input border-white/10"
                    />
                  </div>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-4 py-2 rounded-lg bg-input border border-white/10 text-sm"
                  >
                    <option value="all">All Status</option>
                    <option value="processed">Processed</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border border-white/10 overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-white/10 hover:bg-muted/50">
                        <TableHead>Filename</TableHead>
                        <TableHead>Timestamp</TableHead>
                        <TableHead className="text-center">Weeds</TableHead>
                        <TableHead className="text-center">Crops</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredDetections.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                            <AlertCircle className="mx-auto mb-2" size={24} />
                            No detections found. Upload images to see data here.
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredDetections.slice(0, 10).map((detection) => (
                          <TableRow key={detection.id} className="border-white/10 hover:bg-muted/30">
                            <TableCell className="font-medium">{detection.filename}</TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {format(detection.timestamp.toDate(), 'MMM dd, yyyy HH:mm')}
                            </TableCell>
                            <TableCell className="text-center">
                              <span className="font-semibold text-destructive">{detection.weedsDetected}</span>
                            </TableCell>
                            <TableCell className="text-center">
                              <span className="font-semibold text-primary">{detection.cropsDetected}</span>
                            </TableCell>
                            <TableCell>
                              <Badge className={getStatusColor(detection.status)}>
                                {detection.status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => detection.id && handleDeleteDetection(detection.id)}
                              >
                                <Trash2 size={16} className="text-destructive" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
                {filteredDetections.length > 10 && (
                  <p className="text-sm text-muted-foreground mt-4 text-center">
                    Showing 10 of {filteredDetections.length} detections
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Todo List */}
            <Card className="glass-effect border-white/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 size={20} />
                  To-Do List
                </CardTitle>
                <CardDescription>Track administrative tasks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Add new task..."
                    value={newTodo}
                    onChange={(e) => setNewTodo(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addTodo()}
                    className="flex-1 bg-input border-white/10"
                  />
                  <Button
                    size="icon"
                    onClick={addTodo}
                    className="bg-primary hover:bg-primary/80"
                  >
                    <Plus size={18} />
                  </Button>
                </div>

                <div className="space-y-2">
                  {todos.map((todo) => (
                    <div
                      key={todo.id}
                      className="flex items-center gap-3 p-3 rounded-lg glass-effect border border-white/10 hover:border-primary/20 transition-all group"
                    >
                      <button
                        onClick={() => toggleTodo(todo.id)}
                        className="flex-shrink-0"
                      >
                        {todo.completed ? (
                          <CheckCircle2 size={20} className="text-primary" />
                        ) : (
                          <Circle size={20} className="text-muted-foreground" />
                        )}
                      </button>
                      <span
                        className={`flex-1 text-sm ${todo.completed
                          ? 'line-through text-muted-foreground'
                          : 'text-foreground'
                          }`}
                      >
                        {todo.text}
                      </span>
                      <button
                        onClick={() => deleteTodo(todo.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 size={16} className="text-destructive" />
                      </button>
                    </div>
                  ))}
                </div>

                <div className="pt-4 border-t border-white/10">
                  <p className="text-sm text-muted-foreground">
                    {todos.filter(t => t.completed).length} of {todos.length} tasks completed
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Activity Feed */}
            <Card className="glass-effect border-white/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity size={20} />
                  Recent Activity
                </CardTitle>
                <CardDescription>Live system events</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {activities.length === 0 ? (
                    <div className="text-center text-muted-foreground py-4">
                      <Clock className="mx-auto mb-2" size={24} />
                      <p className="text-sm">No recent activity</p>
                    </div>
                  ) : (
                    activities.slice(0, 5).map((activity) => (
                      <div key={activity.id} className="flex gap-3 p-3 rounded-lg glass-effect border border-white/10">
                        <div className="flex-shrink-0 mt-1">
                          <div className="w-2 h-2 rounded-full bg-primary"></div>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm">{activity.description}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {format(activity.timestamp.toDate(), 'MMM dd, HH:mm')}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};