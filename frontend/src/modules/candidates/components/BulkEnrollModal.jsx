import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { X, Users, Banknote, AlertCircle } from 'lucide-react';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import candidateApi from '../services/candidateApi';

const BulkEnrollModal = ({ isOpen, onClose, candidateIds, filters }) => {
  const queryClient = useQueryClient();
  
  // Form state
  const [formData, setFormData] = useState({
    assessment_series: '',
    occupation_level: '',
    modules: [],
    papers: [],
  });
  const [calculatedFee, setCalculatedFee] = useState(null);
  
  // Use the first selected candidate to get enrollment options
  // All selected candidates share the same occupation and registration category (enforced by filters)
  const firstCandidateId = candidateIds[0];
  
  // Fetch enrollment options from first candidate (same as individual enrollment)
  const { data: optionsData, isLoading } = useQuery({
    queryKey: ['enrollment-options', firstCandidateId],
    queryFn: () => candidateApi.getEnrollmentOptions(firstCandidateId),
    enabled: isOpen && !!firstCandidateId,
  });
  
  const options = optionsData?.data;
  const regCategory = options?.registration_category;
  
  // Auto-set occupation_level for modular (Level 1 is fixed)
  useEffect(() => {
    if (regCategory === 'modular' && options?.level && !formData.occupation_level) {
      setFormData(prev => ({ ...prev, occupation_level: options.level.id.toString() }));
    }
  }, [regCategory, options?.level, formData.occupation_level]);

  // Calculate fee when selections change (same logic as individual enrollment)
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
      const paperCount = formData.papers.length;
      if (paperCount > 0 && options.levels?.length > 0) {
        const level = options.levels[0];
        const perPaperFee = parseFloat(level.workers_pas_per_module_fee || 0);
        fee = perPaperFee * paperCount;
      }
    }

    // Multiply by number of candidates
    setCalculatedFee(fee * candidateIds.length);
  }, [formData, options, regCategory, candidateIds.length]);

  // Bulk enroll mutation
  const bulkEnrollMutation = useMutation({
    mutationFn: (data) => candidateApi.bulkEnroll(data),
    onSuccess: (response) => {
      toast.success(response.data?.message || `Successfully enrolled ${candidateIds.length} candidates`);
      queryClient.invalidateQueries(['candidates']);
      onClose();
      setFormData({
        assessment_series: '',
        occupation_level: '',
        modules: [],
        papers: [],
      });
    },
    onError: (error) => {
      toast.error(`Bulk enrollment failed: ${error.response?.data?.error || error.message}`);
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
      candidate_ids: candidateIds,
      assessment_series: parseInt(formData.assessment_series),
      modules: formData.modules.map(m => parseInt(m)),
      papers: formData.papers.map(p => parseInt(p)),
    };

    // Only include occupation_level for formal and modular
    if (regCategory !== 'workers_pas') {
      enrollmentData.occupation_level = parseInt(formData.occupation_level);
    }

    bulkEnrollMutation.mutate(enrollmentData);
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
      if (regCategory === 'workers_pas' && papers.length >= 4) {
        toast.warning('Maximum 4 papers allowed per assessment series');
        return;
      }
      papers.push(paperId);
    }

    setFormData({ ...formData, papers });
  };
  
  if (!isOpen) return null;
  
  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <Card className="w-full max-w-2xl">
          <Card.Content className="py-12 text-center text-gray-500">
            Loading enrollment options...
          </Card.Content>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <Card.Header className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold">Bulk Enroll Candidates</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </Card.Header>
        
        <Card.Content>
          {/* Show enrollment info */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              Enrolling <span className="font-semibold">{candidateIds.length}</span> candidates
            </p>
            {regCategory && (
              <p className="text-sm text-gray-600">
                Category: <span className="font-semibold">{regCategory}</span>
              </p>
            )}
            {options?.occupation && (
              <p className="text-sm text-gray-600">
                Occupation: <span className="font-semibold">{options.occupation.occ_name}</span>
              </p>
            )}
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
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
              <div>
                <div className="mb-4 p-3 bg-primary-50 border border-primary-200 rounded-lg">
                  <p className="text-sm font-medium text-primary-900">
                    🎓 Level: {options.level.level_name}
                  </p>
                </div>
                
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Modules (Min: 1, Max: 2) <span className="text-red-500">*</span>
                </label>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                  <p className="text-sm text-blue-800">
                    <AlertCircle className="w-4 h-4 inline mr-1" />
                    <strong>Fee per candidate:</strong> 1 Module = UGX {parseFloat(options.level.modular_fee_single_module).toLocaleString()} | 
                    2 Modules = UGX {parseFloat(options.level.modular_fee_double_module).toLocaleString()}
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    Modules selected: <strong>{formData.modules.length}</strong> / 2
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
            )}

            {/* Workers PAS: Show all levels with modules and papers */}
            {regCategory === 'workers_pas' && (
              <>
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

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Select Papers <span className="text-red-500">*</span>
                  </label>
                  <div className="space-y-4 max-h-60 overflow-y-auto">
                    {options?.levels?.map((level) => (
                      <div key={level.id} className="border border-gray-200 rounded-lg overflow-hidden">
                        <div className="bg-gradient-to-r from-primary-50 to-primary-100 px-4 py-2 border-b border-primary-200">
                          <h3 className="text-sm font-bold text-primary-900">🎓 {level.level_name}</h3>
                        </div>
                        {level.modules && level.modules.length > 0 && (
                          <div className="p-2 space-y-2">
                            {level.modules.map((module) => (
                              <div key={module.id} className="border border-gray-300 rounded-lg overflow-hidden">
                                <div className="bg-gray-50 px-3 py-1 border-b border-gray-200">
                                  <span className="text-xs font-semibold text-gray-900">
                                    📚 {module.module_code} - {module.module_name}
                                  </span>
                                </div>
                                {module.papers && module.papers.length > 0 && (
                                  <div className="bg-white p-1 space-y-1">
                                    {module.papers.map((paper) => (
                                      <label key={paper.id} className="flex items-center p-1 rounded hover:bg-gray-50 cursor-pointer text-xs">
                                        <input
                                          type="checkbox"
                                          checked={formData.papers.includes(paper.id)}
                                          onChange={() => handlePaperToggle(paper.id)}
                                          className="w-3 h-3 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                                        />
                                        <span className="ml-2 text-gray-700">
                                          <span className="font-medium">{paper.paper_code}</span> - {paper.paper_name}
                                        </span>
                                      </label>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
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
                    <span className="text-sm font-medium text-green-900">
                      Total Amount ({candidateIds.length} candidates)
                    </span>
                  </div>
                  <span className="text-lg font-bold text-green-900">
                    UGX {parseFloat(calculatedFee).toLocaleString()}
                  </span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={bulkEnrollMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={bulkEnrollMutation.isPending || calculatedFee === null}
              >
                {bulkEnrollMutation.isPending ? 'Enrolling...' : `Enroll ${candidateIds.length} Candidates`}
              </Button>
            </div>
          </form>
        </Card.Content>
      </Card>
    </div>
  );
};

export default BulkEnrollModal;
