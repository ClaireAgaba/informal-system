import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import {
  ArrowLeft,
  Save,
  X,
  Upload,
  Loader,
} from 'lucide-react';
import { toast } from 'sonner';
import candidateApi from '../services/candidateApi';
import occupationApi from '@modules/occupations/services/occupationApi';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const CandidateEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('personal-info');
  const [photoPreview, setPhotoPreview] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  const fetchAllPagesFetch = async (baseUrl, params = {}, page = 1, acc = []) => {
    const url = new URL(baseUrl, window.location.origin);
    const search = new URLSearchParams(params);
    search.set('page', String(page));
    search.set('page_size', '1000');
    url.search = search.toString();

    const response = await fetch(url.toString());
    if (!response.ok) throw new Error('Request failed');
    const data = await response.json();

    if (Array.isArray(data)) {
      return [...acc, ...data];
    }

    const results = data?.results || [];
    const nextAcc = [...acc, ...results];

    if (!data?.next) {
      return nextAcc;
    }

    return fetchAllPagesFetch(baseUrl, params, page + 1, nextAcc);
  };

  const fetchAllPagesApi = async (fetchPage, params = {}, page = 1, acc = []) => {
    const response = await fetchPage({ ...params, page, page_size: 1000 });
    const data = response?.data;

    if (Array.isArray(data)) {
      return [...acc, ...data];
    }

    const results = data?.results || [];
    const nextAcc = [...acc, ...results];

    if (!data?.next) {
      return nextAcc;
    }

    return fetchAllPagesApi(fetchPage, params, page + 1, nextAcc);
  };

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
    setValue,
    watch,
  } = useForm();

  const pad2 = (n) => String(n).padStart(2, '0');
  const formatDate = (d) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
  const today = new Date();
  const todayStr = formatDate(today);
  const maxDob = formatDate(new Date(today.getFullYear() - 12, today.getMonth(), today.getDate()));
  const minDob = formatDate(new Date(today.getFullYear() - 100, today.getMonth(), today.getDate()));

  // Fetch candidate details
  const { data, isLoading } = useQuery({
    queryKey: ['candidate', id],
    queryFn: () => candidateApi.getById(id),
  });

  const candidate = data?.data;

  const selectedDistrict = watch('district');

  // Fetch districts
  const { data: districtsData } = useQuery({
    queryKey: ['districts'],
    queryFn: async () => {
      return fetchAllPagesFetch('/api/configurations/districts/');
    },
  });

  // Fetch villages
  const { data: villagesData } = useQuery({
    queryKey: ['villages', selectedDistrict],
    queryFn: async () => {
      return fetchAllPagesFetch('/api/configurations/villages/', { district: selectedDistrict });
    },
    enabled: !!selectedDistrict,
  });

  // Fetch disabilities
  const { data: disabilitiesData } = useQuery({
    queryKey: ['disabilities'],
    queryFn: async () => {
      return fetchAllPagesFetch('/api/configurations/nature-of-disabilities/');
    },
  });

  // Fetch occupations
  const { data: occupationsData } = useQuery({
    queryKey: ['occupations'],
    queryFn: () => fetchAllPagesApi(occupationApi.getAll),
  });

  // Fetch assessment centers
  const { data: centersData } = useQuery({
    queryKey: ['assessment-centers'],
    queryFn: () => fetchAllPagesApi(assessmentCenterApi.getAll),
  });

  const { data: nationalitiesData } = useQuery({
    queryKey: ['candidate-nationalities'],
    queryFn: () => candidateApi.getNationalities(),
  });

  const districts = districtsData || [];
  const villages = villagesData || [];
  const disabilities = disabilitiesData || [];
  const allOccupations = occupationsData || [];
  const centers = centersData || [];
  const nationalityOptions = nationalitiesData?.data || [];

  useEffect(() => {
    setValue('village', '');
  }, [selectedDistrict, setValue]);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (!userStr) return;
    try {
      setCurrentUser(JSON.parse(userStr));
    } catch (e) {
      setCurrentUser(null);
    }
  }, []);

  const isCenterRep = currentUser?.user_type === 'center_representative';
  const repCenter = currentUser?.center_representative?.assessment_center;
  const repCenterId = repCenter?.id ? String(repCenter.id) : '';
  const repBranch = currentUser?.center_representative?.assessment_center_branch;
  const repBranchId = repBranch?.id ? String(repBranch.id) : '';
  const availableCenters = isCenterRep && repCenterId
    ? [{ id: repCenter.id, center_number: repCenter.center_number, center_name: repCenter.center_name }]
    : centers;

  const selectedCenter = watch('assessment_center');
  const { data: branchesData } = useQuery({
    queryKey: ['center-branches', selectedCenter],
    queryFn: () => fetchAllPagesApi(assessmentCenterApi.branches.getAll, { assessment_center: selectedCenter }),
    enabled: !!selectedCenter,
  });

  const branches = branchesData || [];

  const availableBranches = isCenterRep && repBranchId
    ? branches.filter((b) => String(b.id) === repBranchId)
    : branches;

  // Watch registration category to filter occupations
  const registrationCategory = watch('registration_category');
  
  // Filter occupations based on registration category
  const occupations = allOccupations.filter(occ => {
    if (!registrationCategory) return true;
    if (registrationCategory === 'workers_pas') {
      return occ.occ_category === 'workers_pas';
    } else {
      return occ.occ_category === 'formal';
    }
  });

  // Populate form when data loads
  useEffect(() => {
    if (candidate) {
      reset({
        full_name: candidate.full_name || '',
        date_of_birth: candidate.date_of_birth || '',
        gender: candidate.gender || '',
        nationality: candidate.nationality || '',
        is_refugee: candidate.is_refugee || false,
        refugee_number: candidate.refugee_number || '',
        contact: candidate.contact || '',
        district: candidate.district || '',
        village: candidate.village || '',
        has_disability: candidate.has_disability || false,
        nature_of_disability: candidate.nature_of_disability || '',
        disability_specification: candidate.disability_specification || '',
        assessment_center: candidate.assessment_center || '',
        assessment_center_branch: candidate.assessment_center_branch || '',
        entry_year: candidate.entry_year || '',
        intake: candidate.intake || '',
        registration_category: candidate.registration_category || '',
        occupation: candidate.occupation || '',
        preferred_assessment_language: candidate.preferred_assessment_language || '',
        start_date: candidate.start_date || '',
        finish_date: candidate.finish_date || '',
        assessment_date: candidate.assessment_date || '',
        modular_module_count: candidate.modular_module_count || '',
        modular_billing_amount: candidate.modular_billing_amount || '',
        enrollment_level: candidate.enrollment_level || '',
        status: candidate.status || 'active',
      });
      setPhotoPreview(candidate.passport_photo);
    }
  }, [candidate, reset]);

  useEffect(() => {
    if (!isCenterRep || !repCenterId) return;
    setValue('assessment_center', repCenterId);
    if (repBranchId) {
      setValue('assessment_center_branch', repBranchId);
    }
  }, [isCenterRep, repCenterId, repBranchId, setValue]);

  const prevSelectedCenterRef = useRef(undefined);
  useEffect(() => {
    const prev = prevSelectedCenterRef.current;

    if (!selectedCenter) {
      setValue('assessment_center_branch', '');
      prevSelectedCenterRef.current = selectedCenter;
      return;
    }

    if (prev && String(prev) !== String(selectedCenter)) {
      setValue('assessment_center_branch', '');
    }

    prevSelectedCenterRef.current = selectedCenter;
  }, [selectedCenter, setValue]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data) => candidateApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate', id]);
      queryClient.invalidateQueries(['candidates']);
      toast.success('Candidate updated successfully!');
      navigate(`/candidates/${id}`);
    },
    onError: (error) => {
      console.error('Update error:', error);
      console.error('Error response:', error.response?.data);
      const errorMsg = error.response?.data?.detail || 
                       JSON.stringify(error.response?.data) || 
                       error.message;
      toast.error(`Failed to update candidate: ${errorMsg}`);
    },
  });

  const onSubmit = (data) => {
    console.log('Original form data:', data);
    
    // Clean up data - convert empty strings to null for foreign keys
    const cleanedData = { ...data };
    const fkFields = ['district', 'village', 'nature_of_disability', 
                      'assessment_center', 'assessment_center_branch', 'occupation'];
    
    fkFields.forEach(field => {
      if (cleanedData[field] === '' || cleanedData[field] === 'None') {
        cleanedData[field] = null;
      } else if (cleanedData[field]) {
        // Convert to integer if it's a string number
        cleanedData[field] = parseInt(cleanedData[field], 10);
      }
    });
    
    // Ensure boolean fields are never null
    cleanedData.is_refugee = cleanedData.is_refugee === true;
    cleanedData.has_disability = cleanedData.has_disability === true;
    cleanedData.block_portal_results = cleanedData.block_portal_results === true;
    
    // Fields that should be empty string instead of null
    const textFields = ['disability_specification', 'enrollment_level', 'refugee_number', 
                        'preferred_assessment_language', 'reg_number'];
    
    // Convert empty strings to null for optional fields (but not booleans or text fields)
    Object.keys(cleanedData).forEach(key => {
      if (cleanedData[key] === '' && typeof cleanedData[key] !== 'boolean') {
        // Keep empty string for text fields, null for others
        if (!textFields.includes(key)) {
          cleanedData[key] = null;
        }
      }
    });
    
    console.log('Cleaned data being sent:', cleanedData);
    updateMutation.mutate(cleanedData);
  };

  // Photo upload mutation
  const uploadPhotoMutation = useMutation({
    mutationFn: (file) => candidateApi.uploadPhoto(id, file),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', id]);
      toast.success('Photo uploaded successfully!');
    },
    onError: (error) => {
      toast.error(`Failed to upload photo: ${error.message}`);
    },
  });

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Show preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
      
      // Upload to server
      uploadPhotoMutation.mutate(file);
    }
  };

  // Document upload mutation
  const uploadDocumentMutation = useMutation({
    mutationFn: ({ file, type }) => candidateApi.uploadDocument(id, file, type),
    onSuccess: (response, variables) => {
      queryClient.invalidateQueries(['candidate', id]);
      toast.success(`${variables.type === 'identification' ? 'Identification' : 'Qualification'} document uploaded successfully!`);
    },
    onError: (error) => {
      toast.error(`Failed to upload document: ${error.message}`);
    },
  });

  const handleDocumentChange = (e, documentType) => {
    const file = e.target.files[0];
    if (file) {
      uploadDocumentMutation.mutate({ file, type: documentType });
    }
  };

  const tabs = [
    { id: 'personal-info', label: 'Personal Information' },
    { id: 'location', label: 'Location Information' },
    { id: 'special', label: 'Special Considerations' },
    { id: 'enrollment', label: 'Enrollment Details' },
    { id: 'occupation', label: 'Occupation Details' },
    { id: 'documents', label: 'Documents' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/candidates/${id}`)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to View
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Edit Candidate</h1>
            <p className="text-sm text-gray-600 mt-1">
              {candidate?.full_name} - {candidate?.registration_number || 'No Reg Number'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate(`/candidates/${id}`)}
          >
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleSubmit(onSubmit)}
            disabled={!isDirty || updateMutation.isPending}
            loading={updateMutation.isPending}
          >
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Photo */}
          <div className="lg:col-span-1">
            <Card>
              <Card.Content className="text-center py-6">
                <div className="mb-4">
                  {photoPreview ? (
                    <img
                      src={photoPreview}
                      alt="Preview"
                      className="w-32 h-32 rounded-full object-cover mx-auto border-4 border-gray-200"
                    />
                  ) : (
                    <div className="w-32 h-32 rounded-full bg-gray-200 flex items-center justify-center mx-auto">
                      <span className="text-4xl text-gray-400">?</span>
                    </div>
                  )}
                </div>
                <div>
                  <input
                    type="file"
                    id="photo-upload-edit"
                    accept="image/*"
                    onChange={handlePhotoChange}
                    className="hidden"
                  />
                  <label
                    htmlFor="photo-upload-edit"
                    className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Change Photo
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  JPG, PNG or GIF (max 5MB)
                </p>
                {uploadPhotoMutation.isPending && (
                  <p className="text-xs text-blue-600 mt-1">Uploading...</p>
                )}
              </Card.Content>
            </Card>
          </div>

          {/* Right Column - Form */}
          <div className="lg:col-span-2">
            <Card>
              {/* Tabs */}
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px overflow-x-auto">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-6 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                        activeTab === tab.id
                          ? 'border-primary-600 text-primary-600'
                          : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {/* Personal Information Tab */}
                {activeTab === 'personal-info' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Personal Information
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Full Name *
                        </label>
                        <input
                          type="text"
                          {...register('full_name', { required: 'Full name is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                        {errors.full_name && (
                          <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Date of Birth *
                        </label>
                        <input
                          type="date"
                          min={minDob}
                          max={maxDob}
                          {...register('date_of_birth', {
                            required: 'Date of birth is required',
                            validate: (value) => {
                              if (!value) return true;
                              if (value > todayStr) return 'Date of birth cannot be in the future.';
                              if (value < minDob) return 'Candidate cannot be older than 100 years.';
                              if (value > maxDob) return 'Candidate must be at least 12 years old.';
                              return true;
                            },
                          })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                        {errors.date_of_birth && (
                          <p className="text-red-500 text-xs mt-1">{errors.date_of_birth.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Gender *
                        </label>
                        <select
                          {...register('gender', { required: 'Gender is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">Select Gender</option>
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                          <option value="other">Other</option>
                        </select>
                        {errors.gender && (
                          <p className="text-red-500 text-xs mt-1">{errors.gender.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Nationality *
                        </label>
                        <select
                          {...register('nationality', { required: 'Nationality is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          {candidate?.nationality && !nationalityOptions.some((n) => n.value === candidate.nationality) && (
                            <option value={candidate.nationality}>{candidate.nationality}</option>
                          )}
                          {nationalityOptions.map((n) => (
                            <option key={n.value} value={n.value}>
                              {n.label}
                            </option>
                          ))}
                        </select>
                        {errors.nationality && (
                          <p className="text-red-500 text-xs mt-1">{errors.nationality.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Contact *
                        </label>
                        <input
                          type="text"
                          {...register('contact', { required: 'Contact is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                        {errors.contact && (
                          <p className="text-red-500 text-xs mt-1">{errors.contact.message}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Location Information Tab */}
                {activeTab === 'location' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Location Information
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          District *
                        </label>
                        <select
                          {...register('district', { required: 'District is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">Select district</option>
                          {districts.map((district) => (
                            <option key={district.id} value={district.id}>
                              {district.name}
                            </option>
                          ))}
                        </select>
                        {errors.district && (
                          <p className="text-red-500 text-xs mt-1">{errors.district.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Village
                        </label>
                        <select
                          {...register('village')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
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
                  </div>
                )}

                {/* Special Considerations Tab */}
                {activeTab === 'special' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Special Considerations
                    </h3>

                    <div className="space-y-4">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          {...register('is_refugee')}
                          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        />
                        <label className="ml-2 text-sm font-medium text-gray-700">
                          Is Refugee
                        </label>
                      </div>

                      {watch('is_refugee') && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Refugee Number
                          </label>
                          <input
                            type="text"
                            {...register('refugee_number')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>
                      )}

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          {...register('has_disability')}
                          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        />
                        <label className="ml-2 text-sm font-medium text-gray-700">
                          Has Disability
                        </label>
                      </div>

                      {watch('has_disability') && (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Nature of Disability
                            </label>
                            <select
                              {...register('nature_of_disability')}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
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
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Disability Specification
                            </label>
                            <textarea
                              {...register('disability_specification')}
                              rows="3"
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                              placeholder="Provide additional details..."
                            />
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Enrollment Details Tab */}
                {activeTab === 'enrollment' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Enrollment Details
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Registration Category *
                        </label>
                        <select
                          {...register('registration_category', { required: 'Category is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">Select Category</option>
                          <option value="modular">Modular</option>
                          <option value="formal">Formal</option>
                          <option value="workers_pas">Worker's PAS</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Entry Year
                        </label>
                        <input
                          type="number"
                          {...register('entry_year')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Assessment Intake
                        </label>
                        <select
                          {...register('intake')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">Select Intake</option>
                          <option value="M">March</option>
                          <option value="J">June</option>
                          <option value="S">September</option>
                          <option value="D">December</option>
                          {candidate?.intake === 'A' && <option value="A">August</option>}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Assessment Center *
                        </label>
                        <select
                          {...register('assessment_center', { required: 'Assessment center is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          disabled={isCenterRep && !!repCenterId}
                        >
                          <option value="">Select assessment center</option>
                          {availableCenters.map((center) => (
                            <option key={center.id} value={center.id}>
                              {center.center_number} - {center.center_name}
                            </option>
                          ))}
                        </select>
                        {errors.assessment_center && (
                          <p className="text-red-500 text-xs mt-1">{errors.assessment_center.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Center Branch
                        </label>
                        <select
                          {...register('assessment_center_branch')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          disabled={!selectedCenter || (isCenterRep && !!repCenterId)}
                        >
                          <option value="">Select branch (optional)</option>
                          {availableBranches.map((branch) => (
                            <option key={branch.id} value={branch.id}>
                              {branch.branch_code}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Start Date
                        </label>
                        <input
                          type="date"
                          {...register('start_date')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Finish Date
                        </label>
                        <input
                          type="date"
                          {...register('finish_date')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>

                      {watch('registration_category') === 'modular' && (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Module Count
                            </label>
                            <input
                              type="number"
                              {...register('modular_module_count')}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Billing Amount
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              {...register('modular_billing_amount')}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Occupation Details Tab */}
                {activeTab === 'occupation' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Occupation Details
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Occupation *
                        </label>
                        <select
                          {...register('occupation', { required: 'Occupation is required' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="">Select occupation</option>
                          {occupations.map((occupation) => (
                            <option key={occupation.id} value={occupation.id}>
                              {occupation.occ_name}
                            </option>
                          ))}
                        </select>
                        {errors.occupation && (
                          <p className="text-red-500 text-xs mt-1">{errors.occupation.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Enrollment Level
                        </label>
                        <input
                          type="text"
                          {...register('enrollment_level')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Assessment Date
                        </label>
                        <input
                          type="date"
                          {...register('assessment_date')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Preferred Language
                        </label>
                        <input
                          type="text"
                          {...register('preferred_assessment_language')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Status
                        </label>
                        <select
                          {...register('status')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="active">Active</option>
                          <option value="inactive">Inactive</option>
                          <option value="suspended">Suspended</option>
                          <option value="completed">Completed</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* Documents Tab */}
                {activeTab === 'documents' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Documents
                    </h3>
                    <p className="text-sm text-gray-600 mb-4">Upload or update required documents</p>

                    <div className="grid grid-cols-1 gap-4">
                      {/* Identification Document */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Identification Document
                        </label>
                        <input
                          type="file"
                          accept=".pdf,.png,.jpg,.jpeg"
                          onChange={(e) => handleDocumentChange(e, 'identification')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          disabled={uploadDocumentMutation.isPending}
                        />
                        <p className="mt-1 text-xs text-gray-500">
                          National ID, Birth Certificate, or other identification (PNG, JPG, PDF max 10MB)
                        </p>
                        {candidate.identification_document && (
                          <p className="mt-1 text-xs text-green-600">
                            ✓ Current file: {candidate.identification_document.split('/').pop()}
                          </p>
                        )}
                        {uploadDocumentMutation.isPending && (
                          <p className="mt-1 text-xs text-blue-600">Uploading...</p>
                        )}
                      </div>

                      {/* Qualification Document */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Qualification Document
                        </label>
                        <input
                          type="file"
                          accept=".pdf,.png,.jpg,.jpeg"
                          onChange={(e) => handleDocumentChange(e, 'qualification')}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          disabled={uploadDocumentMutation.isPending}
                        />
                        <p className="mt-1 text-xs text-gray-500">
                          Relevant qualifications for Full Occupation candidates (PNG, JPG, PDF max 10MB)
                        </p>
                        {candidate.qualification_document && (
                          <p className="mt-1 text-xs text-green-600">
                            ✓ Current file: {candidate.qualification_document.split('/').pop()}
                          </p>
                        )}
                        {uploadDocumentMutation.isPending && (
                          <p className="mt-1 text-xs text-blue-600">Uploading...</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CandidateEdit;
