import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Save, Send, Upload } from 'lucide-react';
import { toast } from 'sonner';
import candidateApi from '../services/candidateApi';
import occupationApi from '@modules/occupations/services/occupationApi';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const CandidateCreate = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('personal-info');
  const [savedDraftId, setSavedDraftId] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm({
    defaultValues: {
      full_name: '',
      date_of_birth: '',
      gender: '',
      nationality: 'Uganda',
      is_refugee: false,
      refugee_number: '',
      contact: '',
      district: '',
      village: '',
      has_disability: false,
      nature_of_disability: '',
      disability_specification: '',
      assessment_center: '',
      assessment_center_branch: '',
      entry_year: new Date().getFullYear().toString(),
      intake: '',
      registration_category: '',
      occupation: '',
      preferred_assessment_language: 'English',
      start_date: '',
      finish_date: '',
      assessment_date: '',
      modular_module_count: '',
      enrollment_level: '',
      status: 'active',
    },
  });

  // Fetch districts
  const { data: districtsData } = useQuery({
    queryKey: ['districts'],
    queryFn: async () => {
      const response = await fetch('/api/configurations/districts/');
      if (!response.ok) throw new Error('Failed to fetch districts');
      return response.json();
    },
  });

  // Watch district selection
  const selectedDistrict = watch('district');
  
  // Fetch villages filtered by district
  const { data: villagesData } = useQuery({
    queryKey: ['villages', selectedDistrict],
    queryFn: async () => {
      const url = selectedDistrict 
        ? `/api/configurations/villages/?district=${selectedDistrict}`
        : '/api/configurations/villages/';
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch villages');
      return response.json();
    },
    enabled: !!selectedDistrict, // Only fetch when district is selected
  });

  // Fetch disabilities
  const { data: disabilitiesData } = useQuery({
    queryKey: ['disabilities'],
    queryFn: async () => {
      const response = await fetch('/api/configurations/nature-of-disabilities/');
      if (!response.ok) throw new Error('Failed to fetch disabilities');
      return response.json();
    },
  });

  // Fetch occupations
  const { data: occupationsData } = useQuery({
    queryKey: ['occupations'],
    queryFn: () => occupationApi.getAll(),
  });

  // Fetch assessment centers
  const { data: centersData } = useQuery({
    queryKey: ['assessment-centers'],
    queryFn: () => assessmentCenterApi.getAll(),
  });

  // Fetch branches for selected center
  const selectedCenter = watch('assessment_center');
  const { data: branchesData } = useQuery({
    queryKey: ['center-branches', selectedCenter],
    queryFn: () => assessmentCenterApi.branches.getByCenter(selectedCenter),
    enabled: !!selectedCenter,
  });

  const districts = districtsData?.results || [];
  const villages = villagesData?.results || [];
  const disabilities = disabilitiesData?.results || [];
  const allOccupations = occupationsData?.data?.results || [];
  const centers = centersData?.data?.results || [];
  const branches = branchesData?.data?.results || [];

  const isRefugee = watch('is_refugee');
  const hasDisability = watch('has_disability');
  const registrationCategory = watch('registration_category');

  // Reset village when district changes
  useEffect(() => {
    setValue('village', '');
  }, [selectedDistrict, setValue]);

  // Filter occupations based on registration category
  const occupations = allOccupations.filter(occ => {
    if (!registrationCategory) return true;
    if (registrationCategory === 'workers_pas') {
      return occ.occ_category === 'workers_pas';
    } else {
      // For 'formal' and 'modular', show only 'formal' occupations
      return occ.occ_category === 'formal';
    }
  });

  // Photo upload handler
  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
      // TODO: Upload photo via API when implementing file upload
    }
  };

  // Create/Update mutation (for draft saving)
  const saveDraftMutation = useMutation({
    mutationFn: (data) => {
      if (savedDraftId) {
        return candidateApi.update(savedDraftId, data);
      } else {
        return candidateApi.create(data);
      }
    },
    onSuccess: (response) => {
      console.log('Save draft response:', response);
      const candidateId = response?.data?.id || response?.id;
      if (!savedDraftId && candidateId) {
        setSavedDraftId(candidateId);
      }
      queryClient.invalidateQueries(['candidates']);
      toast.success('Draft saved successfully!');
    },
    onError: (error) => {
      console.error('Save draft error:', error);
      console.error('Error response:', error.response);
      const errorMsg = error.response?.data?.error ||
                       error.response?.data?.detail || 
                       JSON.stringify(error.response?.data) || 
                       error.message;
      toast.error(`Failed to save draft: ${errorMsg}`);
    },
  });

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async (data) => {
      console.log('Starting submit process...');
      // First save as draft if not already saved
      let candidateId = savedDraftId;
      
      if (!candidateId) {
        console.log('Creating new candidate...');
        const saveResponse = await candidateApi.create(data);
        console.log('Create response:', saveResponse);
        candidateId = saveResponse?.data?.id || saveResponse?.id;
        setSavedDraftId(candidateId);
      } else {
        console.log('Updating existing candidate:', candidateId);
        await candidateApi.update(candidateId, data);
      }
      
      // Then submit
      console.log('Submitting candidate:', candidateId);
      const submitResponse = await candidateApi.submit(candidateId);
      console.log('Submit response:', submitResponse);
      return submitResponse;
    },
    onSuccess: (response) => {
      console.log('Submit success response:', response);
      queryClient.invalidateQueries(['candidates']);
      const regNumber = response?.data?.registration_number || response?.registration_number || 'N/A';
      toast.success(`Candidate submitted successfully! Registration Number: ${regNumber}`);
      navigate('/candidates');
    },
    onError: (error) => {
      console.error('Submit error:', error);
      console.error('Error response:', error.response);
      const errorMsg = error.response?.data?.error || 
                       error.response?.data?.detail || 
                       JSON.stringify(error.response?.data) || 
                       error.message;
      toast.error(`Failed to submit candidate: ${errorMsg}`);
    },
  });

  const cleanFormData = (data) => {
    const cleanedData = { ...data };
    const fkFields = ['district', 'village', 'nature_of_disability', 
                      'assessment_center', 'assessment_center_branch', 'occupation'];
    
    fkFields.forEach(field => {
      if (cleanedData[field] === '' || cleanedData[field] === 'None') {
        cleanedData[field] = null;
      } else if (cleanedData[field]) {
        cleanedData[field] = parseInt(cleanedData[field], 10);
      }
    });
    
    cleanedData.is_refugee = cleanedData.is_refugee === true;
    cleanedData.has_disability = cleanedData.has_disability === true;
    
    const textFields = ['disability_specification', 'enrollment_level', 'refugee_number', 
                        'preferred_assessment_language'];
    
    Object.keys(cleanedData).forEach(key => {
      if (cleanedData[key] === '' && typeof cleanedData[key] !== 'boolean') {
        if (!textFields.includes(key)) {
          cleanedData[key] = null;
        }
      }
    });
    
    return cleanedData;
  };

  const onSaveDraft = (data) => {
    const cleanedData = cleanFormData(data);
    console.log('Saving draft:', cleanedData);
    saveDraftMutation.mutate(cleanedData);
  };

  const onSubmit = (data) => {
    const cleanedData = cleanFormData(data);
    console.log('Submitting candidate:', cleanedData);
    submitMutation.mutate(cleanedData);
  };

  const tabs = [
    { id: 'personal-info', label: 'Personal Information' },
    { id: 'location', label: 'Location Information' },
    { id: 'special', label: 'Special Considerations' },
    { id: 'enrollment', label: 'Enrollment Details' },
    { id: 'documents', label: 'Documents' },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/candidates')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to List
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Candidate</h1>
            <p className="text-gray-600 mt-1">
              {savedDraftId ? '✓ Draft saved - You can continue editing' : 'Fill in candidate details'}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Form */}
      <form>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form Content */}
          <div className="lg:col-span-2">
            <Card>
              <Card.Content className="space-y-6">
                {/* Personal Information Tab */}
                {activeTab === 'personal-info' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Personal Information</h3>
                    
                    {/* Passport Photo */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Passport Photo
                      </label>
                      <div className="flex items-center space-x-4">
                        {photoPreview ? (
                          <img
                            src={photoPreview}
                            alt="Preview"
                            className="w-24 h-24 rounded-lg object-cover border-2 border-gray-300"
                          />
                        ) : (
                          <div className="w-24 h-24 rounded-lg bg-gray-100 flex items-center justify-center border-2 border-dashed border-gray-300">
                            <Upload className="w-8 h-8 text-gray-400" />
                          </div>
                        )}
                        <div>
                          <input
                            type="file"
                            id="photo-upload"
                            accept="image/*"
                            onChange={handlePhotoChange}
                            className="hidden"
                          />
                          <label
                            htmlFor="photo-upload"
                            className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                          >
                            <Upload className="w-4 h-4 mr-2" />
                            Upload Photo
                          </label>
                          <p className="mt-1 text-xs text-gray-500">
                            JPG, PNG or GIF (max. 5MB)
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Full Name */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Full Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        {...register('full_name', { required: 'Full name is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        placeholder="Enter full name"
                      />
                      {errors.full_name && (
                        <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
                      )}
                    </div>

                    {/* Date of Birth */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Date of Birth <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        {...register('date_of_birth', { required: 'Date of birth is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                      {errors.date_of_birth && (
                        <p className="mt-1 text-sm text-red-600">{errors.date_of_birth.message}</p>
                      )}
                    </div>

                    {/* Gender */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Gender <span className="text-red-500">*</span>
                      </label>
                      <select
                        {...register('gender', { required: 'Gender is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select gender</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                      </select>
                      {errors.gender && (
                        <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>
                      )}
                    </div>

                    {/* Nationality */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nationality <span className="text-red-500">*</span>
                      </label>
                      <select
                        {...register('nationality', { required: 'Nationality is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="Uganda">Uganda</option>
                        <option value="Kenya">Kenya</option>
                        <option value="Tanzania">Tanzania</option>
                        <option value="Rwanda">Rwanda</option>
                        <option value="Burundi">Burundi</option>
                        <option value="South Sudan">South Sudan</option>
                        <option value="Other">Other</option>
                      </select>
                      {errors.nationality && (
                        <p className="mt-1 text-sm text-red-600">{errors.nationality.message}</p>
                      )}
                    </div>

                    {/* Contact */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Contact Number <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        {...register('contact', { required: 'Contact number is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        placeholder="e.g., 0700123456"
                      />
                      {errors.contact && (
                        <p className="mt-1 text-sm text-red-600">{errors.contact.message}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Location Information Tab */}
                {activeTab === 'location' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Location Information</h3>
                    
                    {/* District */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        District <span className="text-red-500">*</span>
                      </label>
                      <select
                        {...register('district', { required: 'District is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select district</option>
                        {districts.map((district) => (
                          <option key={district.id} value={district.id}>
                            {district.name}
                          </option>
                        ))}
                      </select>
                      {errors.district && (
                        <p className="mt-1 text-sm text-red-600">{errors.district.message}</p>
                      )}
                    </div>

                    {/* Village */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Village
                      </label>
                      <select
                        {...register('village')}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select village (optional)</option>
                        {villages.map((village) => (
                          <option key={village.id} value={village.id}>
                            {village.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {/* Special Considerations Tab */}
                {activeTab === 'special' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Special Considerations</h3>
                    
                    {/* Is Refugee */}
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('is_refugee')}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <label className="ml-2 text-sm text-gray-700">
                        Is Refugee?
                      </label>
                    </div>

                    {/* Refugee Number */}
                    {isRefugee && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Refugee Number
                        </label>
                        <input
                          type="text"
                          {...register('refugee_number')}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          placeholder="Enter refugee identification number"
                        />
                      </div>
                    )}

                    {/* Has Disability */}
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('has_disability')}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <label className="ml-2 text-sm text-gray-700">
                        Has Disability?
                      </label>
                    </div>

                    {/* Nature of Disability */}
                    {hasDisability && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Nature of Disability
                          </label>
                          <select
                            {...register('nature_of_disability')}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <option value="">Select disability type</option>
                            {disabilities.map((disability) => (
                              <option key={disability.id} value={disability.id}>
                                {disability.name}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Disability Specification
                          </label>
                          <textarea
                            {...register('disability_specification')}
                            rows={3}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            placeholder="Provide specific details about the disability"
                          />
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Enrollment Details Tab */}
                {activeTab === 'enrollment' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Enrollment Details</h3>
                    
                    {/* Assessment Center */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Assessment Center <span className="text-red-500">*</span>
                      </label>
                      <select
                        {...register('assessment_center', { required: 'Assessment center is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select assessment center</option>
                        {centers.map((center) => (
                          <option key={center.id} value={center.id}>
                            {center.center_number} - {center.center_name}
                          </option>
                        ))}
                      </select>
                      {errors.assessment_center && (
                        <p className="mt-1 text-sm text-red-600">{errors.assessment_center.message}</p>
                      )}
                    </div>

                    {/* Center Branch */}
                    {selectedCenter && branches.length > 0 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Center Branch
                        </label>
                        <select
                          {...register('assessment_center_branch')}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">Select branch (optional)</option>
                          {branches.map((branch) => (
                            <option key={branch.id} value={branch.id}>
                              {branch.branch_code} - {branch.branch_name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {/* Entry Year */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Entry Year <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        {...register('entry_year', { required: 'Entry year is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        placeholder="e.g., 2025"
                      />
                      {errors.entry_year && (
                        <p className="mt-1 text-sm text-red-600">{errors.entry_year.message}</p>
                      )}
                    </div>

                    {/* Intake */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Intake <span className="text-red-500">*</span>
                      </label>
                      <select
                        {...register('intake', { required: 'Intake is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select intake</option>
                        <option value="M">March</option>
                        <option value="A">August</option>
                      </select>
                      {errors.intake && (
                        <p className="mt-1 text-sm text-red-600">{errors.intake.message}</p>
                      )}
                    </div>

                    {/* Registration Category */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Registration Category <span className="text-red-500">*</span>
                      </label>
                      <select
                        {...register('registration_category', { required: 'Registration category is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select category</option>
                        <option value="modular">Modular</option>
                        <option value="formal">Formal</option>
                        <option value="workers_pas">Worker's PAS</option>
                      </select>
                      {errors.registration_category && (
                        <p className="mt-1 text-sm text-red-600">{errors.registration_category.message}</p>
                      )}
                    </div>

                    {/* Occupation */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Occupation <span className="text-red-500">*</span>
                      </label>
                      <select
                        {...register('occupation', { required: 'Occupation is required' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select occupation</option>
                        {occupations.map((occupation) => (
                          <option key={occupation.id} value={occupation.id}>
                            {occupation.occ_code} - {occupation.occ_name}
                          </option>
                        ))}
                      </select>
                      {errors.occupation && (
                        <p className="mt-1 text-sm text-red-600">{errors.occupation.message}</p>
                      )}
                    </div>

                    {/* Modular Module Count */}
                    {registrationCategory === 'modular' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Module Count
                        </label>
                        <select
                          {...register('modular_module_count')}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">Select module count</option>
                          <option value="1">1 Module</option>
                          <option value="2">2 Modules</option>
                        </select>
                      </div>
                    )}

                    {/* Preferred Assessment Language */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Preferred Assessment Language
                      </label>
                      <input
                        type="text"
                        {...register('preferred_assessment_language')}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        placeholder="e.g., English"
                      />
                    </div>
                  </div>
                )}

                {/* Documents Tab */}
                {activeTab === 'documents' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Documents</h3>
                    <p className="text-sm text-gray-600">Upload required documents (Note: Files will be uploaded when you save)</p>
                    
                    {/* Identification Document */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Identification Document
                      </label>
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        National ID, Birth Certificate, or other identification (PNG, JPG, PDF max 10MB)
                      </p>
                    </div>

                    {/* Qualification Document */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Qualification Document
                      </label>
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        Relevant qualifications for Full Occupation candidates (PNG, JPG, PDF max 10MB)
                      </p>
                    </div>
                  </div>
                )}
              </Card.Content>
            </Card>
          </div>

          {/* Actions Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
              </Card.Header>
              <Card.Content className="space-y-3">
                <Button
                  type="button"
                  variant="primary"
                  size="md"
                  className="w-full"
                  onClick={handleSubmit(onSubmit)}
                  loading={submitMutation.isPending}
                  disabled={submitMutation.isPending || saveDraftMutation.isPending}
                >
                  <Send className="w-4 h-4 mr-2" />
                  Submit Candidate
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={handleSubmit(onSaveDraft)}
                  loading={saveDraftMutation.isPending}
                  disabled={submitMutation.isPending || saveDraftMutation.isPending}
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save Draft
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate('/candidates')}
                >
                  Cancel
                </Button>

                {savedDraftId && (
                  <div className="pt-4 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
                      ✓ Draft saved. You can safely leave and continue later.
                    </p>
                  </div>
                )}
              </Card.Content>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CandidateCreate;
