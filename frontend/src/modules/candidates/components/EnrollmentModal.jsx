import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { X, Banknote, AlertCircle } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import Button from '@shared/components/Button';

const EnrollmentModal = ({ candidate, onClose }) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    assessment_series: '',
    occupation_level: '',
    modules: [],
    papers: [],
  });
  const [calculatedFee, setCalculatedFee] = useState(null);

  // Fetch enrollment options
  const { data: optionsData, isLoading } = useQuery({
    queryKey: ['enrollment-options', candidate.id],
    queryFn: () => candidateApi.getEnrollmentOptions(candidate.id),
    enabled: !!candidate.id,
  });

  const options = optionsData?.data;
  const regCategory = options?.registration_category;

  // Calculate fee when selections change
  useEffect(() => {
    if (!options) {
      setCalculatedFee(null);
      return;
    }

    let fee = 0;

    if (regCategory === 'formal') {
      if (!formData.occupation_level) {
        setCalculatedFee(null);
        return;
      }
      const level = options.levels?.find(l => l.id === parseInt(formData.occupation_level));
      fee = level?.formal_fee || 0;
    } else if (regCategory === 'modular') {
      const moduleCount = formData.modules.length;
      if (moduleCount === 1) {
        fee = parseFloat(options.level?.modular_fee_single_module || 0);
      } else if (moduleCount === 2) {
        fee = parseFloat(options.level?.modular_fee_double_module || 0);
      }
    } else if (regCategory === 'workers_pas') {
      // For Workers PAS: fee per paper selected
      const paperCount = formData.papers.length;
      
      if (paperCount > 0 && options.levels?.length > 0) {
        // Use per-module fee as per-paper fee (75k per paper)
        const level = options.levels[0];
        const perPaperFee = parseFloat(level.workers_pas_per_module_fee || 0);
        fee = perPaperFee * paperCount;
      }
    }

    setCalculatedFee(fee);
  }, [formData, options, regCategory]);

  // Enroll mutation
  const enrollMutation = useMutation({
    mutationFn: (data) => candidateApi.enroll(candidate.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate-enrollments', candidate.id]);
      toast.success('Candidate enrolled successfully!');
      onClose();
    },
    onError: (error) => {
      toast.error(`Enrollment failed: ${error.response?.data?.error || error.message}`);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validation
    if (!formData.assessment_series) {
      toast.error('Please select assessment series');
      return;
    }

    // For formal and modular, level is required
    if ((regCategory === 'formal' || regCategory === 'modular') && !formData.occupation_level) {
      toast.error('Please select a level');
      return;
    }

    if (regCategory === 'modular' && (formData.modules.length < 1 || formData.modules.length > 2)) {
      toast.error('Modular registration requires 1 or 2 modules');
      return;
    }

    if (regCategory === 'workers_pas') {
      if (formData.papers.length < 2) {
        toast.error("Worker's PAS registration requires minimum 2 papers per assessment series");
        return;
      }
      if (formData.papers.length > 4) {
        toast.error("Worker's PAS registration allows maximum 4 papers per assessment series");
        return;
      }
    }

    const enrollmentData = {
      assessment_series: parseInt(formData.assessment_series),
      modules: formData.modules.map(m => parseInt(m)),
      papers: formData.papers.map(p => parseInt(p)),
    };

    // Only include occupation_level for formal and modular
    if (regCategory !== 'workers_pas') {
      enrollmentData.occupation_level = parseInt(formData.occupation_level);
    }

    enrollMutation.mutate(enrollmentData);
  };

  const handleModuleToggle = (moduleId) => {
    const modules = [...formData.modules];
    const index = modules.indexOf(moduleId);

    if (index > -1) {
      modules.splice(index, 1);
    } else {
      if (regCategory === 'modular' && modules.length >= 2) {
        toast.warning('You can only select up to 2 modules for modular registration');
        return;
      }
      modules.push(moduleId);
    }

    setFormData({ ...formData, modules });
  };

  const handlePaperToggle = (paperId) => {
    const papers = [...formData.papers];
    const index = papers.indexOf(paperId);

    if (index > -1) {
      papers.splice(index, 1);
    } else {
      // For Workers PAS, check maximum limit
      if (regCategory === 'workers_pas' && papers.length >= 4) {
        toast.warning('Maximum 4 papers allowed per assessment series');
        return;
      }
      papers.push(paperId);
    }

    setFormData({ ...formData, papers });
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p>Loading enrollment options...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Enroll Candidate</h2>
            <p className="text-sm text-gray-600 mt-1">
              {candidate.full_name} - {options?.occupation?.occ_name}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Assessment Series */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.assessment_series}
              onChange={(e) => setFormData({ ...formData, assessment_series: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            >
              <option value="">Select assessment series</option>
              {options?.assessment_series?.map((series) => (
                <option key={series.id} value={series.id}>
                  {series.name}
                </option>
              ))}
            </select>
          </div>

          {/* Formal: Show levels */}
          {regCategory === 'formal' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Level <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.occupation_level}
                onChange={(e) => setFormData({ ...formData, occupation_level: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="">Select level</option>
                {options?.levels?.map((level) => (
                  <option key={level.id} value={level.id}>
                    {level.level_name} - UGX {parseFloat(level.formal_fee).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Modular: Show Level 1 modules */}
          {regCategory === 'modular' && options?.level && (
            <>
              <input
                type="hidden"
                value={options.level.id}
                onChange={() => setFormData({ ...formData, occupation_level: options.level.id.toString() })}
              />
              {/* Auto-set level */}
              {!formData.occupation_level && setFormData({ ...formData, occupation_level: options.level.id.toString() })}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Modules (Min: 1, Max: 2) <span className="text-red-500">*</span>
                </label>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                  <p className="text-sm text-blue-800">
                    <AlertCircle className="w-4 h-4 inline mr-1" />
                    1 Module: UGX {parseFloat(options.level.modular_fee_single_module).toLocaleString()} | 
                    2 Modules: UGX {parseFloat(options.level.modular_fee_double_module).toLocaleString()}
                  </p>
                </div>
                <div className="space-y-2">
                  {options?.modules?.map((module) => (
                    <label key={module.id} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.modules.includes(module.id)}
                        onChange={() => handleModuleToggle(module.id)}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <span className="ml-3 text-sm">
                        <span className="font-medium">{module.module_code}</span> - {module.module_name}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Workers PAS: Show all levels with modules and papers */}
          {regCategory === 'workers_pas' && (
            <>
              {/* Instructions */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  Paper Selection Instructions
                </h4>
                <div className="text-sm text-blue-800 space-y-1">
                  <p><strong>Worker's PAS/Informal candidates</strong> can select papers from any level and module.</p>
                  <ul className="list-disc list-inside ml-2 mt-2 space-y-1">
                    <li><strong>Minimum:</strong> 2 papers per assessment series</li>
                    <li><strong>Maximum:</strong> 4 papers per assessment series</li>
                    <li><strong>Rule:</strong> Only one paper per module</li>
                  </ul>
                  <p className="mt-2 text-xs">
                    Papers selected: <strong>{formData.papers.length} / 4</strong>
                  </p>
                </div>
              </div>

              {/* Show all levels with their modules and papers */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Select Papers <span className="text-red-500">*</span>
                </label>
                <div className="space-y-4">
                  {options?.levels?.map((level) => (
                    <div key={level.id} className="border border-gray-200 rounded-lg overflow-hidden">
                      {/* Level Header */}
                      <div className="bg-gradient-to-r from-primary-50 to-primary-100 px-4 py-3 border-b border-primary-200">
                        <h3 className="text-sm font-bold text-primary-900 flex items-center">
                          🎓 {level.level_name}
                        </h3>
                      </div>
                      
                      {/* Modules in this level */}
                      {level.modules && level.modules.length > 0 ? (
                        <div className="p-3 space-y-3">
                          {level.modules.map((module) => (
                            <div key={module.id} className="border border-gray-300 rounded-lg overflow-hidden">
                              {/* Module Header */}
                              <div className="bg-gray-50 px-3 py-2 border-b border-gray-200">
                                <span className="text-sm font-semibold text-gray-900">
                                  📚 {module.module_code} - {module.module_name}
                                </span>
                              </div>
                              
                              {/* Papers in this module */}
                              {module.papers && module.papers.length > 0 ? (
                                <div className="bg-white p-2 space-y-1">
                                  {module.papers.map((paper) => (
                                    <label key={paper.id} className="flex items-center p-2 rounded hover:bg-gray-50 cursor-pointer">
                                      <input
                                        type="checkbox"
                                        checked={formData.papers.includes(paper.id)}
                                        onChange={() => handlePaperToggle(paper.id)}
                                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                                      />
                                      <span className="ml-3 text-sm text-gray-700">
                                        <span className="font-medium">{paper.paper_code}</span> - {paper.paper_name}
                                        <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">
                                          {paper.paper_type_display || paper.paper_type}
                                        </span>
                                      </span>
                                    </label>
                                  ))}
                                </div>
                              ) : (
                                <div className="p-3 text-sm text-gray-500 italic">
                                  No papers defined for this module
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-4 text-sm text-gray-500 italic">
                          No modules defined for this level
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Calculated Fee */}
          {calculatedFee !== null && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Banknote className="w-5 h-5 text-green-600 mr-2" />
                  <span className="text-sm font-medium text-green-900">Total Amount</span>
                </div>
                <span className="text-lg font-bold text-green-900">
                  UGX {calculatedFee.toLocaleString()}
                </span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={enrollMutation.isPending}
              disabled={enrollMutation.isPending || calculatedFee === null}
            >
              Enroll Candidate
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EnrollmentModal;
