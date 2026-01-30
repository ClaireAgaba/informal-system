import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Printer, Search } from 'lucide-react';
import apiClient from '../../../services/apiClient';
import marksheetsApi from '../api/marksheetsApi';

export default function PrintMarksheets() {
  const [formData, setFormData] = useState({
    assessment_series: '',
    registration_category: '',
    occupation: '',
    level: '',
    module: '',
    assessment_center: '',
  });

  const [selectedModule, setSelectedModule] = useState(null);
  const [moduleSearch, setModuleSearch] = useState('');
  const [occupationSearch, setOccupationSearch] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch assessment series
  const { data: seriesData } = useQuery({
    queryKey: ['assessment-series'],
    queryFn: async () => {
      const response = await apiClient.get('/assessment-series/series/');
      return response.data.results || response.data;
    },
  });

  // Fetch occupations
  const { data: occupationsData } = useQuery({
    queryKey: ['occupations-all'],
    queryFn: async () => {
      const response = await apiClient.get('/occupations/occupations/', { params: { page_size: 1000 } });
      return response.data.results || response.data;
    },
  });

  // Fetch levels
  const { data: levelsData } = useQuery({
    queryKey: ['occupation-levels', formData.occupation],
    queryFn: async () => {
      const response = await apiClient.get(`/occupations/levels/by_occupation/?occupation_id=${formData.occupation}`);
      return response.data.results || response.data;
    },
    enabled: !!formData.occupation && (formData.registration_category === 'formal' || formData.registration_category === 'workers_pas'),
  });

  // Fetch modules for modular
  const { data: modulesData } = useQuery({
    queryKey: ['occupation-modules', formData.occupation],
    queryFn: async () => {
      const response = await apiClient.get(`/occupations/modules/by-occupation/?occupation=${formData.occupation}`);
      return response.data.results || response.data;
    },
    enabled: !!formData.occupation && formData.registration_category === 'modular',
  });

  // Fetch assessment centers
  const { data: centersData } = useQuery({
    queryKey: ['assessment-centers'],
    queryFn: async () => {
      const response = await apiClient.get('/assessment-centers/centers/', { params: { page_size: 1000 } });
      return response.data.results || response.data;
    },
  });

  const series = Array.isArray(seriesData) ? seriesData : [];
  const allOccupations = Array.isArray(occupationsData) ? occupationsData : [];
  const levels = Array.isArray(levelsData) ? levelsData : [];
  const modules = Array.isArray(modulesData) ? modulesData : [];
  const centers = Array.isArray(centersData) ? centersData : [];

  const selectedLevel = levels.find(l => l.id === parseInt(formData.level));
  const structureType = selectedLevel?.structure_type;

  const occupations = formData.registration_category
    ? allOccupations.filter(occ => {
      if (formData.registration_category === 'modular') {
        return occ.has_modular === true;
      }
      return occ.occ_category === formData.registration_category;
    })
    : allOccupations;

  const filteredModules = modules.filter(module =>
    module.module_name.toLowerCase().includes(moduleSearch.toLowerCase()) ||
    module.module_code.toLowerCase().includes(moduleSearch.toLowerCase())
  );

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (name === 'registration_category') {
      setFormData(prev => ({ ...prev, occupation: '', level: '', module: '' }));
      setSelectedModule(null);
    }

    if (name === 'occupation') {
      setFormData(prev => ({ ...prev, level: '', module: '' }));
      setSelectedModule(null);
    }

    if (name === 'level') {
      setFormData(prev => ({ ...prev, module: '' }));
      setSelectedModule(null);
    }
  };

  const handleModuleSelect = (module) => {
    setSelectedModule(module);
    setFormData(prev => ({ ...prev, module: module.id }));
  };

  const handleGenerate = async () => {
    setError('');
    setSuccess('');

    if (!formData.assessment_series || !formData.registration_category || !formData.occupation) {
      setError('Please fill in all required fields');
      return;
    }

    if (formData.registration_category === 'modular' && !formData.module) {
      setError('Please select a module');
      return;
    }

    if ((formData.registration_category === 'formal' || formData.registration_category === 'workers_pas') && !formData.level) {
      setError('Please select a level');
      return;
    }

    setIsGenerating(true);

    try {
      let response;
      let filename;

      if (formData.registration_category === 'modular') {
        response = await marksheetsApi.printModularMarksheet({
          assessment_series: formData.assessment_series,
          occupation: formData.occupation,
          module: formData.module,
          assessment_center: formData.assessment_center || null,
        });
        filename = `Marksheet_Modular_${selectedModule?.module_code}.pdf`;
      } else if (formData.registration_category === 'formal') {
        response = await marksheetsApi.printFormalMarksheet({
          assessment_series: formData.assessment_series,
          occupation: formData.occupation,
          level: formData.level,
          structure_type: structureType,
          assessment_center: formData.assessment_center || null,
        });
        filename = `Marksheet_Formal_${selectedLevel?.level_name}.pdf`;
      } else if (formData.registration_category === 'workers_pas') {
        response = await marksheetsApi.printWorkersPasMarksheet({
          assessment_series: formData.assessment_series,
          occupation: formData.occupation,
          level: formData.level,
          assessment_center: formData.assessment_center || null,
        });
        filename = `Marksheet_WorkersPAS_${selectedLevel?.level_name}.pdf`;
      }

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      window.open(url, '_blank');

      // Clean up the URL object after a short delay to ensure it loaded
      setTimeout(() => window.URL.revokeObjectURL(url), 100);

      setSuccess('Marksheet generated successfully!');
    } catch (err) {
      if (err.response?.status === 404) {
        setError('No enrolled candidates found for the selected parameters');
      } else {
        setError(err.response?.data?.error || 'Failed to print marksheet');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Printer className="h-7 w-7 text-purple-600" />
          Print Marksheets
        </h1>
        <p className="text-gray-600 mt-1">Generate PDF marksheets for printing</p>
      </div>

      {/* Render Error and Success messages */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          {success}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* Form Fields - Reused from GenerateMarksheets but cleaned up */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series <span className="text-red-500">*</span>
            </label>
            <select
              name="assessment_series"
              value={formData.assessment_series}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select Series</option>
              {series.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Registration Category <span className="text-red-500">*</span>
            </label>
            <select
              name="registration_category"
              value={formData.registration_category}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select Category</option>
              <option value="modular">Modular</option>
              <option value="formal">Formal</option>
              <option value="workers_pas">Worker's PAS</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Occupation <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder={formData.registration_category ? 'Type to search occupation...' : 'Select Category First'}
                value={occupationSearch}
                onChange={(e) => setOccupationSearch(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={!formData.registration_category}
              />
              <Search className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
            {formData.registration_category && occupationSearch && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {occupations
                  .filter(occ =>
                    occ.occ_name?.toLowerCase().includes(occupationSearch.toLowerCase()) ||
                    occ.occ_code?.toLowerCase().includes(occupationSearch.toLowerCase())
                  )
                  .map(occ => (
                    <div
                      key={occ.id}
                      onClick={() => {
                        setFormData(prev => ({ ...prev, occupation: occ.id }));
                        setOccupationSearch(`${occ.occ_name} (${occ.occ_code})`);
                      }}
                      className="px-3 py-2 hover:bg-blue-50 cursor-pointer"
                    >
                      {occ.occ_name} ({occ.occ_code})
                    </div>
                  ))}
                {occupations.filter(occ =>
                  occ.occ_name?.toLowerCase().includes(occupationSearch.toLowerCase()) ||
                  occ.occ_code?.toLowerCase().includes(occupationSearch.toLowerCase())
                ).length === 0 && (
                    <div className="px-3 py-2 text-gray-500">No occupations found</div>
                  )}
              </div>
            )}
          </div>

          {(formData.registration_category === 'formal' || formData.registration_category === 'workers_pas') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Level <span className="text-red-500">*</span>
              </label>
              <select
                name="level"
                value={formData.level}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={!formData.occupation}
              >
                <option value="">
                  {formData.occupation ? 'Select Level' : 'Select Occupation First'}
                </option>
                {levels.map(level => (
                  <option key={level.id} value={level.id}>
                    {level.level_name} ({level.structure_type === 'modules' ? 'Module-Based' : 'Paper-Based'})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {formData.registration_category === 'modular' && formData.occupation && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Module <span className="text-red-500">*</span>
            </label>
            <div className="border border-gray-300 rounded-lg p-4">
              <div className="mb-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search modules..."
                    value={moduleSearch}
                    onChange={(e) => setModuleSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="max-h-64 overflow-y-auto space-y-2">
                {filteredModules.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No modules found</p>
                ) : (
                  filteredModules.map(module => (
                    <label
                      key={module.id}
                      className="flex items-center p-3 hover:bg-gray-50 rounded-lg cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="module"
                        checked={selectedModule?.id === module.id}
                        onChange={() => handleModuleSelect(module)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <span className="ml-3 text-sm text-gray-900">
                        {module.module_name} ({module.module_code})
                      </span>
                    </label>
                  ))
                )}
              </div>

              {selectedModule && (
                <div className="mt-3 pt-3 border-t border-gray-200 text-sm text-gray-600">
                  <span className="font-medium">Selected: {selectedModule.module_name}</span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Assessment Center (optional)
          </label>
          <select
            name="assessment_center"
            value={formData.assessment_center}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">-- All Centers --</option>
            {centers.map(center => (
              <option key={center.id} value={center.id}>
                {center.center_name} ({center.center_number})
              </option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-3">
          <button
            onClick={() => {
              setFormData({
                assessment_series: '',
                registration_category: '',
                occupation: '',
                level: '',
                module: '',
                assessment_center: '',
              });
              setSelectedModule(null);
              setError('');
              setSuccess('');
            }}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={
              isGenerating ||
              (formData.registration_category === 'modular' && !formData.module) ||
              (formData.registration_category === 'formal' && !formData.level) ||
              (formData.registration_category === 'workers_pas' && !formData.level)
            }
            className="flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Printer className="h-4 w-4" />
            {isGenerating ? 'Generating PDF...' : 'Print Marksheet'}
          </button>
        </div>
      </div>
    </div>
  );
}
