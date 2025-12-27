import { Link } from 'react-router-dom';
import { FileSpreadsheet, Upload, Printer } from 'lucide-react';

export default function MarksheetsIndex() {
  const submodules = [
    {
      name: 'Generate Marksheets',
      description: 'Generate Excel marksheet templates for assessments',
      icon: FileSpreadsheet,
      path: '/marksheets/generate',
      color: 'blue',
    },
    {
      name: 'Upload Marksheets',
      description: 'Upload completed marksheets with results',
      icon: Upload,
      path: '/marksheets/upload',
      color: 'green',
    },
    {
      name: 'Print Marksheets',
      description: 'Print marksheets for distribution',
      icon: Printer,
      path: '/marksheets/print',
      color: 'purple',
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Marksheets</h1>
        <p className="text-gray-600 mt-1">Manage assessment marksheets</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {submodules.map((module) => {
          const Icon = module.icon;
          return (
            <Link
              key={module.path}
              to={module.path}
              className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow`}
            >
              <div className={`w-12 h-12 bg-${module.color}-100 rounded-lg flex items-center justify-center mb-4`}>
                <Icon className={`h-6 w-6 text-${module.color}-600`} />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{module.name}</h3>
              <p className="text-gray-600 text-sm">{module.description}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
