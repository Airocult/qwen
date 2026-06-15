import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CheckCircle, AlertCircle, Shield, FileCheck, Download } from 'lucide-react';
import { StatusBadge } from '../components/common';
import { designApi } from '../utils/api';
import { useDesignStore } from '../hooks/useDesignStore';
import type { ValidationResult } from '../types';
import toast from 'react-hot-toast';

export const ValidationScreen: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentDesign, updateDesign, setValidationResult } = useDesignStore();
  const [isRunning, setIsRunning] = useState(false);
  const [validationResult, setValidationResultState] = useState<ValidationResult | null>(null);

  const designId = location.state?.designId || currentDesign?.id;

  const handleRunValidation = async () => {
    if (!designId) {
      toast.error('No design loaded');
      return;
    }

    setIsRunning(true);

    try {
      // Mock validation results for demo
      await new Promise((resolve) => setTimeout(resolve, 2000));
      
      const mockResult: ValidationResult = {
        passed: true,
        errors: [],
        warnings: [
          { id: 'w1', message: 'Consider increasing clearance on high-voltage nets', suggestion: 'Increase to 0.5mm minimum' },
          { id: 'w2', message: 'Thermal relief recommended for large copper pours', suggestion: 'Add thermal spokes' },
        ],
        drcChecks: [
          { checkName: 'Minimum Trace Width', passed: true, violations: 0, details: 'All traces meet 0.15mm minimum' },
          { checkName: 'Minimum Clearance', passed: true, violations: 0, details: 'All clearances meet 0.15mm minimum' },
          { checkName: 'Impedance Control', passed: true, violations: 0, details: 'Controlled impedance nets within ±10% tolerance' },
          { checkName: 'Via Spacing', passed: true, violations: 0, details: 'All vias properly spaced' },
          { checkName: 'Annular Ring', passed: true, violations: 0, details: 'All vias have sufficient annular ring' },
          { checkName: 'Solder Mask Sliver', passed: true, violations: 0, details: 'No solder mask slivers detected' },
        ],
      };

      setValidationResultState(mockResult);
      setValidationResult(mockResult);
      
      if (mockResult.passed) {
        toast.success('All DRC checks passed! Design ready for Gerber generation.');
        // Update design status
        if (currentDesign) {
          updateDesign({ ...currentDesign, status: 'ready_for_gerber' });
        }
      } else {
        toast.error(`Validation failed with ${mockResult.errors.length} errors.`);
      }
    } catch (error) {
      console.error('Failed to validate design:', error);
      toast.error('Failed to validate design. Please try again.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleGenerateGerber = async () => {
    if (!designId) {
      toast.error('No design loaded');
      return;
    }

    try {
      const result = await designApi.generateGerber(designId);
      
      toast.success('Gerber files generated successfully!');
      
      // In a real app, this would trigger a download
      setTimeout(() => {
        navigate('/gerber', { state: { designId, gerberFiles: result.gerberFiles } });
      }, 1000);
    } catch (error) {
      console.error('Failed to generate Gerber:', error);
      toast.error('Failed to generate Gerber files.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Design Validation</h1>
              <p className="mt-2 text-gray-600">Comprehensive DRC and electrical rule checking</p>
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
          {/* Left Column - Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Summary Card */}
            {validationResult && (
              <div className={`card ${validationResult.passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex items-center space-x-4">
                  {validationResult.passed ? (
                    <CheckCircle className="w-12 h-12 text-success" />
                  ) : (
                    <AlertCircle className="w-12 h-12 text-error" />
                  )}
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">
                      {validationResult.passed ? 'All Checks Passed!' : 'Validation Failed'}
                    </h2>
                    <p className="text-gray-600">
                      {validationResult.drcChecks.filter((c) => c.passed).length} of{' '}
                      {validationResult.drcChecks.length} DRC checks passed
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* DRC Checks */}
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">DRC Check Results</h2>
              
              {isRunning ? (
                <div className="space-y-4">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg animate-pulse">
                      <div className="flex items-center space-x-3">
                        <div className="w-6 h-6 bg-gray-300 rounded-full"></div>
                        <span className="text-gray-500">Running check {i + 1}...</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : validationResult ? (
                <div className="space-y-3">
                  {validationResult.drcChecks.map((check, index) => (
                    <div
                      key={index}
                      className={`flex items-center justify-between p-4 rounded-lg border ${
                        check.passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        {check.passed ? (
                          <CheckCircle className="w-5 h-5 text-success" />
                        ) : (
                          <AlertCircle className="w-5 h-5 text-error" />
                        )}
                        <div>
                          <p className="font-medium text-gray-900">{check.checkName}</p>
                          {check.details && (
                            <p className="text-sm text-gray-600 mt-1">{check.details}</p>
                          )}
                        </div>
                      </div>
                      <span className={`text-sm font-medium ${
                        check.violations > 0 ? 'text-error' : 'text-success'
                      }`}>
                        {check.violations} violations
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="font-medium">Run validation to check your design</p>
                  <p className="text-sm mt-1">Checks include DRC, impedance, clearance, and more</p>
                </div>
              )}
            </div>

            {/* Warnings */}
            {validationResult && validationResult.warnings.length > 0 && (
              <div className="card border-yellow-200 bg-yellow-50">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <AlertCircle className="w-5 h-5 text-warning mr-2" />
                  Warnings ({validationResult.warnings.length})
                </h3>
                <div className="space-y-3">
                  {validationResult.warnings.map((warning) => (
                    <div key={warning.id} className="p-3 bg-white rounded-lg border border-yellow-200">
                      <p className="text-sm text-gray-900">{warning.message}</p>
                      {warning.suggestion && (
                        <p className="text-xs text-gray-600 mt-1">
                          💡 {warning.suggestion}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Actions */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Validation Controls</h2>
              
              <button
                onClick={handleRunValidation}
                disabled={isRunning}
                className="w-full btn-primary flex items-center justify-center space-x-2 mb-4"
              >
                {isRunning ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Running Checks...</span>
                  </>
                ) : (
                  <>
                    <FileCheck className="w-4 h-4" />
                    <span>Run Full Validation</span>
                  </>
                )}
              </button>

              {validationResult?.passed && (
                <button
                  onClick={handleGenerateGerber}
                  className="w-full btn-primary bg-green-600 hover:bg-green-700 flex items-center justify-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Generate Gerber Files</span>
                </button>
              )}

              {!validationResult?.passed && validationResult && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700 font-medium">
                    Please fix all errors before generating Gerber files
                  </p>
                </div>
              )}
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Standards Compliance</h3>
              <div className="space-y-3">
                <ComplianceItem standard="IPC-2152" description="Current-carrying capacity" />
                <ComplianceItem standard="IPC-2221" description="Generic PCB design standards" />
                <ComplianceItem standard="IPC-2141" description="Controlled impedance" />
                <ComplianceItem standard="IEC 60950" description="Safety clearances" />
              </div>
            </div>

            <div className="card bg-blue-50 border-blue-200">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                Validation Coverage
              </h3>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• Minimum trace width</li>
                <li>• Minimum clearance</li>
                <li>• Impedance control (±10%)</li>
                <li>• Via spacing & annular ring</li>
                <li>• Solder mask slivers</li>
                <li>• Copper pour isolation</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

interface ComplianceItemProps {
  standard: string;
  description: string;
}

const ComplianceItem: React.FC<ComplianceItemProps> = ({ standard, description }) => (
  <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
    <div>
      <p className="font-medium text-gray-900 text-sm">{standard}</p>
      <p className="text-xs text-gray-600 mt-1">{description}</p>
    </div>
  </div>
);
