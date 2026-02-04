import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore, UserRole } from '../store/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Sprout, Shield, User, Mail, Lock, AlertCircle, Loader2, ArrowRight } from 'lucide-react';

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
    <div className="min-h-screen flex items-center justify-center p-4 md:p-8 cyber-grid relative overflow-hidden bg-slate-950">
      {/* Animated background gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent/20 rounded-full blur-[120px] animate-pulse delay-1000" />
      </div>

      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-12 items-center relative z-10">
        {/* Hero Section */}
        <div className="text-center lg:text-left space-y-8 px-4 lg:px-0">
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-md mb-4">
            <span className="flex h-2 w-2 rounded-full bg-primary animate-ping" />
            <span className="text-xs font-medium text-white/70 uppercase tracking-wider">v2.0 Now Live</span>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-center lg:justify-start gap-4 mb-2">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
                <Sprout size={48} className="text-white" />
              </div>
              <h1 className="text-6xl md:text-7xl font-black tracking-tighter">
                <span className="gradient-text">AgriVision</span>
              </h1>
            </div>
            
            <p className="text-xl md:text-2xl text-slate-300 font-light leading-relaxed max-w-xl mx-auto lg:mx-0">
              Transforming agriculture with <span className="text-primary font-semibold">Precision AI</span> weed detection.
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-8">
            <div className="group p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-all duration-300">
              <div className="text-4xl font-bold text-primary mb-2 group-hover:scale-110 transition-transform">98.4%</div>
              <div className="text-sm text-slate-400 font-medium uppercase tracking-wide">Model Accuracy</div>
            </div>
            <div className="group p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-all duration-300">
              <div className="text-4xl font-bold text-accent mb-2 group-hover:scale-110 transition-transform">0.05s</div>
              <div className="text-sm text-slate-400 font-medium uppercase tracking-wide">Inference Latency</div>
            </div>
          </div>
        </div>

        {/* Auth Card */}
        <div className="relative">
          <div className="absolute -inset-1 bg-gradient-to-r from-primary to-accent rounded-3xl blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
          <Card className="glass-effect border-white/10 shadow-[0_0_50px_-12px_rgba(0,0,0,0.5)] relative bg-slate-900/80 backdrop-blur-xl">
            <CardHeader className="space-y-3 pb-8">
              <CardTitle className="text-4xl font-bold text-center">
                Get Started
              </CardTitle>
              <CardDescription className="text-center text-lg text-slate-400">
                Choose your path to smarter farming
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <Tabs defaultValue="login" className="w-full">
                <TabsList className="grid w-full grid-cols-2 p-1.5 bg-slate-950/50 rounded-xl mb-8 border border-white/5">
                  <TabsTrigger 
                    value="login" 
                    className="rounded-lg py-2.5 text-base font-semibold data-[state=active]:bg-white/10 data-[state=active]:text-white transition-all"
                  >
                    Log In
                  </TabsTrigger>
                  <TabsTrigger 
                    value="signup" 
                    className="rounded-lg py-2.5 text-base font-semibold data-[state=active]:bg-white/10 data-[state=active]:text-white transition-all"
                  >
                    Join Now
                  </TabsTrigger>
                </TabsList>

                {error && (
                  <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3 animate-in fade-in slide-in-from-top-2">
                    <AlertCircle size={20} className="text-red-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm font-medium text-red-400 leading-tight">{error}</span>
                  </div>
                )}

                {/* Login Tab */}
                <TabsContent value="login" className="space-y-6">
                  <form onSubmit={handleLogin} className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="login-email" className="text-sm font-semibold text-slate-300 ml-1">Email Address</Label>
                      <div className="relative group">
                        <Mail size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                        <Input
                          id="login-email"
                          type="email"
                          placeholder="farmer@agrivision.ai"
                          value={loginEmail}
                          onChange={(e) => setLoginEmail(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-14 bg-slate-950/50 border-white/10 focus:border-primary/50 focus:ring-primary/20 text-lg rounded-xl transition-all"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between items-center ml-1">
                        <Label htmlFor="login-password" className="text-sm font-semibold text-slate-300">Password</Label>
                        <button type="button" className="text-xs font-bold text-primary hover:underline transition-all">Forgot password?</button>
                      </div>
                      <div className="relative group">
                        <Lock size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                        <Input
                          id="login-password"
                          type="password"
                          placeholder="••••••••"
                          value={loginPassword}
                          onChange={(e) => setLoginPassword(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-14 bg-slate-950/50 border-white/10 focus:border-primary/50 focus:ring-primary/20 text-lg rounded-xl transition-all"
                        />
                      </div>
                    </div>

                    <div className="space-y-3">
                      <Label className="text-sm font-semibold text-slate-300 ml-1">Select Access Role</Label>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          type="button"
                          onClick={() => setLoginRole('user')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            loginRole === 'user'
                              ? 'border-primary bg-primary/10 shadow-[0_0_20px_rgba(var(--primary-rgb),0.1)]'
                              : 'border-white/5 bg-white/5 hover:border-white/20'
                          }`}
                        >
                          <User size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${loginRole === 'user' ? 'text-primary' : 'text-slate-500'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${loginRole === 'user' ? 'text-primary' : 'text-slate-400'}`}>Farmer</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => setLoginRole('admin')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            loginRole === 'admin'
                              ? 'border-accent bg-accent/10 shadow-[0_0_20px_rgba(var(--accent-rgb),0.1)]'
                              : 'border-white/5 bg-white/5 hover:border-white/20'
                          }`}
                        >
                          <Shield size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${loginRole === 'admin' ? 'text-accent' : 'text-slate-500'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${loginRole === 'admin' ? 'text-accent' : 'text-slate-400'}`}>Admin</div>
                        </button>
                      </div>
                    </div>

                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-14 text-lg font-bold bg-gradient-to-r from-primary via-primary to-accent hover:shadow-[0_0_30px_-5px_rgba(var(--primary-rgb),0.5)] transition-all duration-500 group rounded-xl"
                    >
                      {isLoading ? (
                        <Loader2 size={24} className="animate-spin" />
                      ) : (
                        <span className="flex items-center gap-2">
                          Access Dashboard <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </span>
                      )}
                    </Button>
                  </form>
                </TabsContent>

                {/* Signup Tab */}
                <TabsContent value="signup" className="space-y-6">
                  <form onSubmit={handleSignup} className="space-y-5">
                    <div className="space-y-2">
                      <Label htmlFor="signup-name" className="text-sm font-semibold text-slate-300 ml-1">Full Name</Label>
                      <div className="relative group">
                        <User size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                        <Input
                          id="signup-name"
                          type="text"
                          placeholder="John Doe"
                          value={signupName}
                          onChange={(e) => setSignupName(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-14 bg-slate-950/50 border-white/10 focus:border-primary/50 focus:ring-primary/20 text-lg rounded-xl transition-all"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="signup-email" className="text-sm font-semibold text-slate-300 ml-1">Email Address</Label>
                      <div className="relative group">
                        <Mail size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                        <Input
                          id="signup-email"
                          type="email"
                          placeholder="your.email@example.com"
                          value={signupEmail}
                          onChange={(e) => setSignupEmail(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-14 bg-slate-950/50 border-white/10 focus:border-primary/50 focus:ring-primary/20 text-lg rounded-xl transition-all"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="signup-password" className="text-sm font-semibold text-slate-300 ml-1">Password</Label>
                      <div className="relative group">
                        <Lock size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                        <Input
                          id="signup-password"
                          type="password"
                          placeholder="••••••••"
                          value={signupPassword}
                          onChange={(e) => setSignupPassword(e.target.value)}
                          required
                          disabled={isLoading}
                          className="pl-12 h-14 bg-slate-950/50 border-white/10 focus:border-primary/50 focus:ring-primary/20 text-lg rounded-xl transition-all"
                        />
                      </div>
                      <p className="text-xs text-slate-500 ml-1">At least 6 characters with mixed case recommended</p>
                    </div>

                    <div className="space-y-3">
                      <Label className="text-sm font-semibold text-slate-300 ml-1">I want to join as</Label>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          type="button"
                          onClick={() => setSignupRole('user')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            signupRole === 'user'
                              ? 'border-primary bg-primary/10 shadow-[0_0_20px_rgba(var(--primary-rgb),0.1)]'
                              : 'border-white/5 bg-white/5 hover:border-white/20'
                          }`}
                        >
                          <User size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${signupRole === 'user' ? 'text-primary' : 'text-slate-500'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${signupRole === 'user' ? 'text-primary' : 'text-slate-400'}`}>Farmer</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => setSignupRole('admin')}
                          disabled={isLoading}
                          className={`group p-4 rounded-2xl border-2 transition-all duration-300 ${
                            signupRole === 'admin'
                              ? 'border-accent bg-accent/10 shadow-[0_0_20px_rgba(var(--accent-rgb),0.1)]'
                              : 'border-white/5 bg-white/5 hover:border-white/20'
                          }`}
                        >
                          <Shield size={28} className={`mx-auto mb-2 transition-transform group-hover:scale-110 ${signupRole === 'admin' ? 'text-accent' : 'text-slate-500'}`} />
                          <div className={`text-sm font-bold uppercase tracking-wider ${signupRole === 'admin' ? 'text-accent' : 'text-slate-400'}`}>Admin</div>
                        </button>
                      </div>
                    </div>

                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-14 text-lg font-bold bg-gradient-to-r from-primary via-primary to-accent hover:shadow-[0_0_30px_-5px_rgba(var(--primary-rgb),0.5)] transition-all duration-500 group rounded-xl"
                    >
                      {isLoading ? (
                        <Loader2 size={24} className="animate-spin" />
                      ) : (
                        <span className="flex items-center gap-2">
                          Create Account <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </span>
                      )}
                    </Button>
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
