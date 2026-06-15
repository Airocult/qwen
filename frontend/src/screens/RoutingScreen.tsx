import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Route, Zap, Layers, CheckCircle, AlertCircle } from 'lucide-react';
import { ProgressBar, StatusBadge } from '../components/common';
import { designApi } from '../utils/api';
import { useDesignStore } from '../hooks/useDesignStore';
import type { RoutingProgress } from '../types';
import toast from 'react-hot-toast';

export const RoutingScreen: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentDesign, setRoutingProgress } = useDesignStore();
  const [isRouting, setIsRouting] = useState(false);
  const [routingProgress, setRoutingProgressState] = useState<RoutingProgress>({
    status: 'idle',
    progress: 0,
    totalNets: 0,
    routedNets: 0,
    failedNets: 0,
    elapsedTime: 0,
  });
  const [elapsedTime, setElapsedTime] = useState(0);

  const designId = location.state?.designId || currentDesign?.id;

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    
    if (isRouting && routingProgress.status === 'running') {
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
        
        // Simulate progress updates
        setRoutingProgressState((prev) => {
          const increment = Math.random() * 5 + 2;
          const newProgress = Math.min(prev.progress + increment, 95);
          const newRoutedNets = Math.floor((newProgress / 100) * prev.totalNets);
          
          return {
            ...prev,
            progress: newProgress,
            routedNets: newRoutedNets,
            elapsedTime: prev.elapsedTime + 1,
            currentNet: `NET_${newRoutedNets + 1}`,
          };
        });
      }, 1000);
    }

    return () => clearInterval(interval);
  }, [isRouting, routingProgress.status]);

  const handleStartRouting = async () => {
    if (!designId) {
      toast.error('No design loaded');
      return;
    }

    setIsRouting(true);
    setElapsedTime(0);
    
    try {
      // Initialize with mock data
      const mockTotalNets = currentDesign?.nets?.length || 25;
      setRoutingProgressState({
        status: 'running',
        progress: 0,
        totalNets: mockTotalNets,
        routedNets: 0,
        failedNets: 0,
        elapsedTime: 0,
        currentNet: 'NET_1',
      });

      const result = await designApi.routeDesign(designId);
      
      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const progress = await designApi.getRoutingProgress(result.jobId);
          setRoutingProgressState(progress);
          setRoutingProgress(progress);
          
          if (progress.status === 'completed' || progress.status === 'failed') {
            clearInterval(pollInterval);
            setIsRouting(false);
            
            if (progress.status === 'completed') {
              toast.success(`Routing completed! ${progress.routedNets} nets routed successfully.`);
              setTimeout(() => {
                navigate('/validation', { state: { designId } });
              }, 1500);
            } else {
              toast.error(`Routing failed. ${progress.failedNets} nets could not be routed.`);
            }
          }
        } catch (error) {
          console.error('Failed to get progress:', error);
        }
      }, 2000);

    } catch (error) {
      console.error('Failed to start routing:', error);
      toast.error('Failed to start routing. Please try again.');
      setIsRouting(false);
      setRoutingProgressState((prev) => ({ ...prev, status: 'failed' }));
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!currentDesign && !designId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">No Design Loaded</h2>
          <button onClick={() => navigate('/')} className="btn-primary">
            Import Schematic
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Deterministic Routing</h1>
              <p className="mt-2 text-gray-600">A* maze routing with impedance control</p>
            </div>
            {currentDesign && (
              <StatusBadge status={currentDesign.status} />
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Visualization */}
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Routing Progress</h2>
              
              {/* Board visualization placeholder */}
              <div className="aspect-video bg-gray-900 rounded-lg border-2 border-gray-700 flex items-center justify-center relative overflow-hidden">
                {isRouting ? (
                  <div className="absolute inset-0 bg-grid-pattern opacity-20"></div>
                ) : null}
                
                <div className="text-center text-gray-400 z-10">
                  <Route className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="font-medium">
                    {isRouting ? 'Routing in progress...' : 'Board Routing View'}
                  </p>
                  {isRouting && (
                    <p className="text-sm mt-2 text-primary-400">
                      Current: {routingProgress.currentNet}
                    </p>
                  )}
                </div>

                {/* Animated routing lines simulation */}
                {isRouting && (
                  <div className="absolute inset-0 pointer-events-none">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className="absolute h-0.5 bg-primary-500 animate-pulse"
                        style={{
                          width: `${Math.random() * 200 + 50}px`,
                          left: `${Math.random() * 80}%`,
                          top: `${20 + i * 15}%`,
                          animationDelay: `${i * 0.3}s`,
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Progress bar */}
              <div className="mt-6">
                <ProgressBar
                  progress={routingProgress.progress}
                  status={routingProgress.status}
                  label={`Routing Net ${routingProgress.routedNets + 1} of ${routingProgress.totalNets}`}
                  details={{
                    currentNet: routingProgress.currentNet,
                    totalNets: routingProgress.totalNets,
                    routedNets: routingProgress.routedNets,
                    failedNets: routingProgress.failedNets,
                  }}
                />
              </div>

              {/* Stats */}
              <div className="mt-6 grid grid-cols-4 gap-4">
                <StatBox
                  label="Elapsed Time"
                  value={formatTime(elapsedTime)}
                  icon={<Zap className="w-4 h-4" />}
                />
                <StatBox
                  label="Routed Nets"
                  value={routingProgress.routedNets.toString()}
                  icon={<CheckCircle className="w-4 h-4 text-success" />}
                />
                <StatBox
                  label="Remaining"
                  value={(routingProgress.totalNets - routingProgress.routedNets).toString()}
                  icon={<Layers className="w-4 h-4" />}
                />
                {routingProgress.failedNets > 0 && (
                  <StatBox
                    label="Failed"
                    value={routingProgress.failedNets.toString()}
                    icon={<AlertCircle className="w-4 h-4 text-error" />}
                    isError
                  />
                )}
              </div>
            </div>

            {/* Routing parameters */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Routing Parameters</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <ParameterItem label="Grid Size" value="0.1mm" />
                <ParameterItem label="Via Minimization" value="Enabled" />
                <ParameterItem label="Impedance Control" value="±10%" />
                <ParameterItem label="Differential Pairs" value="Auto-detect" />
              </div>
            </div>
          </div>

          {/* Right Column - Controls */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Routing Control</h2>
              
              <div className="space-y-4">
                <RoutingOption
                  icon={<Zap className="w-5 h-5 text-yellow-600" />}
                  title="Impedance Control"
                  description="Maintain target impedance for high-speed signals"
                  enabled
                />
                
                <RoutingOption
                  icon={<Layers className="w-5 h-5 text-blue-600" />}
                  title="Layer Optimization"
                  description="Automatic layer assignment with preferred directions"
                  enabled
                />
                
                <RoutingOption
                  icon={<Route className="w-5 h-5 text-green-600" />}
                  title="Via Minimization"
                  description="Reduce via count for better signal integrity"
                  enabled
                />
              </div>

              <div className="mt-6 space-y-3">
                <button
                  onClick={handleStartRouting}
                  disabled={isRouting || routingProgress.status === 'completed'}
                  className="w-full btn-primary flex items-center justify-center space-x-2"
                >
                  {isRouting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Routing...</span>
                    </>
                  ) : routingProgress.status === 'completed' ? (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      <span>Completed</span>
                    </>
                  ) : (
                    <>
                      <Route className="w-4 h-4" />
                      <span>Start Routing</span>
                    </>
                  )}
                </button>

                {routingProgress.status === 'completed' && (
                  <button
                    onClick={() => navigate('/validation', { state: { designId } })}
                    className="w-full btn-secondary"
                  >
                    Continue to Validation
                  </button>
                )}
              </div>
            </div>

            <div className="card bg-green-50 border-green-200">
              <h3 className="text-sm font-semibold text-green-900 mb-2">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                Deterministic Advantages
              </h3>
              <ul className="text-xs text-green-700 space-y-1">
                <li>• 100% reproducible results</li>
                <li>• Guaranteed constraint satisfaction</li>
                <li>• No impedance mismatches</li>
                <li>• Full DRC compliance</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

interface StatBoxProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  isError?: boolean;
}

const StatBox: React.FC<StatBoxProps> = ({ label, value, icon, isError }) => (
  <div className={`bg-gray-50 rounded-lg p-3 ${isError ? 'bg-red-50' : ''}`}>
    <div className="flex items-center space-x-2">
      {icon}
      <span className={`text-lg font-bold ${isError ? 'text-error' : 'text-gray-900'}`}>
        {value}
      </span>
    </div>
    <div className="text-xs text-gray-600 mt-1">{label}</div>
  </div>
);

interface ParameterItemProps {
  label: string;
  value: string;
}

const ParameterItem: React.FC<ParameterItemProps> = ({ label, value }) => (
  <div className="text-center p-3 bg-gray-50 rounded-lg">
    <div className="text-sm font-semibold text-gray-900">{value}</div>
    <div className="text-xs text-gray-600 mt-1">{label}</div>
  </div>
);

interface RoutingOptionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  enabled: boolean;
}

const RoutingOption: React.FC<RoutingOptionProps> = ({
  icon,
  title,
  description,
  enabled,
}) => (
  <div className={`flex items-start space-x-3 p-3 rounded-lg border ${
    enabled ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-gray-50'
  }`}>
    <div className="flex-shrink-0">{icon}</div>
    <div>
      <h4 className="font-medium text-gray-900 text-sm">{title}</h4>
      <p className="text-xs text-gray-600 mt-1">{description}</p>
    </div>
  </div>
);
