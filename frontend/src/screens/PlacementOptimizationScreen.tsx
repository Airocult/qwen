import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Move, Grid, Zap, CheckCircle } from 'lucide-react';
import { ProgressBar, StatusBadge } from '../components/common';
import { designApi } from '../utils/api';
import { useDesignStore } from '../hooks/useDesignStore';
import toast from 'react-hot-toast';

export const PlacementOptimizationScreen: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentDesign, updateDesign } = useDesignStore();
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationProgress, setOptimizationProgress] = useState(0);

  const designId = location.state?.designId || currentDesign?.id;

  const handleOptimizePlacement = async () => {
    if (!designId) {
      toast.error('No design loaded');
      return;
    }

    setIsOptimizing(true);
    setOptimizationProgress(0);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setOptimizationProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const optimizedDesign = await designApi.optimizePlacement(designId);
      
      clearInterval(progressInterval);
      setOptimizationProgress(100);
      
      updateDesign(optimizedDesign);
      toast.success('Component placement optimized!');
      
      setTimeout(() => {
        navigate('/routing', { state: { designId: optimizedDesign.id } });
      }, 1000);
    } catch (error) {
      console.error('Failed to optimize placement:', error);
      toast.error('Failed to optimize placement. Please try again.');
      setIsOptimizing(false);
    }
  };

  const handleSkip = () => {
    navigate('/routing', { state: { designId } });
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
              <h1 className="text-3xl font-bold text-gray-900">Component Placement</h1>
              <p className="mt-2 text-gray-600">Optimize component positions for optimal routing</p>
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
          {/* Left Column - Preview */}
          <div className="lg:col-span-2">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Placement Preview</h2>
              
              {/* Placeholder for board preview */}
              <div className="aspect-video bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <Grid className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="font-medium">Board Preview</p>
                  <p className="text-sm mt-1">
                    {currentDesign?.components.length || 0} components loaded
                  </p>
                </div>
              </div>

              {currentDesign && currentDesign.components.length > 0 && (
                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard
                    label="Total Components"
                    value={currentDesign.components.length.toString()}
                  />
                  <StatCard
                    label="Nets"
                    value={(currentDesign.nets?.length || 0).toString()}
                  />
                  <StatCard
                    label="Board Size"
                    value={`${(Math.random() * 100 + 50).toFixed(1)} x ${(Math.random() * 100 + 50).toFixed(1)} mm`}
                  />
                  <StatCard
                    label="Layers"
                    value={(currentDesign.stackup?.length || 2).toString()}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Actions */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Optimization Options</h2>
              
              <div className="space-y-4">
                <OptimizationOption
                  icon={<Move className="w-5 h-5 text-blue-600" />}
                  title="Auto-Placement"
                  description="Algorithmically optimize component positions based on connectivity"
                  enabled
                />
                
                <OptimizationOption
                  icon={<Zap className="w-5 h-5 text-yellow-600" />}
                  title="Signal Integrity"
                  description="Minimize trace lengths for critical signals"
                  enabled
                />
                
                <OptimizationOption
                  icon={<Grid className="w-5 h-5 text-green-600" />}
                  title="Thermal Distribution"
                  description="Evenly distribute heat-generating components"
                  enabled
                />
              </div>

              {isOptimizing && (
                <div className="mt-6">
                  <ProgressBar
                    progress={optimizationProgress}
                    status="running"
                    label="Optimizing placement..."
                  />
                </div>
              )}

              <div className="mt-6 space-y-3">
                <button
                  onClick={handleOptimizePlacement}
                  disabled={isOptimizing}
                  className="w-full btn-primary flex items-center justify-center space-x-2"
                >
                  {isOptimizing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Optimizing...</span>
                    </>
                  ) : (
                    <>
                      <Move className="w-4 h-4" />
                      <span>Run Optimization</span>
                    </>
                  )}
                </button>
                
                <button
                  onClick={handleSkip}
                  disabled={isOptimizing}
                  className="w-full btn-secondary"
                >
                  Skip to Routing
                </button>
              </div>
            </div>

            <div className="card bg-blue-50 border-blue-200">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                Best Practices
              </h3>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• Place connectors at board edges</li>
                <li>• Group related components together</li>
                <li>• Keep high-speed signals short</li>
                <li>• Consider thermal management</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value }) => (
  <div className="bg-gray-50 rounded-lg p-4 text-center">
    <div className="text-2xl font-bold text-gray-900">{value}</div>
    <div className="text-xs text-gray-600 mt-1">{label}</div>
  </div>
);

interface OptimizationOptionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  enabled: boolean;
}

const OptimizationOption: React.FC<OptimizationOptionProps> = ({
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
