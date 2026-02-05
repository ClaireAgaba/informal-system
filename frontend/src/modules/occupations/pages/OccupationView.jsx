import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Briefcase,
  Tag,
  Building2,
  CheckCircle,
  XCircle,
  Layers,
  BookOpen,
  FileText,
  Plus,
} from 'lucide-react';
import occupationApi from '../services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import LevelModal from '../components/LevelModal';
import { toast } from 'sonner';
import { formatDate } from '@shared/utils/formatters';

const OccupationView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('levels');
  const [isLevelModalOpen, setIsLevelModalOpen] = useState(false);
  const [editingLevel, setEditingLevel] = useState(null);

  // Redirect if ID is invalid
  if (!id || id === 'undefined' || id === 'new') {
    navigate('/occupations');
    return null;
  }

  // Fetch occupation details
  const { data, isLoading, error } = useQuery({
    queryKey: ['occupation', id],
    queryFn: () => occupationApi.getById(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  // Fetch occupation levels
  const { data: levelsData } = useQuery({
    queryKey: ['occupation-levels', id],
    queryFn: () => occupationApi.levels.getByOccupation(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  // Fetch occupation modules
  const { data: modulesData, error: modulesError } = useQuery({
    queryKey: ['occupation-modules', id],
    queryFn: () => occupationApi.modules.getByOccupation(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  // Fetch occupation papers
  const { data: papersData, error: papersError } = useQuery({
    queryKey: ['occupation-papers', id],
    queryFn: () => occupationApi.papers.getByOccupation(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  const occupation = data?.data;
  const levels = levelsData?.data?.results || [];
  const modules = modulesData?.data?.results || [];
  const papers = papersData?.data?.results || [];

  // Level mutations
  const createLevelMutation = useMutation({
    mutationFn: (levelData) => occupationApi.levels.create({ ...levelData, occupation: id }),
    onSuccess: () => {
      toast.success('Level created successfully!');
      queryClient.invalidateQueries(['occupation-levels', id]);
      setIsLevelModalOpen(false);
      setEditingLevel(null);
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to create level');
    },
  });

  const updateLevelMutation = useMutation({
    mutationFn: ({ levelId, data }) => occupationApi.levels.update(levelId, data),
    onSuccess: () => {
      toast.success('Level updated successfully!');
      queryClient.invalidateQueries(['occupation-levels', id]);
      setIsLevelModalOpen(false);
      setEditingLevel(null);
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to update level');
    },
  });

  const handleLevelSubmit = (data) => {
    if (editingLevel) {
      updateLevelMutation.mutate({ levelId: editingLevel.id, data });
    } else {
      createLevelMutation.mutate(data);
    }
  };

  const handleEditLevel = (level) => {
    setEditingLevel(level);
    setIsLevelModalOpen(true);
  };

  const handleAddLevel = () => {
    setEditingLevel(null);
    setIsLevelModalOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading occupation details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Error loading occupation: {error.message}</div>
      </div>
    );
  }

  if (!occupation) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Occupation not found</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/occupations')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Occupations
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{occupation.occ_name}</h1>
            <p className="text-gray-600 mt-1">Code: {occupation.occ_code}</p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate(`/occupations/${id}/edit`)}
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit Occupation
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Basic Info */}
        <div className="lg:col-span-1">
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
            </Card.Header>
            <Card.Content className="space-y-4">
              {/* Status Badge */}
              <div className="flex items-center justify-center py-4">
                <span
                  className={`inline-flex px-4 py-2 text-sm font-semibold rounded-full ${
                    occupation.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {occupation.is_active ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Active
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 mr-2" />
                      Inactive
                    </>
                  )}
                </span>
              </div>

              <InfoItem
                icon={<Tag className="w-5 h-5 text-gray-400" />}
                label="Occupation Code"
                value={occupation.occ_code}
              />

              <InfoItem
                icon={<Briefcase className="w-5 h-5 text-gray-400" />}
                label="Occupation Name"
                value={occupation.occ_name}
              />

              <InfoItem
                icon={<Tag className="w-5 h-5 text-gray-400" />}
                label="Category"
                value={
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      occupation.occ_category === 'formal'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-purple-100 text-purple-800'
                    }`}
                  >
                    {occupation.occ_category_display}
                  </span>
                }
              />

              <InfoItem
                icon={<Building2 className="w-5 h-5 text-gray-400" />}
                label="Sector"
                value={occupation.sector_name || 'Not assigned'}
              />

              <InfoItem
                icon={<Layers className="w-5 h-5 text-gray-400" />}
                label="Has Modular"
                value={
                  occupation.has_modular ? (
                    <span className="text-green-600 font-medium">Yes</span>
                  ) : (
                    <span className="text-gray-500">No</span>
                  )
                }
              />

              {/* Award fields - only for formal category */}
              {occupation.occ_category === 'formal' && occupation.award && (
                <InfoItem
                  icon={<FileText className="w-5 h-5 text-gray-400" />}
                  label="Award (Full Occupation)"
                  value={occupation.award}
                />
              )}

              {occupation.occ_category === 'formal' && occupation.has_modular && occupation.award_modular && (
                <InfoItem
                  icon={<FileText className="w-5 h-5 text-gray-400" />}
                  label="Award (Modular)"
                  value={occupation.award_modular}
                />
              )}

              {occupation.contact_hours && (
                <InfoItem
                  icon={<Tag className="w-5 h-5 text-gray-400" />}
                  label="Contact Hours"
                  value={`${occupation.contact_hours} Hrs`}
                />
              )}

              <InfoItem
                icon={<Layers className="w-5 h-5 text-gray-400" />}
                label="Total Levels"
                value={occupation.levels_count || 0}
              />

              <div className="pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500 space-y-1">
                  <p>Created: {formatDate(occupation.created_at)}</p>
                  <p>Updated: {formatDate(occupation.updated_at)}</p>
                </div>
              </div>
            </Card.Content>
          </Card>
        </div>

        {/* Right Column - Tabs */}
        <div className="lg:col-span-2">
          <Card>
            {/* Tabs Navigation */}
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                <button
                  onClick={() => setActiveTab('levels')}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'levels'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Layers className="w-4 h-4 inline mr-2" />
                  Levels ({levels.length})
                </button>
                <button
                  onClick={() => setActiveTab('modules')}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'modules'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <BookOpen className="w-4 h-4 inline mr-2" />
                  Modules ({modules.length})
                </button>
                <button
                  onClick={() => setActiveTab('papers')}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'papers'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <FileText className="w-4 h-4 inline mr-2" />
                  Papers ({papers.length})
                </button>
              </nav>
            </div>

            <Card.Content className="p-6">
              {/* Levels Tab */}
              {activeTab === 'levels' && (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Occupation Levels</h3>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleAddLevel}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Level
                    </Button>
                  </div>
                  {levels.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No levels defined for this occupation yet.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {levels.map((level, index) => {
                    const isLevel1 = index === 0 || level.level_name.toLowerCase().includes('level 1');
                    const isFormal = occupation.occ_category === 'formal';
                    const isWorkersPas = occupation.occ_category === 'workers_pas';
                    const hasModular = occupation.has_modular;
                    
                    return (
                      <div
                        key={level.id}
                        className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="text-base font-semibold text-gray-900">
                                {level.level_name}
                              </h4>
                              <span
                                className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${
                                  level.is_active
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {level.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </div>
                            
                            <div className="space-y-3">
                              {/* Structure Type */}
                              <div className="flex items-center text-sm">
                                <span className="text-gray-500 w-48">Structure Type:</span>
                                <span className="font-medium text-gray-900">
                                  {level.structure_type_display}
                                </span>
                              </div>
                              
                              {/* Formal Fee - Show for formal category */}
                              {isFormal && (
                                <div className="flex items-center text-sm">
                                  <span className="text-gray-500 w-48">Formal Fee:</span>
                                  <span className="font-medium text-gray-900">
                                    UGX {level.formal_fee?.toLocaleString() || '0.00'}
                                  </span>
                                </div>
                              )}
                              
                              {/* Worker's PAS Fee - Only show for workers_pas category */}
                              {isWorkersPas && (
                                <div className="flex items-center text-sm">
                                  <span className="text-gray-500 w-48">Worker's PAS Fee:</span>
                                  <span className="font-medium text-gray-900">
                                    UGX {level.workers_pas_per_module_fee?.toLocaleString() || '0.00'}
                                  </span>
                                </div>
                              )}
                              
                              {/* Modular Fees - Only show for Level 1 if occupation has_modular is true */}
                              {isFormal && hasModular && isLevel1 && (
                                <>
                                  <div className="flex items-center text-sm">
                                    <span className="text-gray-500 w-48">Modular Fee (Single Module):</span>
                                    <span className="font-medium text-gray-900">
                                      UGX {level.modular_fee_single_module?.toLocaleString() || '0.00'}
                                    </span>
                                  </div>
                                  
                                  <div className="flex items-center text-sm">
                                    <span className="text-gray-500 w-48">Modular Fee (Double Module):</span>
                                    <span className="font-medium text-gray-900">
                                      UGX {level.modular_fee_double_module?.toLocaleString() || '0.00'}
                                    </span>
                                  </div>
                                </>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditLevel(level)}
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                        );
                      })}
                    </div>
                  )}
                </>
              )}

              {/* Modules Tab */}
              {activeTab === 'modules' && (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Occupation Modules</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/occupations/${id}/modules/new`)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Module
                    </Button>
                  </div>
                  {modules.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No modules defined for this occupation yet.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {modules.map((module) => (
                        <div
                          key={module.id}
                          className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-base font-semibold text-gray-900">
                                  {module.module_name}
                                </h4>
                                <span
                                  className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${
                                    module.is_active
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-gray-100 text-gray-800'
                                  }`}
                                >
                                  {module.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </div>
                              <div className="space-y-1 text-sm">
                                <div className="flex items-center">
                                  <span className="text-gray-500 w-32">Module Code:</span>
                                  <span className="font-medium text-gray-900">{module.module_code}</span>
                                </div>
                                <div className="flex items-center">
                                  <span className="text-gray-500 w-32">Level:</span>
                                  <span className="text-gray-900">{module.level_name || 'N/A'}</span>
                                </div>
                              </div>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => navigate(`/occupations/modules/${module.id}/edit`)}
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}

              {/* Papers Tab */}
              {activeTab === 'papers' && (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Occupation Papers</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/occupations/${id}/papers/new`)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Paper
                    </Button>
                  </div>
                  {papers.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No papers defined for this occupation yet.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {papers.map((paper) => (
                        <div
                          key={paper.id}
                          className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-base font-semibold text-gray-900">
                                  {paper.paper_name}
                                </h4>
                                <span
                                  className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${
                                    paper.is_active
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-gray-100 text-gray-800'
                                  }`}
                                >
                                  {paper.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </div>
                              <div className="space-y-1 text-sm">
                                <div className="flex items-center">
                                  <span className="text-gray-500 w-32">Paper Code:</span>
                                  <span className="font-medium text-gray-900">{paper.paper_code}</span>
                                </div>
                                <div className="flex items-center">
                                  <span className="text-gray-500 w-32">Paper Type:</span>
                                  <span className="text-gray-900">{paper.paper_type_display || paper.paper_type}</span>
                                </div>
                                <div className="flex items-center">
                                  <span className="text-gray-500 w-32">Level:</span>
                                  <span className="text-gray-900">{paper.level_name || 'N/A'}</span>
                                </div>
                                {paper.module && (
                                  <div className="flex items-center">
                                    <span className="text-gray-500 w-32">Module:</span>
                                    <span className="text-gray-900 font-medium">{paper.module_code || paper.module}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => navigate(`/occupations/papers/${paper.id}/edit`)}
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </Card.Content>
          </Card>
        </div>
      </div>

      {/* Level Modal */}
      <LevelModal
        isOpen={isLevelModalOpen}
        onClose={() => {
          setIsLevelModalOpen(false);
          setEditingLevel(null);
        }}
        onSubmit={handleLevelSubmit}
        level={editingLevel}
        isLoading={createLevelMutation.isPending || updateLevelMutation.isPending}
      />
    </div>
  );
};

// Helper Component
const InfoItem = ({ icon, label, value }) => (
  <div className="flex items-start space-x-3">
    <div className="flex-shrink-0 mt-0.5">{icon}</div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-1 text-sm text-gray-900">{value}</p>
    </div>
  </div>
);

export default OccupationView;
