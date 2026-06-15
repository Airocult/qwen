import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Shield, Layers, CheckCircle } from 'lucide-react';
import { FileUpload } from '../components/common';
import { designApi } from '../utils/api';
import { useDesignStore } from '../hooks/useDesignStore';
import toast from 'react-hot-toast';

export const SchematicImportScreen: React.FC = () => {
  const navigate = useNavigate();
  const { addDesign, setCurrentDesign } = useDesignStore();
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = async (file: File, format: 'kicad' | 'easyeda' | 'generic') => {
    setIsUploading(true);
    
    try {
      const design = await designApi.parseSchematic(file, format);
      
      addDesign(design);
      setCurrentDesign(design);
      
      toast.success('Schematic parsed successfully!');
      navigate('/placement', { state: { designId: design.id } });
    } catch (error) {
      console.error('Failed to parse schematic:', error);
      toast.error('Failed to parse schematic. Please check the file format.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">PCB Design Studio</h1>
          <p className="mt-2 text-gray-600">Professional deterministic PCB routing system</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Left Column - Upload */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Import Schematic</h2>
              <p className="text-gray-600 mb-6">
                Upload your schematic file in KiCAD, EasyEDA, or generic format. 
                Our deterministic engine will process it and prepare for optimal routing.
              </p>
              
              <FileUpload
                onFileSelect={handleFileSelect}
                disabled={isUploading}
              />

              {isUploading && (
                <div className="mt-6 p-4 bg-primary-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
                    <span className="text-primary-700 font-medium">Parsing schematic...</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Features */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Why Choose Deterministic Routing?</h2>
              
              <div className="space-y-4">
                <FeatureCard
                  icon={<Zap className="w-6 h-6 text-yellow-600" />}
                  title="100% Constraint Satisfaction"
                  description="Unlike AI-based systems, our deterministic approach guarantees all electrical rules are followed."
                />
                
                <FeatureCard
                  icon={<Shield className="w-6 h-6 text-green-600" />}
                  title="IPC Standards Compliant"
                  description="Automatically calculates impedance, trace width, and clearances per IPC-2141, IPC-2152, and IPC-2221."
                />
                
                <FeatureCard
                  icon={<Layers className="w-6 h-6 text-blue-600" />}
                  title="Multi-Layer Support"
                  description="Intelligent layer assignment with preferred direction routing for optimal signal integrity."
                />
                
                <FeatureCard
                  icon={<CheckCircle className="w-6 h-6 text-purple-600" />}
                  title="Built-in DRC Validation"
                  description="Real-time design rule checking ensures manufacturability before Gerber generation."
                />
              </div>
            </div>

            <div className="card bg-gradient-to-r from-primary-500 to-primary-600 text-white">
              <h3 className="text-lg font-semibold mb-2">Supported Formats</h3>
              <ul className="space-y-2 text-sm">
                <li>• KiCAD (.kicad_sch, .sch)</li>
                <li>• EasyEDA (.json)</li>
                <li>• Generic netlist formats</li>
                <li>• Export to Gerber (RS-274X)</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description }) => (
  <div className="flex items-start space-x-4 p-4 rounded-lg hover:bg-gray-50 transition-colors">
    <div className="flex-shrink-0">{icon}</div>
    <div>
      <h3 className="font-medium text-gray-900">{title}</h3>
      <p className="text-sm text-gray-600 mt-1">{description}</p>
    </div>
  </div>
);
