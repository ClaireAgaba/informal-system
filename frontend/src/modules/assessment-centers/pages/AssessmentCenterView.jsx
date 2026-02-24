import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Edit,
  Building2,
  MapPin,
  Phone,
  Users,
  Users2,
  CheckCircle,
  XCircle,
  Plus,
  Tag,
} from 'lucide-react';
import assessmentCenterApi from '../services/assessmentCenterApi';
import candidateApi from '@modules/candidates/services/candidateApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';

const AssessmentCenterView = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Redirect if ID is invalid
  if (!id || id === 'undefined' || id === 'new') {
    navigate('/assessment-centers');
    return null;
  }

  // Fetch center details
  const { data, isLoading, error } = useQuery({
    queryKey: ['assessment-center', id],
    queryFn: () => assessmentCenterApi.getById(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  // Fetch center branches
  const { data: branchesData } = useQuery({
    queryKey: ['center-branches', id],
    queryFn: () => assessmentCenterApi.branches.getByCenter(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  // Fetch candidates count
  const { data: candidatesData } = useQuery({
    queryKey: ['center-candidates-count', id],
    queryFn: () => candidateApi.getByCenter(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  const center = data?.data;
  const branches = branchesData?.data?.results || [];
  const candidatesCount = candidatesData?.data?.count || 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading center details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Error loading center: {error.message}</div>
      </div>
    );
  }

  if (!center) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Assessment center not found</div>
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
          onClick={() => navigate('/assessment-centers')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Centers
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{center.center_name}</h1>
            <p className="text-gray-600 mt-1">Code: {center.center_number}</p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="md"
              onClick={() => navigate(`/assessment-centers/${id}/representatives`)}
            >
              <Users2 className="w-4 h-4 mr-2" />
              Center Representatives
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate(`/assessment-centers/${id}/edit`)}
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit Center
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Basic Info */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
            </Card.Header>
            <Card.Content className="space-y-4">
              {/* Status Badge */}
              <div className="flex items-center justify-center py-4">
                <span
                  className={`inline-flex px-4 py-2 text-sm font-semibold rounded-full ${
                    center.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {center.is_active ? (
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
                label="Center Number"
                value={center.center_number}
              />

              <InfoItem
                icon={<Building2 className="w-5 h-5 text-gray-400" />}
                label="Center Name"
                value={center.center_name}
              />

              <InfoItem
                icon={<Tag className="w-5 h-5 text-gray-400" />}
                label="Assessment Category"
                value={
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      center.assessment_category === 'VTI'
                        ? 'bg-blue-100 text-blue-800'
                        : center.assessment_category === 'TTI'
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {center.assessment_category_display}
                  </span>
                }
              />

              <InfoItem
                icon={<MapPin className="w-5 h-5 text-gray-400" />}
                label="District"
                value={center.district_name || 'Not set'}
              />

              <InfoItem
                icon={<MapPin className="w-5 h-5 text-gray-400" />}
                label="Village"
                value={center.village_name || 'Not set'}
              />

              <InfoItem
                icon={<Phone className="w-5 h-5 text-gray-400" />}
                label="Contact 1"
                value={center.contact_1 || 'Not provided'}
              />

              {center.contact_2 && (
                <InfoItem
                  icon={<Phone className="w-5 h-5 text-gray-400" />}
                  label="Contact 2"
                  value={center.contact_2}
                />
              )}

              <InfoItem
                icon={<Building2 className="w-5 h-5 text-gray-400" />}
                label="Has Branches"
                value={
                  center.has_branches ? (
                    <span className="text-green-600 font-medium">Yes</span>
                  ) : (
                    <span className="text-gray-500">No</span>
                  )
                }
              />

              <div className="pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500 space-y-1">
                  <p>Created: {formatDate(center.created_at)}</p>
                  <p>Updated: {formatDate(center.updated_at)}</p>
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Candidates Count Card */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-primary-100 rounded-lg">
                    <Users className="w-6 h-6 text-primary-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Total Candidates</p>
                    <p className="text-2xl font-bold text-gray-900">{candidatesCount}</p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/candidates?assessment_center=${id}`)}
                >
                  View All
                </Button>
              </div>
            </Card.Content>
          </Card>
        </div>

        {/* Right Column - Branches */}
        <div className="lg:col-span-2">
          <Card>
            <Card.Header>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Center Branches
                  {center.has_branches && branches.length > 0 && (
                    <span className="ml-2 text-sm font-medium text-gray-500">({branches.length})</span>
                  )}
                </h3>
                {center.has_branches && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/assessment-centers/${id}/branches/new`)}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Branch
                  </Button>
                )}
              </div>
            </Card.Header>
            <Card.Content>
              {!center.has_branches ? (
                <div className="text-center py-8 text-gray-500">
                  This center does not have branches enabled.
                </div>
              ) : branches.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No branches defined for this center yet.
                </div>
              ) : (
                <div className="space-y-4">
                  {branches.map((branch) => (
                    <div
                      key={branch.id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-base font-semibold text-gray-900">
                            {branch.branch_name}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">Code: {branch.branch_code}</p>
                          <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">District:</span>
                              <span className="ml-2 font-medium text-gray-900">
                                {branch.district_name || 'N/A'}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500">Village:</span>
                              <span className="ml-2 font-medium text-gray-900">
                                {branch.village_name || 'N/A'}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500">Status:</span>
                              <span
                                className={`ml-2 inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${
                                  branch.is_active
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {branch.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500">Candidates:</span>
                              <span className="ml-2 font-medium text-primary-600">
                                {branch.candidates_count ?? 0}
                              </span>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/assessment-centers/branches/${branch.id}/edit`)}
                        >
                          <Edit className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card.Content>
          </Card>
        </div>
      </div>
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

export default AssessmentCenterView;
