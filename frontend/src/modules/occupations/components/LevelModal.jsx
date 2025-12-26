import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { X, Save } from 'lucide-react';
import Button from '@shared/components/Button';

const LevelModal = ({ isOpen, onClose, onSubmit, level, isLoading }) => {
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  useEffect(() => {
    if (level) {
      reset({
        level_name: level.level_name,
        structure_type: level.structure_type,
        formal_fee: level.formal_fee,
        workers_pas_base_fee: level.workers_pas_base_fee,
        workers_pas_per_module_fee: level.workers_pas_per_module_fee,
        modular_fee_single_module: level.modular_fee_single_module,
        modular_fee_double_module: level.modular_fee_double_module,
      });
    } else {
      reset({
        level_name: '',
        structure_type: 'modules',
        formal_fee: '0.00',
        workers_pas_base_fee: '0.00',
        workers_pas_per_module_fee: '0.00',
        modular_fee_single_module: '0.00',
        modular_fee_double_module: '0.00',
      });
    }
  }, [level, reset]);

  if (!isOpen) return null;

  const handleFormSubmit = (data) => {
    onSubmit(data);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">
            {level ? 'Edit Level' : 'Add Occupation Level'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6 space-y-6">
          {/* Level Information */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-3">Level Information</h3>
            <p className="text-xs text-blue-700 mb-4">
              Define the level name and whether it contains modules or papers
            </p>

            <div className="space-y-4">
              {/* Level Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Level name *
                </label>
                <input
                  type="text"
                  {...register('level_name', { required: 'Level name is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter level name (e.g., Level 1, Level 2, etc.)"
                />
                {errors.level_name && (
                  <p className="text-red-500 text-xs mt-1">{errors.level_name.message}</p>
                )}
              </div>

              {/* Structure Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Structure type:
                </label>
                <select
                  {...register('structure_type', { required: 'Structure type is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="modules">Modules</option>
                  <option value="papers">Papers</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Does this level contain modules or papers?
                </p>
                {errors.structure_type && (
                  <p className="text-red-500 text-xs mt-1">{errors.structure_type.message}</p>
                )}
              </div>
            </div>
          </div>

          {/* Billing Information */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-green-900 mb-3">Billing Information</h3>
            <p className="text-xs text-green-700 mb-4">
              Set the fees for different registration types (all amounts in UGX)
            </p>

            <div className="space-y-4">
              {/* Formal Fee */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Formal Fee (UGX):
                </label>
                <input
                  type="number"
                  step="0.01"
                  {...register('formal_fee')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="0.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Fee for Formal registration (varies by level)
                </p>
              </div>

              {/* Worker's PAS Base Fee */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Worker's PAS Base Fee (UGX):
                </label>
                <input
                  type="number"
                  step="0.01"
                  {...register('workers_pas_base_fee')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="0.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Fee for Worker's PAS registration (flat rate across levels)
                </p>
              </div>

              {/* Worker's PAS Per-Module Fee */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Worker's PAS Per-Module Fee (UGX):
                </label>
                <input
                  type="number"
                  step="0.01"
                  {...register('workers_pas_per_module_fee')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="0.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Fee per module for Worker's PAS registration (multiplied by modules enrolled)
                </p>
              </div>

              {/* Modular Fee - Single Module */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Modular Fee - Single Module (UGX):
                </label>
                <input
                  type="number"
                  step="0.01"
                  {...register('modular_fee_single_module')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="0.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Fee for Modular registration with 1 module
                </p>
              </div>

              {/* Modular Fee - Double Module */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Modular Fee - Double Module (UGX):
                </label>
                <input
                  type="number"
                  step="0.01"
                  {...register('modular_fee_double_module')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="0.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Fee for Modular registration with 2 modules
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={isLoading}
              disabled={isLoading}
            >
              <Save className="w-4 h-4 mr-2" />
              {level ? 'Save Changes' : 'Create Level'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LevelModal;
