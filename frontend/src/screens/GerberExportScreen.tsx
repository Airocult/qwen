import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Download, FileCheck, CheckCircle, Package } from 'lucide-react';
import { StatusBadge } from '../components/common';
import { useDesignStore } from '../hooks/useDesignStore';

export const GerberExportScreen: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentDesign } = useDesignStore();
  
  const gerberFiles = location.state?.gerberFiles || [
    { name: 'top_copper.gtl', layer: 'Top Copper', size: '245 KB' },
    { name: 'bottom_copper.gbl', layer: 'Bottom Copper', size: '198 KB' },
    { name: 'top_silkscreen.gto', layer: 'Top Silkscreen', size: '45 KB' },
    { name: 'bottom_silkscreen.gbo', layer: 'Bottom Silkscreen', size: '38 KB' },
    { name: 'top_soldermask.gts', layer: 'Top Soldermask', size: '156 KB' },
    { name: 'bottom_soldermask.gbs', layer: 'Bottom Soldermask', size: '142 KB' },
    { name: 'drill_file.drl', layer: 'Drill Data', size: '67 KB' },
    { name: 'board_outline.gko', layer: 'Board Outline', size: '12 KB' },
  ];

  const handleDownloadAll = () => {
    // In a real app, this would trigger a ZIP download
    alert('Downloading all Gerber files as PCB_Gerber_Files.zip...');
  };

  const handleDownloadSingle = (fileName: string) => {
    // In a real app, this would trigger individual file download
    alert(`Downloading ${fileName}...`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Gerber Export</h1>
              <p className="mt-2 text-gray-600">Production-ready Gerber files ready for manufacturing</p>
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
          {/* Left Column - File List */}
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Gerber Files</h2>
                <button
                  onClick={handleDownloadAll}
                  className="btn-primary flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Download All (ZIP)</span>
                </button>
              </div>

              <div className="space-y-3">
                {gerberFiles.map((file: any) => (
                  <div
                    key={file.name}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-primary-300 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="p-2 bg-white rounded-lg">
                        <FileCheck className="w-6 h-6 text-primary-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-600">{file.layer}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-gray-500">{file.size}</span>
                      <button
                        onClick={() => handleDownloadSingle(file.name)}
                        className="btn-secondary text-sm py-1 px-3"
                      >
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Manufacturing Notes */}
            <div className="card bg-blue-50 border-blue-200">
              <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                <Package className="w-5 h-5 mr-2" />
                Manufacturing Specifications
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <SpecItem label="Board Thickness" value="1.6mm (Standard)" />
                <SpecItem label="Copper Weight" value="1oz (35µm)" />
                <SpecItem label="Min Trace/Space" value="0.15mm / 0.15mm" />
                <SpecItem label="Min Via Size" value="0.3mm drill" />
                <SpecItem label="Surface Finish" value="HASL Lead-Free" />
                <SpecItem label="Solder Mask Color" value="Green" />
              </div>
            </div>
          </div>

          {/* Right Column - Summary & Actions */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Export Summary</h2>
              
              <div className="space-y-4">
                <SummaryItem
                  label="Total Files"
                  value={gerberFiles.length.toString()}
                  icon={<FileCheck className="w-4 h-4" />}
                />
                <SummaryItem
                  label="Total Size"
                  value="903 KB"
                  icon={<Package className="w-4 h-4" />}
                />
                <SummaryItem
                  label="Layers"
                  value="2 (Double-sided)"
                  icon={<CheckCircle className="w-4 h-4" />}
                />
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Next Steps</h3>
                <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                  <li>Download Gerber files (ZIP)</li>
                  <li>Review files with Gerber viewer</li>
                  <li>Upload to PCB manufacturer</li>
                  <li>Specify manufacturing requirements</li>
                </ol>
              </div>
            </div>

            <div className="card bg-green-50 border-green-200">
              <h3 className="text-sm font-semibold text-green-900 mb-3">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                Quality Assurance
              </h3>
              <ul className="text-xs text-green-700 space-y-2">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>All DRC checks passed</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Impedance controlled traces verified</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>IPC standards compliance confirmed</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Manufacturing rules validated</span>
                </li>
              </ul>
            </div>

            <div className="card">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Recommended Manufacturers</h3>
              <div className="space-y-2">
                <ManufacturerOption name="PCBWay" leadTime="24 hours" price="From $5" />
                <ManufacturerOption name="JLCPCB" leadTime="24 hours" price="From $2" />
                <ManufacturerOption name="Seeed Studio" leadTime="48 hours" price="From $4.90" />
              </div>
            </div>

            <button
              onClick={() => navigate('/')}
              className="w-full btn-secondary"
            >
              Start New Project
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

interface SummaryItemProps {
  label: string;
  value: string;
  icon: React.ReactNode;
}

const SummaryItem: React.FC<SummaryItemProps> = ({ label, value, icon }) => (
  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
    <div className="flex items-center space-x-3">
      <div className="text-gray-500">{icon}</div>
      <span className="text-sm text-gray-600">{label}</span>
    </div>
    <span className="font-semibold text-gray-900">{value}</span>
  </div>
);

interface SpecItemProps {
  label: string;
  value: string;
}

const SpecItem: React.FC<SpecItemProps> = ({ label, value }) => (
  <div className="p-3 bg-white rounded-lg border border-blue-100">
    <p className="text-xs text-blue-600 mb-1">{label}</p>
    <p className="font-medium text-blue-900">{value}</p>
  </div>
);

interface ManufacturerOptionProps {
  name: string;
  leadTime: string;
  price: string;
}

const ManufacturerOption: React.FC<ManufacturerOptionProps> = ({ name, leadTime, price }) => (
  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
    <div>
      <p className="font-medium text-gray-900 text-sm">{name}</p>
      <p className="text-xs text-gray-600">{leadTime} turnaround</p>
    </div>
    <span className="text-sm font-semibold text-green-600">{price}</span>
  </div>
);
