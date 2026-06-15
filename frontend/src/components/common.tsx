import React from 'react';
import { FileUp, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File, format: 'kicad' | 'easyeda' | 'generic') => void;
  acceptedFormats?: string[];
  disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  acceptedFormats = ['.sch', '.kicad_sch', '.json'],
  disabled = false,
}) => {
  const [dragActive, setDragActive] = React.useState(false);
  const [selectedFormat, setSelectedFormat] = React.useState<'kicad' | 'easyeda' | 'generic'>('kicad');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    onFileSelect(file, selectedFormat);
  };

  return (
    <div className="w-full">
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
          dragActive
            ? 'border-primary-500 bg-primary-50 scale-[1.02]'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          onChange={handleChange}
          accept={acceptedFormats.join(',')}
          disabled={disabled}
        />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className={`p-4 rounded-full ${dragActive ? 'bg-primary-100' : 'bg-gray-100'}`}>
              <FileUp className={`w-8 h-8 ${dragActive ? 'text-primary-600' : 'text-gray-400'}`} />
            </div>
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              Drop your schematic file here, or click to browse
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Supports KiCAD, EasyEDA, and generic schematic formats
            </p>
          </div>

          <div className="flex justify-center gap-2 pt-2">
            {(['kicad', 'easyeda', 'generic'] as const).map((format) => (
              <button
                key={format}
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  setSelectedFormat(format);
                }}
                className={`px-3 py-1 text-sm rounded-full transition-colors ${
                  selectedFormat === format
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {format.charAt(0).toUpperCase() + format.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

interface ProgressBarProps {
  progress: number;
  status: 'idle' | 'running' | 'completed' | 'failed';
  label?: string;
  showDetails?: boolean;
  details?: {
    currentNet?: string;
    totalNets?: number;
    routedNets?: number;
    failedNets?: number;
  };
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  status,
  label,
  showDetails = true,
  details,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-success';
      case 'failed':
        return 'bg-error';
      case 'running':
        return 'bg-primary-600';
      default:
        return 'bg-gray-300';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-success" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-error" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />;
      default:
        return null;
    }
  };

  return (
    <div className="w-full space-y-2">
      {(label || status !== 'idle') && (
        <div className="flex items-center justify-between">
          {label && <span className="text-sm font-medium text-gray-700">{label}</span>}
          {getStatusIcon()}
        </div>
      )}
      
      <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ease-out ${getStatusColor()}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>

      {showDetails && details && (
        <div className="grid grid-cols-3 gap-4 text-xs text-gray-600">
          {details.currentNet && (
            <div>
              <span className="font-medium">Current:</span> {details.currentNet}
            </div>
          )}
          {details.totalNets !== undefined && (
            <div>
              <span className="font-medium">Total Nets:</span> {details.totalNets}
            </div>
          )}
          {details.routedNets !== undefined && (
            <div>
              <span className="font-medium">Routed:</span> {details.routedNets}
            </div>
          )}
          {details.failedNets !== undefined && details.failedNets > 0 && (
            <div className="text-error">
              <span className="font-medium">Failed:</span> {details.failedNets}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface StatusBadgeProps {
  status: 'draft' | 'routed' | 'validated' | 'ready_for_gerber';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const config = {
    draft: { color: 'bg-gray-100 text-gray-700', label: 'Draft' },
    routed: { color: 'bg-blue-100 text-blue-700', label: 'Routed' },
    validated: { color: 'bg-yellow-100 text-yellow-700', label: 'Validated' },
    ready_for_gerber: { color: 'bg-green-100 text-green-700', label: 'Ready for Gerber' },
  };

  const { color, label } = config[status];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
};
