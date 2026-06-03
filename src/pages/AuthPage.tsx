import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore, UserRole } from '../store/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Sprout, Shield, User, Mail, Lock, AlertCircle, Loader2, ArrowRight, Leaf } from 'lucide-react';

export const AuthPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, signup } = useAuthStore();
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginRole, setLoginRole] = useState<UserRole>('user');
  
  // Signup form state
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupRole, setSignupRole] = useState<UserRole>('user');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    
    try {
      await login(loginEmail, loginPassword, loginRole);
      navigate(loginRole === 'admin' ? '/admin' : '/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    
    try {
      await signup(signupEmail, signupPassword, signupName, signupRole);
      navigate(signupRole === 'admin' ? '/admin' : '/dashboard');
    } catch (err: any) {
      setError(err.message || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 md:p-8 relative overflow-hidden" style={{ background: '#0a3d2e' }}>
      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Organic blobs */}
        <div className="absolute top-[-15%] right-[-10%] w-[55%] h-[55%] rounded-full blur-[100px] opacity-30" style={{ background: '#1a7a5a' }} />
        <div className="absolute bottom-[-15%] left-[-10%] w-[50%] h-[50%] rounded-full blur-[100px] opacity-20" style={{ background: '#d4f04d' }} />
        <div className="absolute top-[40%] left-[30%] w-[25%] h-[25%] rounded-full blur-[80px] opacity-10" style={{ background: '#5a9e6f' }} />

        {/* Subtle dot pattern */}
        <div className="absolute inset-0" style={{ 
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.04) 1px, transparent 0)',
          backgroundSize: '32px 32px'
        }} />
      </div>

      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-12 lg:gap-20 items-center relative z-10">
        {/* Hero Section */}
        <div className="text-center lg:text-left space-y-8 px-4 lg:px-0">
          {/* Badge */}
          <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full border border-white/15 backdrop-blur-sm" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <span className="flex h-2 w-2 rounded-full bg-[#d4f04d] animate-pulse" />
            <span className="text-xs font-semibold text-white/70 uppercase tracking-widest">Powered by YOLOv11</span>
          </div>
          
          <div className="space-y-5">
            <div className="flex items-center justify-center lg:justify-start gap-4 mb-3">
              <div className="p-4 rounded-2xl" style={{ background: '#d4f04d' }}>
                <Sprout size={44} style={{ color: '#0a3d2e' }} />
              </div>
              <h1 className="text-6xl md:text-7xl font-black tracking-tight text-white">
                Agri<span className="serif-accent" style={{ color: '#d4f04d' }}>Vision</span>
              </h1>
            </div>
            
            <p className="text-xl md:text-2xl font-light leading-relaxed max-w-xl mx-auto lg:mx-0" style={{ color: 'rgba(232, 240, 236, 0.8)' }}>
              Empowering farmers with <span className="serif-accent" style={{ color: '#d4f04d' }}>AI-Powered</span> crop protection & weed identification.
            </p>
          </div>
          
          {/* Project Description */}
          <div className="pt-6 space-y-5">
            <div className="p-6 rounded-2xl" style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Leaf size={18} style={{ color: '#d4f04d' }} />
                <span className="text-sm font-semibold uppercase tracking-wider" style={{ color: '#d4f04d' }}>About the Project</span>
              </div>
              <p className="text-sm leading-relaxed" style={{ color: 'rgba(232, 240, 236, 0.75)' }}>
                <span className="font-semibold text-white">AgriVision</span> is an intelligent weed detection platform built for precision agriculture. 
                It leverages a fine-tuned <span style={{ color: '#d4f04d' }}>YOLOv11n</span> deep learning model to identify and classify 
                <span className="font-semibold text-white"> 12 weed species</span> in cotton crops through real-time image analysis. 
                Upload field images or use your camera for instant detection, and monitor weed density across your farm — all from a single dashboard.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl text-center" style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div className="text-2xl font-black text-white">12</div>
                <div className="text-[10px] mt-0.5 font-medium uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.5)' }}>Weed Species</div>
              </div>
              <div className="p-3 rounded-xl text-center" style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div className="text-2xl font-black" style={{ color: '#d4f04d' }}>YOLOv11</div>
                <div className="text-[10px] mt-0.5 font-medium uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.5)' }}>Detection Model</div>
              </div>
            </div>
          </div>
        </div>

        {/* Auth Card — Verdantix clean white style */}
        <div className="relative">
          <div className="absolute -inset-1 rounded-3xl blur opacity-30" style={{ background: 'linear-gradient(135deg, #d4f04d, #5a9e6f)' }} />
          <Card className="relative bg-white shadow-2xl border-0 rounded-3xl overflow-hidden">
            <CardHeader className="space-y-3 pb-6 pt-8 px-8">
              <CardTitle className="text-3xl font-bold text-center" style={{ color: '#0a3d2e' }}>
                Welcome to the <span className="serif-accent">Field</span>
              </CardTitle>
              <CardDescription className="text-center text-base" style={{ color: '#5a7265' }}>
                Sign in to protect your crops with AI
              </CardDescription>
            </CardHeader>
            
            <CardContent className="px-8 pb-8">
              <Tabs defaultValue="login" className="w-full">
                <TabsList className="grid w-full grid-cols-2 p-1.5 rounded-full mb-8" style={{ background: '#eef0ea' }}>
                  <TabsTrigger 
                    value="login" 
                    className="rounded-full py-2.5 text-sm font-semibold transition-all data-[state=active]:bg-[#0a3d2e] data-[state=active]:text-white data-[state=active]:shadow-md"
                  >
                    Log In
                  </TabsTrigger>
                  <TabsTrigger 
                    value="signup" 
                    className="rounded-full py-2.5 text-sm font-semibold transition-all data-[state=active]:bg-[#0a3d2e] data-[state=active]:text-white data-[state=active]:shadow-md"
                  >
                    Join Now
                  </TabsTrigger>
                </TabsList>

                {error && (
                  <div className="mb-6 p-4 rounded-2xl flex items-start gap-3 animate-in fade-in slide-in-from-top-2" style={{ background: '#fef2f2', border: '1px solid #fecaca' }}>
                    <AlertCircle size={20} className="text-red-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm font-medium text-red-600 leading-tight">{error}</span>
                  </div>
                )}

                {/* Login Tab */}
                <TabsContent value="login" className="space-y-5">
                  <form onSubmit={handleLogin} className="space-y-5">
                    <div className="space-y-2">
                      <Label htmlFor="login-email" className="text-sm font-semibold ml-1" style={{ color: '#0a3d2e' }}>Email Address</Label>
                      <div className="relative group">
                        <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 transition-colors" style={{ color: '#8baa96' }} />
                        <Input
                          id="login-email"
                          type="email"
                          placeholder="farmer@agrivision.com"
                          value={loginEmail}
                          onChange={(e) => setLoginEmail(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-13 text-base rounded-xl transition-all focus:ring-2 focus:ring-[#0a3d2e]/20"
                          style={{ background: '#f3f4f1', border: '1.5px solid #d8ddd3', color: '#0a3d2e' }}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between items-center ml-1">
                        <Label htmlFor="login-password" className="text-sm font-semibold" style={{ color: '#0a3d2e' }}>Password</Label>
                        <button type="button" className="text-xs font-bold hover:underline transition-all" style={{ color: '#5a9e6f' }}>Forgot password?</button>
                      </div>
                      <div className="relative group">
                        <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 transition-colors" style={{ color: '#8baa96' }} />
                        <Input
                          id="login-password"
                          type="password"
                          placeholder="••••••••"
                          value={loginPassword}
                          onChange={(e) => setLoginPassword(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-13 text-base rounded-xl transition-all focus:ring-2 focus:ring-[#0a3d2e]/20"
                          style={{ background: '#f3f4f1', border: '1.5px solid #d8ddd3', color: '#0a3d2e' }}
                        />
                      </div>
                    </div>

                    <div className="space-y-3">
                      <Label className="text-sm font-semibold ml-1" style={{ color: '#0a3d2e' }}>Select Access Role</Label>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          type="button"
                          onClick={() => setLoginRole('user')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            loginRole === 'user'
                              ? 'border-[#0a3d2e] shadow-lg'
                              : 'border-[#d8ddd3] hover:border-[#8baa96]'
                          }`}
                          style={{ background: loginRole === 'user' ? '#eef0ea' : '#ffffff' }}
                        >
                          <Sprout size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${loginRole === 'user' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${loginRole === 'user' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`}>Farmer</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => setLoginRole('admin')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            loginRole === 'admin'
                              ? 'border-[#0a3d2e] shadow-lg'
                              : 'border-[#d8ddd3] hover:border-[#8baa96]'
                          }`}
                          style={{ background: loginRole === 'admin' ? '#eef0ea' : '#ffffff' }}
                        >
                          <Shield size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${loginRole === 'admin' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${loginRole === 'admin' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`}>Admin</div>
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="verdantix-btn w-full h-14 text-base group"
                    >
                      {isLoading ? (
                        <Loader2 size={22} className="animate-spin" />
                      ) : (
                        <span className="flex items-center gap-2">
                          Access Dashboard <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                        </span>
                      )}
                    </button>
                  </form>
                </TabsContent>

                {/* Signup Tab */}
                <TabsContent value="signup" className="space-y-5">
                  <form onSubmit={handleSignup} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="signup-name" className="text-sm font-semibold ml-1" style={{ color: '#0a3d2e' }}>Full Name</Label>
                      <div className="relative group">
                        <User size={18} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: '#8baa96' }} />
                        <Input
                          id="signup-name"
                          type="text"
                          placeholder="John Doe"
                          value={signupName}
                          onChange={(e) => setSignupName(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-13 text-base rounded-xl focus:ring-2 focus:ring-[#0a3d2e]/20"
                          style={{ background: '#f3f4f1', border: '1.5px solid #d8ddd3', color: '#0a3d2e' }}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="signup-email" className="text-sm font-semibold ml-1" style={{ color: '#0a3d2e' }}>Email Address</Label>
                      <div className="relative group">
                        <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: '#8baa96' }} />
                        <Input
                          id="signup-email"
                          type="email"
                          placeholder="your.email@example.com"
                          value={signupEmail}
                          onChange={(e) => setSignupEmail(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-13 text-base rounded-xl focus:ring-2 focus:ring-[#0a3d2e]/20"
                          style={{ background: '#f3f4f1', border: '1.5px solid #d8ddd3', color: '#0a3d2e' }}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="signup-password" className="text-sm font-semibold ml-1" style={{ color: '#0a3d2e' }}>Password</Label>
                      <div className="relative group">
                        <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: '#8baa96' }} />
                        <Input
                          id="signup-password"
                          type="password"
                          placeholder="••••••••"
                          value={signupPassword}
                          onChange={(e) => setSignupPassword(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-13 text-base rounded-xl focus:ring-2 focus:ring-[#0a3d2e]/20"
                          style={{ background: '#f3f4f1', border: '1.5px solid #d8ddd3', color: '#0a3d2e' }}
                        />
                      </div>
                      <p className="text-xs ml-1" style={{ color: '#8baa96' }}>At least 6 characters with mixed case recommended</p>
                    </div>

                    <div className="space-y-3">
                      <Label className="text-sm font-semibold ml-1" style={{ color: '#0a3d2e' }}>I want to join as</Label>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          type="button"
                          onClick={() => setSignupRole('user')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            signupRole === 'user'
                              ? 'border-[#0a3d2e] shadow-lg'
                              : 'border-[#d8ddd3] hover:border-[#8baa96]'
                          }`}
                          style={{ background: signupRole === 'user' ? '#eef0ea' : '#ffffff' }}
                        >
                          <Sprout size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${signupRole === 'user' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${signupRole === 'user' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`}>Farmer</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => setSignupRole('admin')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            signupRole === 'admin'
                              ? 'border-[#0a3d2e] shadow-lg'
                              : 'border-[#d8ddd3] hover:border-[#8baa96]'
                          }`}
                          style={{ background: signupRole === 'admin' ? '#eef0ea' : '#ffffff' }}
                        >
                          <Shield size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${signupRole === 'admin' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${signupRole === 'admin' ? 'text-[#0a3d2e]' : 'text-[#8baa96]'}`}>Admin</div>
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="verdantix-btn w-full h-14 text-base group"
                    >
                      {isLoading ? (
                        <Loader2 size={22} className="animate-spin" />
                      ) : (
                        <span className="flex items-center gap-2">
                          Create Account <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                        </span>
                      )}
                    </button>
                  </form>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
