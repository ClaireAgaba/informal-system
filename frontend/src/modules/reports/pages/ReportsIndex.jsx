import { useNavigate } from 'react-router-dom';
import { BookImage, ClipboardList } from 'lucide-react';

const reportTypes = [
  {
    name: 'Albums',
    icon: BookImage,
    path: '/reports/albums',
    description: 'Generate Registration Lists',
    color: 'bg-indigo-500',
  },
  {
    name: 'Result List',
    icon: ClipboardList,
    path: '/reports/result-lists',
    description: 'Generate Result Lists',
    color: 'bg-orange-500',
  },
];

const ReportsIndex = () => {
  const navigate = useNavigate();

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Generate Reports</h1>
        <p className="text-gray-600 mt-2">Select a report type to generate</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        {reportTypes.map((report) => {
          const Icon = report.icon;
          return (
            <button
              key={report.name}
              onClick={() => navigate(report.path)}
              className="group relative bg-white hover:bg-gray-50 rounded-lg p-6 transition-all duration-200 hover:shadow-lg border border-gray-200 hover:border-gray-300"
            >
              <div className="flex flex-col items-center space-y-3">
                <div
                  className={`${report.color} w-16 h-16 rounded-lg flex items-center justify-center shadow group-hover:shadow-md transition-shadow`}
                >
                  <Icon className="w-8 h-8 text-white" />
                </div>
                
                <div className="text-center">
                  <h3 className="text-gray-900 font-semibold text-base">
                    {report.name}
                  </h3>
                  <p className="text-gray-500 text-xs mt-1">
                    {report.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ReportsIndex;
