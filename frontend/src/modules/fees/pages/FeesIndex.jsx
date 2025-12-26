import { useNavigate } from 'react-router-dom';
import { Users, Building2, Banknote } from 'lucide-react';

const submodules = [
  {
    name: 'Candidate Fees',
    icon: Users,
    path: '/fees/candidate-fees',
    color: 'bg-blue-500',
    description: 'Manage individual candidate fee payments',
  },
  {
    name: 'Center Fees',
    icon: Building2,
    path: '/fees/center-fees',
    color: 'bg-green-500',
    description: 'Track assessment center fees',
  },
];

export default function FeesIndex() {
  const navigate = useNavigate();

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Banknote className="h-8 w-8 text-rose-600" />
          UVTAB Fees
        </h1>
        <p className="text-gray-600 mt-1">Manage candidate and center fee payments</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
        {submodules.map((module) => {
          const Icon = module.icon;
          return (
            <button
              key={module.name}
              onClick={() => navigate(module.path)}
              className="group bg-white hover:bg-gray-50 rounded-lg shadow-md hover:shadow-lg p-8 transition-all duration-200 border border-gray-200 hover:border-gray-300 text-left"
            >
              <div className="flex items-start space-x-4">
                <div
                  className={`${module.color} w-16 h-16 rounded-lg flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow flex-shrink-0`}
                >
                  <Icon className="w-8 h-8 text-white" />
                </div>
                
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {module.name}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {module.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
