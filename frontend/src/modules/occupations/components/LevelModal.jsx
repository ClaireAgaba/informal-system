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
        wp_level_name: level.wp_level_name || '',
        structure_type: level.structure_type,
        formal_fee: level.formal_fee,
        workers_pas_base_fee: level.workers_pas_base_fee,
        workers_pas_per_module_fee: level.workers_pas_per_module_fee,
        modular_fee_single_module: level.modular_fee_single_module,
        modular_fee_double_module: level.modular_fee_double_module,
        award: level.award || '',
        contact_hours: level.contact_hours || '',
        level_description: level.level_description || '',
        competence_description: level.competence_description || '',
      });
    } else {
      reset({
        level_name: '',
        wp_level_name: '',
        structure_type: 'modules',
        formal_fee: '0.00',
        workers_pas_base_fee: '0.00',
        workers_pas_per_module_fee: '0.00',
        modular_fee_single_module: '0.00',
        modular_fee_double_module: '0.00',
        award: '',
        contact_hours: '',
        level_description: '',
        competence_description: '',
      });
    }
  }, [level, reset]);

  if (!isOpen) return null;

  const handleFormSubmit = (data) => {
    // Normalize optional fields so empty strings don't fail backend validation.
    // award and contact_hours are optional (N/A for Worker's PAS levels).
    const cleaned = {
      ...data,
      wp_level_name: data.wp_level_name?.trim() || null,
      award: data.award?.trim() ? data.award.trim() : null,
      contact_hours:
        data.contact_hours === '' || data.contact_hours === null || data.contact_hours === undefined
          ? null
          : parseInt(data.contact_hours, 10) || null,
      level_description: data.level_description?.trim() ? data.level_description.trim() : '',
      competence_description: data.competence_description?.trim() ? data.competence_description.trim() : '',
    };
    onSubmit(cleaned);
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

          {/* Award & Duration */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-purple-900 mb-3">Award & Duration <span className="text-xs font-normal text-purple-700">(optional)</span></h3>
            <p className="text-xs text-purple-700 mb-4">
              Award title and contact hours for this level (used on transcripts). Leave blank for Worker's PAS — N/A.
            </p>

            <div className="space-y-4">
              {/* Award */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Award: <span className="text-xs font-normal text-gray-500">(optional)</span>
                </label>
                <input
                  type="text"
                  {...register('award')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Certificate in Hair Dressing Level 1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Award/Certificate title for this level (used on transcripts)
                </p>
              </div>

              {/* Contact Hours */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Hours: <span className="text-xs font-normal text-gray-500">(optional)</span>
                </label>
                <input
                  type="number"
                  {...register('contact_hours')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., 1200"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Total contact hours for this level
                </p>
              </div>
            </div>
          </div>

          {/* Worker's PAS Booklet Content */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-amber-900 mb-3">Worker's PAS Booklet Content</h3>
            <p className="text-xs text-amber-700 mb-4">
              Used only when generating Worker's PAS booklets. Leave blank for Formal occupations.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  WP Level Name <span className="text-xs font-normal text-gray-500">(for the book)</span>
                </label>
                <input
                  type="text"
                  {...register('wp_level_name')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Level 4"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Name shown on the booklet for this level. Controls the cover label and section titles. Falls back to Level Name if blank.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Level Description
                </label>
                <textarea
                  rows={4}
                  {...register('level_description')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Description of this competence level (appears on page 4 of the booklet)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Shown on the booklet's "Levels of Competence" page.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Competence (Section Intro)
                </label>
                <textarea
                  rows={3}
                  {...register('competence_description')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Short italic description shown on the sections list (page 6)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Shown next to "Section X / Competence Level X" on the sections list.
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
