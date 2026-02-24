import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Edit,
  Calendar,
  CheckCircle,
  Clock,
  AlertCircle,
  Flag,
  DollarSign,
  Download,
} from 'lucide-react';
import assessmentSeriesApi from '../services/assessmentSeriesApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';

const AssessmentSeriesView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [exporting, setExporting] = useState(false);

  // Redirect if ID is invalid
  if (!id || id === 'undefined' || id === 'new') {
    navigate('/assessment-series');
    return null;
  }

  // Fetch series details
  const { data, isLoading, error } = useQuery({
    queryKey: ['assessment-series', id],
    queryFn: () => assessmentSeriesApi.getById(id),
    enabled: !!id && id !== 'undefined' && id !== 'new',
  });

  const series = data?.data;

  // Set as current mutation
  const setCurrentMutation = useMutation({
    mutationFn: () => assessmentSeriesApi.setCurrent(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-series']);
      toast.success('Set as current assessment series!');
    },
    onError: (error) => {
      toast.error(`Failed to set as current: ${error.message}`);
    },
  });

  // Release results mutation
  const releaseResultsMutation = useMutation({
    mutationFn: () => assessmentSeriesApi.releaseResults(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-series', id]);
      toast.success('Results released successfully!');
    },
    onError: (error) => {
      toast.error(`Failed to release results: ${error.message}`);
    },
  });

  const handleExportSpecialNeeds = async () => {
    setExporting(true);
    try {
      const response = await assessmentSeriesApi.exportSpecialNeeds(id);

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      const contentDisposition = response.headers['content-disposition'];
      let filename = `special_needs_refugees_${new Date().toISOString().slice(0, 10)}.xlsx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch.length > 1) {
          filename = filenameMatch[1];
        } else {
          const fallbackMatch = contentDisposition.match(/filename=([^;]+)/);
          if (fallbackMatch && fallbackMatch.length > 1) {
            filename = fallbackMatch[1].trim();
          }
        }
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Export downloaded successfully!');
    } catch (error) {
      toast.error('Failed to download export');
    } finally {
      setExporting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading series details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Error loading series: {error.message}</div>
      </div>
    );
  }

  if (!series) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Assessment series not found</div>
      </div>
    );
  }

  const getStatusInfo = () => {
    const today = new Date();
    const startDate = new Date(series.start_date);
    const endDate = new Date(series.end_date);

    if (today < startDate) {
      return { label: 'Upcoming', color: 'gray', icon: Clock };
    } else if (today >= startDate && today <= endDate) {
      return { label: 'Ongoing', color: 'green', icon: AlertCircle };
    } else {
      return { label: 'Completed', color: 'purple', icon: CheckCircle };
    }
  };

  const statusInfo = getStatusInfo();
  const StatusIcon = statusInfo.icon;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/assessment-series')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Series
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{series.name}</h1>
            <p className="text-gray-600 mt-1">
              {formatDate(series.start_date)} - {formatDate(series.end_date)}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate(`/assessment-series/${id}/edit`)}
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit Series
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Series Information</h3>
            </Card.Header>
            <Card.Content className="space-y-4">
              <InfoItem
                icon={<Calendar className="w-5 h-5 text-gray-400" />}
                label="Series Name"
                value={series.name}
              />

              <InfoItem
                icon={<Calendar className="w-5 h-5 text-gray-400" />}
                label="Start Date"
                value={formatDate(series.start_date)}
              />

              <InfoItem
                icon={<Calendar className="w-5 h-5 text-gray-400" />}
                label="End Date"
                value={formatDate(series.end_date)}
              />

              <InfoItem
                icon={<Calendar className="w-5 h-5 text-gray-400" />}
                label="Results Release Date"
                value={formatDate(series.date_of_release)}
              />

              <InfoItem
                icon={<Calendar className="w-5 h-5 text-gray-400" />}
                label="Completion Year"
                value={series.completion_year || 'Not set'}
              />

              <InfoItem
                icon={<StatusIcon className="w-5 h-5 text-gray-400" />}
                label="Status"
                value={
                  <span
                    className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-${statusInfo.color}-100 text-${statusInfo.color}-800`}
                  >
                    {statusInfo.label}
                  </span>
                }
              />

              <InfoItem
                icon={<Flag className="w-5 h-5 text-gray-400" />}
                label="Current Series"
                value={
                  series.is_current ? (
                    <span className="text-green-600 font-medium">Yes</span>
                  ) : (
                    <span className="text-gray-500">No</span>
                  )
                }
              />

              <InfoItem
                icon={<CheckCircle className="w-5 h-5 text-gray-400" />}
                label="Results Released"
                value={
                  series.results_released ? (
                    <span className="text-green-600 font-medium">Yes</span>
                  ) : (
                    <span className="text-gray-500">No</span>
                  )
                }
              />

              <InfoItem
                icon={<Calendar className="w-5 h-5 text-gray-400" />}
                label="Fiscal Quarter"
                value={
                  series.quarter ? (
                    <span className="text-blue-600 font-medium">
                      {series.quarter === 'Q1' && 'Q1 (July - September)'}
                      {series.quarter === 'Q2' && 'Q2 (October - December)'}
                      {series.quarter === 'Q3' && 'Q3 (January - March)'}
                      {series.quarter === 'Q4' && 'Q4 (April - June)'}
                    </span>
                  ) : (
                    <span className="text-amber-500 font-medium">Not configured</span>
                  )
                }
              />

              <InfoItem
                icon={<DollarSign className="w-5 h-5 text-gray-400" />}
                label="Billing Status"
                value={
                  series.dont_charge ? (
                    <span className="text-purple-600 font-medium">No Charges</span>
                  ) : (
                    <span className="text-green-600 font-medium">Standard Billing</span>
                  )
                }
              />
            </Card.Content>
          </Card>
        </div>

        {/* Actions Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
            </Card.Header>
            <Card.Content className="space-y-3">
              {!series.is_current && (
                <Button
                  variant="primary"
                  size="md"
                  className="w-full"
                  onClick={() => {
                    if (window.confirm('Set this as the current assessment series?')) {
                      setCurrentMutation.mutate();
                    }
                  }}
                  loading={setCurrentMutation.isPending}
                >
                  <Flag className="w-4 h-4 mr-2" />
                  Set as Current
                </Button>
              )}

              {!series.results_released && (
                <Button
                  variant="success"
                  size="md"
                  className="w-full"
                  onClick={() => {
                    if (window.confirm('Release results for this assessment series?')) {
                      releaseResultsMutation.mutate();
                    }
                  }}
                  loading={releaseResultsMutation.isPending}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Release Results
                </Button>
              )}

              <Button
                variant="outline"
                size="md"
                className="w-full text-primary-600 border-primary-200 hover:bg-primary-50"
                onClick={handleExportSpecialNeeds}
                loading={exporting}
              >
                <Download className="w-4 h-4 mr-2" />
                Export Special Needs & Refugees
              </Button>

              <div className="pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500 space-y-1">
                  <p>Created: {formatDate(series.created_at)}</p>
                  <p>Updated: {formatDate(series.updated_at)}</p>
                </div>
              </div>
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

export default AssessmentSeriesView;
