import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Edit,
  Pencil,
  Trash2,
  CheckCircle,
  XCircle,
  CreditCard,
  Download,
  Upload,
  Mail,
  Phone,
  MapPin,
  Calendar,
  User,
  FileText,
  AlertCircle,
  X,
  Plus,
  Send,
  MoreVertical,
  ChevronDown,
  Building2,
  Briefcase,
  Tag,
  Eye,
} from 'lucide-react';
import candidateApi from '../services/candidateApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';
import EnrollmentModal from '../components/EnrollmentModal';
import ChangeSeriesModal from '../components/ChangeSeriesModal';
import ChangeCenterModal from '../components/ChangeCenterModal';
import ChangeOccupationModal from '../components/ChangeOccupationModal';
import ChangeRegCategoryModal from '../components/ChangeRegCategoryModal';
import CandidateResults from '../components/CandidateResults';

const CandidateView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const fromAwards = location.state?.from === 'awards';
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('bio-data');
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [declineReason, setDeclineReason] = useState('');
  const [showEnrollmentModal, setShowEnrollmentModal] = useState(false);
  const [showChangeSeriesModal, setShowChangeSeriesModal] = useState(false);
  const [showChangeCenterModal, setShowChangeCenterModal] = useState(false);
  const [showChangeOccupationModal, setShowChangeOccupationModal] = useState(false);
  const [showChangeRegCategoryModal, setShowChangeRegCategoryModal] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [showActionsDropdown, setShowActionsDropdown] = useState(false);
  const [showTRSNoModal, setShowTRSNoModal] = useState(false);
  const [trSNoValue, setTRSNoValue] = useState('');
  const [savingTRSNo, setSavingTRSNo] = useState(false);
  const photoInputRef = useRef(null);
  const [showPhotoConfirm, setShowPhotoConfirm] = useState(null);

  // Load current user from localStorage
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setCurrentUser(user);
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  // Fetch candidate details
  const { data, isLoading, error } = useQuery({
    queryKey: ['candidate', id],
    queryFn: () => candidateApi.getById(id),
  });

  const candidate = data?.data;

  // Fetch enrollments
  const { data: enrollmentsData } = useQuery({
    queryKey: ['candidate-enrollments', id],
    queryFn: () => candidateApi.getEnrollments(id),
    enabled: !!id,
  });

  const enrollments = enrollmentsData?.data || [];

  const { data: activityData, isLoading: isActivityLoading } = useQuery({
    queryKey: ['candidate-activity', id],
    queryFn: () => candidateApi.getActivity(id),
    enabled: !!id && activeTab === 'activity',
  });

  const activities = activityData?.data || [];

  // De-enroll mutation
  const deEnrollMutation = useMutation({
    mutationFn: (enrollmentId) => candidateApi.deEnroll(id, enrollmentId),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate-enrollments', id]);
      queryClient.invalidateQueries(['candidate', id]);
      toast.success('Candidate de-enrolled successfully!');
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message;
      toast.error(errorMsg);
    },
  });

  const handleDeEnroll = (enrollmentId, seriesName) => {
    if (window.confirm(`Are you sure you want to de-enroll this candidate from "${seriesName}"? This will delete the enrollment and reset fees.`)) {
      deEnrollMutation.mutate(enrollmentId);
    }
  };

  // Verify mutation
  const verifyMutation = useMutation({
    mutationFn: () => candidateApi.verify(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate', id]);
      queryClient.invalidateQueries(['candidates']);
      const wasDeclined = candidate.verification_status === 'declined';
      toast.success(wasDeclined ? 'Candidate verified successfully! Previous decline has been overridden.' : 'Candidate verified successfully!');
    },
    onError: (error) => {
      toast.error(`Failed to verify candidate: ${error.message}`);
    },
  });

  // Decline mutation
  const declineMutation = useMutation({
    mutationFn: (reason) => candidateApi.decline(id, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate', id]);
      queryClient.invalidateQueries(['candidates']);
      const wasDeclined = candidate.verification_status === 'declined';
      toast.success(wasDeclined ? 'Decline reason updated successfully!' : 'Candidate declined successfully!');
      setShowDeclineModal(false);
      setDeclineReason('');
    },
    onError: (error) => {
      toast.error(`Failed to decline candidate: ${error.message}`);
    },
  });

  const handleVerify = () => {
    const message = candidate.verification_status === 'verified'
      ? 'This candidate is already verified. Do you want to re-verify them?'
      : candidate.verification_status === 'declined'
        ? 'This candidate was previously declined. Are you sure you want to verify them now?'
        : 'Are you sure you want to verify this candidate?';

    if (window.confirm(message)) {
      verifyMutation.mutate();
    }
  };

  const handleDecline = () => {
    if (!declineReason.trim()) {
      toast.error('Please provide a reason for declining');
      return;
    }
    declineMutation.mutate(declineReason);
  };

  // Submit mutation (for draft candidates)
  const submitMutation = useMutation({
    mutationFn: () => candidateApi.submit(id),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', id]);
      queryClient.invalidateQueries(['candidates']);
      toast.success(`Candidate submitted successfully! Registration Number: ${response.data.registration_number}`);
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.error || error.message;
      toast.error(`Failed to submit candidate: ${errorMsg}`);
    },
  });

  const handleSubmit = () => {
    if (window.confirm('Are you sure you want to submit this candidate? This will generate a registration number and the candidate cannot be edited as a draft anymore.')) {
      submitMutation.mutate();
    }
  };

  // Generate payment code mutation
  const generatePaymentCodeMutation = useMutation({
    mutationFn: () => candidateApi.generatePaymentCode(id),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', id]);
      queryClient.invalidateQueries(['candidates']);
      toast.success(`Payment code generated: ${response.data.payment_code}`);
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.error || error.message;
      toast.error(`Failed to generate payment code: ${errorMsg}`);
    },
  });

  const handleGeneratePaymentCode = () => {
    if (window.confirm('Generate payment code for this candidate?')) {
      generatePaymentCodeMutation.mutate();
    }
  };

  // Mark paid mutation
  const markPaidMutation = useMutation({
    mutationFn: () => candidateApi.markPaymentCleared(id),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', id]);
      queryClient.invalidateQueries(['candidates']);
      toast.success('Payment marked as cleared successfully!');
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.error || error.message;
      toast.error(`Failed to mark payment as cleared: ${errorMsg}`);
    },
  });

  const handleMarkPaid = () => {
    if (window.confirm('Mark this payment as cleared? This will set the amount due to 0.')) {
      markPaidMutation.mutate();
    }
  };

  // Photo upload mutation
  const uploadPhotoMutation = useMutation({
    mutationFn: (file) => candidateApi.uploadPhoto(id, file),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate', id]);
      toast.success('Photo updated successfully!');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to upload photo');
    },
  });

  // Photo delete mutation
  const deletePhotoMutation = useMutation({
    mutationFn: () => candidateApi.deletePhoto(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate', id]);
      toast.success('Photo deleted successfully!');
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to delete photo');
    },
  });

  const handlePhotoEdit = () => {
    setShowPhotoConfirm('edit');
  };

  const handlePhotoDelete = () => {
    setShowPhotoConfirm('delete');
  };

  const confirmPhotoAction = () => {
    if (showPhotoConfirm === 'edit') {
      photoInputRef.current?.click();
    } else if (showPhotoConfirm === 'delete') {
      deletePhotoMutation.mutate();
    }
    setShowPhotoConfirm(null);
  };

  const handlePhotoFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      uploadPhotoMutation.mutate(file);
    }
    e.target.value = '';
  };

  const handleTranscript = async () => {
    try {
      const url = candidateApi.getTranscriptPDF(id, candidate?.registration_category);
      const response = await fetch(url);

      if (!response.ok) {
        const data = await response.json();
        toast.error(data.error || 'Candidate does not qualify for transcript');
        return;
      }

      // If successful, open the PDF
      window.open(url, '_blank');
    } catch (error) {
      toast.error('Failed to generate transcript');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading candidate details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Error loading candidate: {error.message}</div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Candidate not found</div>
      </div>
    );
  }

  const tabs = [
    { id: 'bio-data', label: 'Bio Data' },
    { id: 'general-info', label: 'General Information' },
    { id: 'occupation-info', label: 'Occupation Information' },
    { id: 'documents', label: 'Documents' },
    { id: 'enrollment', label: 'Enrollment' },
    { id: 'results', label: 'Results' },
    { id: 'payment', label: 'Payment Information' },
    { id: 'activity', label: 'Activity Log' },
  ];

  const getStatusBadge = (status) => {
    const colors = {
      verified: 'bg-green-100 text-green-800',
      declined: 'bg-red-100 text-red-800',
      pending_verification: 'bg-yellow-100 text-yellow-800',
    };
    const labels = {
      verified: 'Verified',
      declined: 'Declined',
      pending_verification: 'Pending',
    };
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(fromAwards ? '/awards' : '/candidates')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {fromAwards ? 'Back to Awards' : 'Back to Candidates'}
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {candidate.full_name}
            </h1>
            <p className="text-sm mt-1">
              {candidate.is_submitted ? (
                <span className="text-gray-600">
                  Registration: {candidate.registration_number || 'Not assigned'}
                </span>
              ) : (
                <span className="text-orange-600 font-semibold">
                  ⚠ Draft - Not Submitted
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="md"
            onClick={() => window.open(candidateApi.getVerifiedResultsPDF(id, candidate?.registration_category), '_blank')}
          >
            <Download className="w-4 h-4 mr-2" />
            Verified Results
          </Button>
          {candidate?.registration_category !== 'workers_pas' && currentUser?.user_type !== 'center_representative' && (
            <Button
              variant="outline"
              size="md"
              onClick={handleTranscript}
            >
              <span className="mr-2">📄</span>
              Transcript
            </Button>
          )}
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate(`/candidates/${id}/edit`)}
          >
            <Edit className="w-4 h-4 mr-2" />
            Edit
          </Button>

          {/* Actions Dropdown */}
          <div className="relative">
            <Button
              variant="outline"
              size="md"
              onClick={() => setShowActionsDropdown(!showActionsDropdown)}
            >
              Actions
              <ChevronDown className="w-4 h-4 ml-2" />
            </Button>

            {showActionsDropdown && (
              <>
                {/* Backdrop to close dropdown */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowActionsDropdown(false)}
                />

                {/* Dropdown Menu */}
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                    onClick={() => {
                      setShowActionsDropdown(false);
                      setShowChangeSeriesModal(true);
                    }}
                  >
                    <Calendar className="w-4 h-4 mr-2" />
                    Change Assessment Series
                  </button>
                  {currentUser?.user_type !== 'center_representative' && (
                    <button
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                      onClick={() => {
                        setShowActionsDropdown(false);
                        setShowChangeCenterModal(true);
                      }}
                    >
                      <Building2 className="w-4 h-4 mr-2" />
                      Change Assessment Center
                    </button>
                  )}
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                    onClick={() => {
                      setShowActionsDropdown(false);
                      setShowChangeOccupationModal(true);
                    }}
                  >
                    <Briefcase className="w-4 h-4 mr-2" />
                    Change Occupation
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                    onClick={() => {
                      setShowActionsDropdown(false);
                      setShowChangeRegCategoryModal(true);
                    }}
                  >
                    <Tag className="w-4 h-4 mr-2" />
                    Change Registration Category
                  </button>
                  {currentUser?.user_type !== 'center_representative' && (
                    <>
                      <button
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                        onClick={() => {
                          setShowActionsDropdown(false);
                          setTRSNoValue(candidate.transcript_serial_number || '');
                          setShowTRSNoModal(true);
                        }}
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        Add TR SNo
                      </button>
                      <button
                        className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center"
                        onClick={async () => {
                          setShowActionsDropdown(false);
                          if (window.confirm(`Are you sure you want to clear ALL results, enrollments, and fees for ${candidate.full_name}? This action cannot be undone.`)) {
                            try {
                              const response = await candidateApi.clearData(id);
                              const { cleared } = response.data;
                              toast.success(`Cleared: ${cleared.modular_results + cleared.formal_results + cleared.workers_pas_results} results, ${cleared.enrollments} enrollments`);
                              queryClient.invalidateQueries(['candidate', id]);
                              queryClient.invalidateQueries(['candidate-enrollments', id]);
                            } catch (error) {
                              toast.error(error.response?.data?.error || 'Failed to clear data');
                            }
                          }
                        }}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Clear Results, Enrollments & Fees
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Profile Card */}
        <div className="lg:col-span-1">
          <Card>
            <Card.Content className="text-center py-6">
              {/* Profile Image */}
              <div className="relative inline-block group">
                <input
                  type="file"
                  ref={photoInputRef}
                  className="hidden"
                  accept="image/*"
                  onChange={handlePhotoFileChange}
                />
                {candidate.passport_photo ? (
                  <>
                    <img
                      src={candidate.passport_photo}
                      alt={candidate.full_name}
                      className="w-32 h-32 rounded-full object-cover mx-auto border-4 border-gray-200"
                    />
                    {/* Edit/Delete overlay */}
                    <div className="absolute inset-0 rounded-full flex items-center justify-center gap-2 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={handlePhotoEdit}
                        className="p-2 bg-white rounded-full shadow hover:bg-blue-50 transition-colors"
                        title="Change photo"
                        disabled={uploadPhotoMutation.isPending}
                      >
                        <Pencil className="w-4 h-4 text-blue-600" />
                      </button>
                      <button
                        onClick={handlePhotoDelete}
                        className="p-2 bg-white rounded-full shadow hover:bg-red-50 transition-colors"
                        title="Delete photo"
                        disabled={deletePhotoMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  </>
                ) : (
                  <div
                    className="w-32 h-32 rounded-full bg-primary-100 flex items-center justify-center mx-auto border-4 border-gray-200 cursor-pointer hover:bg-primary-200 transition-colors"
                    onClick={() => setShowPhotoConfirm('upload')}
                    title="Upload photo"
                  >
                    <span className="text-4xl font-bold text-primary-600">
                      {candidate.full_name?.charAt(0) || '?'}
                    </span>
                  </div>
                )}
                {/* Verification Badge */}
                {candidate.verification_status === 'verified' && (
                  <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
                    <span className="bg-green-500 text-white text-xs px-3 py-1 rounded-full font-medium">
                      VERIFIED
                    </span>
                  </div>
                )}
              </div>

              {/* Photo confirmation modal */}
              {showPhotoConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                  <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {showPhotoConfirm === 'delete' ? 'Delete Photo' : showPhotoConfirm === 'edit' ? 'Change Photo' : 'Upload Photo'}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {showPhotoConfirm === 'delete'
                        ? 'Are you sure you want to delete this photo? This action cannot be undone.'
                        : showPhotoConfirm === 'edit'
                          ? 'Are you sure you want to replace the current photo with a new one?'
                          : 'Would you like to upload a photo for this candidate?'}
                    </p>
                    <div className="flex justify-end gap-3">
                      <button
                        onClick={() => setShowPhotoConfirm(null)}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={showPhotoConfirm === 'upload' ? () => { setShowPhotoConfirm(null); photoInputRef.current?.click(); } : confirmPhotoAction}
                        className={`px-4 py-2 text-sm font-medium text-white rounded-lg ${
                          showPhotoConfirm === 'delete' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                      >
                        {showPhotoConfirm === 'delete' ? 'Delete' : 'Continue'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <h2 className="text-xl font-bold text-gray-900 mt-4">
                {candidate.full_name}
              </h2>
              <p className="text-sm">
                {candidate.is_submitted ? (
                  <span className="text-gray-600">
                    {candidate.registration_number || 'No Registration Number'}
                  </span>
                ) : (
                  <span className="text-orange-600 font-semibold">
                    Draft - Not Submitted
                  </span>
                )}
              </p>

              <div className="mt-4">
                {candidate.is_submitted ? (
                  getStatusBadge(candidate.verification_status)
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-orange-100 text-orange-800">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    Pending Submission
                  </span>
                )}
              </div>

              {/* Candidate Fees */}
              <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="text-xs text-gray-600 mb-1">Candidate Fees</div>
                <div className="text-lg font-bold text-green-600">
                  UGX {enrollments.reduce((sum, e) => sum + parseFloat(e.total_amount || 0), 0).toLocaleString()}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="mt-6 pt-6 border-t space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Gender</span>
                  <span className="font-medium text-gray-900 capitalize">
                    {candidate.gender}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Date of Birth</span>
                  <span className="font-medium text-gray-900">
                    {formatDate(candidate.date_of_birth)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Age</span>
                  <span className="font-medium text-gray-900">
                    {candidate.age || 'N/A'} years
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Nationality</span>
                  <span className="font-medium text-gray-900">
                    {candidate.nationality_display || candidate.nationality}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Transcript Serial No</span>
                  <span className="font-medium text-gray-900">
                    {candidate.transcript_serial_number || '-'}
                  </span>
                </div>
                {candidate.is_refugee && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Refugee Number</span>
                    <span className="font-medium text-gray-900">
                      {candidate.refugee_number}
                    </span>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="mt-6 pt-6 border-t space-y-2">
                {/* Submit button - only for draft candidates */}
                {!candidate.is_submitted && (
                  <Button
                    variant="primary"
                    size="md"
                    className="w-full"
                    onClick={handleSubmit}
                    loading={submitMutation.isPending}
                    disabled={submitMutation.isPending}
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Submit Candidate
                  </Button>
                )}

                {/* Verify button - only for submitted candidates and NOT for center representatives */}
                {candidate.is_submitted && currentUser?.user_type !== 'center_representative' && (
                  <Button
                    variant="success"
                    size="md"
                    className="w-full"
                    onClick={handleVerify}
                    loading={verifyMutation.isPending}
                    disabled={verifyMutation.isPending}
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    {candidate.verification_status === 'verified' ? 'Re-verify Candidate' : 'Verify Candidate'}
                  </Button>
                )}

                {/* Decline button - NOT available for center representatives */}
                {currentUser?.user_type !== 'center_representative' && (
                  <Button
                    variant="danger"
                    size="md"
                    className="w-full"
                    onClick={() => setShowDeclineModal(true)}
                    disabled={declineMutation.isPending}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    {candidate.verification_status === 'declined' ? 'Update Decline Reason' : 'Decline Candidate'}
                  </Button>
                )}

                {/* Clear Payment button - NOT available for center representatives */}
                {!candidate.payment_cleared && currentUser?.user_type !== 'center_representative' && (
                  <Button variant="primary" size="md" className="w-full">
                    <CreditCard className="w-4 h-4 mr-2" />
                    Clear Payment
                  </Button>
                )}

                {/* Generate Payment Code button - only for submitted candidates without payment code */}
                {candidate.is_submitted && candidate.registration_number && !candidate.payment_code && (
                  <Button
                    variant="primary"
                    size="md"
                    className="w-full"
                    onClick={handleGeneratePaymentCode}
                    loading={generatePaymentCodeMutation.isPending}
                    disabled={generatePaymentCodeMutation.isPending}
                  >
                    <CreditCard className="w-4 h-4 mr-2" />
                    Generate Payment Code
                  </Button>
                )}

                <Button
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => candidate.passport_photo ? handlePhotoEdit() : setShowPhotoConfirm('upload')}
                  loading={uploadPhotoMutation.isPending}
                  disabled={uploadPhotoMutation.isPending}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {candidate.passport_photo ? 'Change Photo' : 'Upload Photo'}
                </Button>
              </div>
            </Card.Content>
          </Card>

          {/* Alerts */}
          {candidate.has_disability && (
            <Card className="mt-4">
              <Card.Content className="py-4">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      Has Disability
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {candidate.nature_of_disability_detail?.name || 'Not specified'}
                    </p>
                    {candidate.disability_specification && (
                      <p className="text-xs text-gray-500 mt-1">
                        {candidate.disability_specification}
                      </p>
                    )}
                  </div>
                </div>
              </Card.Content>
            </Card>
          )}

          {candidate.is_refugee && (
            <Card className="mt-4">
              <Card.Content className="py-4">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      Refugee Status
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Refugee Number: {candidate.refugee_number}
                    </p>
                  </div>
                </div>
              </Card.Content>
            </Card>
          )}

          {/* Declined Alert */}
          {candidate.verification_status === 'declined' && candidate.decline_reason && (
            <Card className="mt-4 border-red-200 bg-red-50">
              <Card.Content className="py-4">
                <div className="flex items-start space-x-3">
                  <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-red-900">
                      Application Declined
                    </h4>
                    <p className="text-sm text-red-700 mt-1">
                      {candidate.decline_reason}
                    </p>
                    {candidate.declined_at && (
                      <p className="text-xs text-red-600 mt-2">
                        Declined on {formatDate(candidate.declined_at)}
                        {candidate.declined_by_name && ` by ${candidate.declined_by_name}`}
                      </p>
                    )}
                  </div>
                </div>
              </Card.Content>
            </Card>
          )}
        </div>

        {/* Right Column - Detailed Information */}
        <div className="lg:col-span-2">
          {/* Tabs */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id
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
              {/* Bio Data Tab */}
              {activeTab === 'bio-data' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Personal Information
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem label="Full Name" value={candidate.full_name} />
                      <InfoItem label="Gender" value={candidate.gender} />
                      <InfoItem label="Date of Birth" value={formatDate(candidate.date_of_birth)} />
                      <InfoItem label="Age" value={`${candidate.age || 'N/A'} years`} />
                      <InfoItem label="Nationality" value={candidate.nationality_display || candidate.nationality} />
                      <InfoItem
                        label="Candidate Fees"
                        value={
                          <span className={enrollments.length > 0 ? 'text-green-600 font-semibold' : 'text-gray-600'}>
                            UGX {enrollments.reduce((sum, e) => sum + parseFloat(e.total_amount || 0), 0).toLocaleString()}
                          </span>
                        }
                      />
                      <InfoItem label="Contact" value={candidate.contact} />
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Location Information
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem label="District" value={candidate.district_detail?.name} />
                      <InfoItem label="Village" value={candidate.village_detail?.name} />
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Special Considerations
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem
                        label="Refugee Status"
                        value={candidate.is_refugee ? 'Yes' : 'No'}
                      />
                      {candidate.is_refugee && (
                        <InfoItem label="Refugee Number" value={candidate.refugee_number} />
                      )}
                      <InfoItem
                        label="Has Disability"
                        value={candidate.has_disability ? 'Yes' : 'No'}
                      />
                      {candidate.has_disability && (
                        <InfoItem
                          label="Nature of Disability"
                          value={candidate.nature_of_disability_detail?.name}
                        />
                      )}
                    </div>
                    {candidate.disability_specification && (
                      <div className="mt-4">
                        <InfoItem
                          label="Disability Specification"
                          value={candidate.disability_specification}
                          fullWidth
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* General Information Tab */}
              {activeTab === 'general-info' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Registration Details
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem
                        label="Registration Number"
                        value={candidate.registration_number}
                      />
                      <InfoItem
                        label="Payment Code"
                        value={candidate.payment_code}
                      />
                      <InfoItem
                        label="Registration Category"
                        value={candidate.registration_category}
                      />
                      <InfoItem label="Entry Year" value={candidate.entry_year} />
                      <InfoItem
                        label="Assessment Intake"
                        value={
                          candidate.intake === 'M'
                            ? 'March'
                            : candidate.intake === 'J'
                              ? 'June'
                              : candidate.intake === 'S'
                                ? 'September'
                                : candidate.intake === 'D'
                                  ? 'December'
                                  : candidate.intake === 'A'
                                    ? 'August'
                                    : candidate.intake
                        }
                      />
                      <InfoItem label="Status" value={candidate.status} />
                      <InfoItem
                        label="Verification Status"
                        value={candidate.verification_status}
                      />
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Assessment Center
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem
                        label="Center Name"
                        value={candidate.assessment_center_detail?.center_name}
                      />
                      <InfoItem
                        label="Center Number"
                        value={candidate.assessment_center_detail?.center_number}
                      />
                      <InfoItem
                        label="Branch Code"
                        value={candidate.assessment_center_branch_detail?.branch_code || candidate.assessment_center_branch_detail?.branch_name}
                      />
                      <InfoItem
                        label="Category"
                        value={candidate.assessment_center_detail?.assessment_category}
                      />
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Audit Information
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem label="Created By" value={candidate.created_by_name} />
                      <InfoItem label="Created At" value={formatDate(candidate.created_at)} />
                      <InfoItem label="Updated By" value={candidate.updated_by_name} />
                      <InfoItem label="Updated At" value={formatDate(candidate.updated_at)} />
                      {candidate.verified_by_name && (
                        <>
                          <InfoItem label="Verified By" value={candidate.verified_by_name} />
                          <InfoItem label="Verified At" value={formatDate(candidate.verification_date)} />
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Occupation Information Tab */}
              {activeTab === 'occupation-info' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Occupation Details
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem
                        label="Occupation Code"
                        value={candidate.occupation_detail?.occ_code}
                      />
                      <InfoItem
                        label="Occupation Name"
                        value={candidate.occupation_detail?.occ_name}
                      />
                      <InfoItem
                        label="Sector"
                        value={candidate.occupation_detail?.sector?.name}
                      />
                      <InfoItem
                        label="Enrollment Level"
                        value={candidate.enrollment_level}
                      />
                    </div>
                  </div>

                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Assessment Dates
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem label="Start Date" value={formatDate(candidate.start_date)} />
                      <InfoItem label="Finish Date" value={formatDate(candidate.finish_date)} />
                      <InfoItem label="Assessment Date" value={formatDate(candidate.assessment_date)} />
                      <InfoItem
                        label="Preferred Language"
                        value={candidate.preferred_assessment_language}
                      />
                    </div>
                  </div>

                  {candidate.registration_category === 'modular' && (
                    <div className="border-t pt-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Modular Information
                      </h3>
                      <div className="grid grid-cols-2 gap-4">
                        <InfoItem
                          label="Module Count"
                          value={candidate.modular_module_count}
                        />
                        <InfoItem
                          label="Billing Amount"
                          value={candidate.modular_billing_amount ? `UGX ${candidate.modular_billing_amount}` : 'N/A'}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Enrollment Tab */}
              {activeTab === 'enrollment' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Enrollment Information
                    </h3>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setShowEnrollmentModal(true)}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Enroll
                    </Button>
                  </div>

                  {enrollments.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 rounded-lg">
                      <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-gray-600 mb-4">No enrollments yet</p>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setShowEnrollmentModal(true)}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Enroll Candidate
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {enrollments.map((enrollment) => (
                        <Card key={enrollment.id}>
                          <Card.Content className="p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-3 mb-2">
                                  <h4 className="font-semibold text-gray-900">
                                    {enrollment.assessment_series_name}
                                  </h4>
                                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${enrollment.is_active
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                    }`}>
                                    {enrollment.is_active ? 'Active' : 'Inactive'}
                                  </span>
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="text-gray-500">Occupation:</span>
                                    <span className="ml-2 font-medium">{enrollment.occupation_name}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-500">Level:</span>
                                    <span className="ml-2 font-medium">{enrollment.level_name}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-500">Total Amount:</span>
                                    <span className="ml-2 font-medium text-green-600">
                                      UGX {parseFloat(enrollment.total_amount).toLocaleString()}
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-gray-500">Enrolled:</span>
                                    <span className="ml-2 font-medium">{formatDate(enrollment.enrolled_at)}</span>
                                  </div>
                                </div>

                                {/* Modules */}
                                {enrollment.modules && enrollment.modules.length > 0 && (
                                  <div className="mt-3">
                                    <span className="text-sm font-medium text-gray-700">Modules:</span>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                      {enrollment.modules.map((module) => (
                                        <span
                                          key={module.id}
                                          className="inline-flex px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                                          title={module.module_name}
                                        >
                                          {module.module_code} - {module.module_name}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Papers */}
                                {enrollment.papers && enrollment.papers.length > 0 && (
                                  <div className="mt-3">
                                    <span className="text-sm font-medium text-gray-700">Papers:</span>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                      {enrollment.papers.map((paper) => (
                                        <span
                                          key={paper.id}
                                          className="inline-flex px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded"
                                        >
                                          {paper.paper_code}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* De-enroll Button */}
                              <div className="ml-4">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleDeEnroll(enrollment.id, enrollment.assessment_series_name)}
                                  loading={deEnrollMutation.isPending}
                                  className="text-red-600 hover:text-red-700 hover:border-red-600"
                                >
                                  <Trash2 className="w-4 h-4 mr-2" />
                                  De-enroll
                                </Button>
                              </div>
                            </div>
                          </Card.Content>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Results Tab */}
              {activeTab === 'results' && (
                <CandidateResults
                  candidateId={id}
                  registrationCategory={candidate.registration_category}
                  hasEnrollments={enrollments && enrollments.length > 0}
                  enrollments={enrollments}
                />
              )}

              {/* Documents Tab */}
              {activeTab === 'documents' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Uploaded Documents
                  </h3>

                  <DocumentItem
                    label="Passport Photo"
                    file={candidate.passport_photo}
                    type="image"
                  />
                  <DocumentItem
                    label="Passport Photo with Reg No"
                    file={candidate.passport_photo_with_regno}
                    type="image"
                  />
                  <DocumentItem
                    label="Identification Document"
                    file={candidate.identification_document}
                    type="file"
                  />
                  <DocumentItem
                    label="Qualification Document"
                    file={candidate.qualification_document}
                    type="file"
                  />
                </div>
              )}

              {/* Payment Information Tab */}
              {activeTab === 'payment' && (
                <div className="space-y-6">
                  {/* Billing Information */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Billing Information
                    </h3>
                    {enrollments && enrollments.length > 0 ? (
                      <div className="space-y-4">
                        {enrollments.map((enrollment) => (
                          <div key={enrollment.id} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                            <div className="grid grid-cols-2 gap-4">
                              <InfoItem
                                label="Assessment Series"
                                value={enrollment.assessment_series_name}
                              />
                              <InfoItem
                                label="Level Enrolled"
                                value={enrollment.level_name}
                              />
                              <InfoItem
                                label="Amount"
                                value={`UGX ${parseFloat(enrollment.total_amount).toLocaleString()}`}
                              />
                              <InfoItem
                                label="Enrolled Date"
                                value={formatDate(enrollment.enrolled_at)}
                              />
                            </div>
                          </div>
                        ))}
                        {/* Payment Summary */}
                        <div className="pt-4 border-t border-gray-300 space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-lg font-semibold text-gray-900">Total Billed:</span>
                            <span className="text-xl font-bold text-primary-600">
                              UGX {enrollments.reduce((sum, e) => sum + parseFloat(e.total_amount || 0), 0).toLocaleString()}
                            </span>
                          </div>

                          {candidate.payment_amount_cleared > 0 && (
                            <div className="flex justify-between items-center">
                              <span className="text-lg font-semibold text-gray-900">Amount Paid:</span>
                              <span className="text-xl font-bold text-green-600">
                                UGX {parseFloat(candidate.payment_amount_cleared || 0).toLocaleString()}
                              </span>
                            </div>
                          )}

                          <div className="flex justify-between items-center pt-2 border-t border-gray-200">
                            <span className="text-lg font-semibold text-gray-900">Amount Due:</span>
                            <span className={`text-xl font-bold ${candidate.payment_cleared ? 'text-green-600' : 'text-red-600'
                              }`}>
                              UGX {(
                                enrollments.reduce((sum, e) => sum + parseFloat(e.total_amount || 0), 0) -
                                parseFloat(candidate.payment_amount_cleared || 0)
                              ).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">No billing information available</p>
                    )}
                  </div>

                  {/* Payment Status & Actions */}
                  <div>
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Payment Status
                      </h3>
                      {!candidate.payment_cleared && candidate.payment_amount_cleared > 0 && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={handleMarkPaid}
                          loading={markPaidMutation.isPending}
                          disabled={markPaidMutation.isPending}
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Mark Paid
                        </Button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <InfoItem
                        label="Payment Cleared"
                        value={candidate.payment_cleared ? 'Yes' : 'No'}
                      />
                      {candidate.payment_cleared && (
                        <>
                          <InfoItem
                            label="Amount Cleared"
                            value={candidate.payment_amount_cleared ? `UGX ${parseFloat(candidate.payment_amount_cleared).toLocaleString()}` : 'N/A'}
                          />
                          <InfoItem
                            label="Cleared Date"
                            value={formatDate(candidate.payment_cleared_date)}
                          />
                          <InfoItem
                            label="Cleared By"
                            value={candidate.payment_cleared_by}
                          />
                          <InfoItem
                            label="Reference"
                            value={candidate.payment_center_series_ref}
                          />
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Activity Log Tab */}
              {activeTab === 'activity' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Recent Activity
                  </h3>
                  {isActivityLoading ? (
                    <div className="text-gray-600 text-sm">Loading activity...</div>
                  ) : activities.length === 0 ? (
                    <div className="text-gray-600 text-sm">No activity yet.</div>
                  ) : (
                    <div className="space-y-3">
                      {activities.map((a) => (
                        <div key={a.id} className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="text-sm font-medium text-gray-900 truncate">
                                {a.description || a.action}
                              </div>
                              <div className="text-xs text-gray-600 mt-1">
                                {(a.actor_name || 'System')}{a.actor_user_type ? ` (${a.actor_user_type})` : ''}
                              </div>
                              {a.details && Object.keys(a.details).length > 0 && (
                                <pre className="mt-2 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded p-2 overflow-auto">{JSON.stringify(a.details, null, 2)}</pre>
                              )}
                            </div>
                            <div className="text-xs text-gray-500 whitespace-nowrap">
                              {a.created_at ? new Date(a.created_at).toLocaleString() : ''}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Decline Modal */}
      {showDeclineModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {candidate.verification_status === 'declined' ? 'Update Decline Reason' : 'Decline Candidate'}
              </h3>
              <button
                onClick={() => {
                  setShowDeclineModal(false);
                  setDeclineReason('');
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              {candidate.verification_status === 'declined'
                ? 'Update the decline reason. This will be visible to the candidate so they can rectify the issues.'
                : 'Please provide a reason for declining this candidate. This will be visible to the candidate so they can rectify the issues.'
              }
            </p>

            {candidate.verification_status === 'declined' && candidate.decline_reason && (
              <div className="mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Current reason:</p>
                <p className="text-sm text-gray-700">{candidate.decline_reason}</p>
              </div>
            )}

            <textarea
              value={declineReason}
              onChange={(e) => setDeclineReason(e.target.value)}
              placeholder={candidate.verification_status === 'declined' ? 'Enter new decline reason...' : 'Enter decline reason...'}
              rows="4"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
            />

            <div className="flex items-center justify-end space-x-3 mt-4">
              <Button
                variant="outline"
                size="md"
                onClick={() => {
                  setShowDeclineModal(false);
                  setDeclineReason('');
                }}
                disabled={declineMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="md"
                onClick={handleDecline}
                loading={declineMutation.isPending}
                disabled={declineMutation.isPending || !declineReason.trim()}
              >
                {candidate.verification_status === 'declined' ? 'Update Reason' : 'Decline Candidate'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Enrollment Modal */}
      {showEnrollmentModal && candidate && (
        <EnrollmentModal
          candidate={candidate}
          onClose={() => setShowEnrollmentModal(false)}
        />
      )}

      {/* Change Series Modal */}
      {showChangeSeriesModal && candidate && (
        <ChangeSeriesModal
          candidate={candidate}
          onClose={() => setShowChangeSeriesModal(false)}
        />
      )}

      {/* Change Center Modal */}
      {showChangeCenterModal && candidate && (
        <ChangeCenterModal
          candidate={candidate}
          onClose={() => setShowChangeCenterModal(false)}
        />
      )}

      {/* Change Occupation Modal */}
      {showChangeOccupationModal && candidate && (
        <ChangeOccupationModal
          candidate={candidate}
          onClose={() => setShowChangeOccupationModal(false)}
        />
      )}

      {/* Change Registration Category Modal */}
      {showChangeRegCategoryModal && candidate && (
        <ChangeRegCategoryModal
          candidate={candidate}
          onClose={() => setShowChangeRegCategoryModal(false)}
        />
      )}

      {/* TR SNo Modal */}
      {showTRSNoModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setShowTRSNoModal(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {candidate.transcript_serial_number ? 'Update' : 'Add'} Transcript Serial Number
              </h3>
              <button
                onClick={() => setShowTRSNoModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                TR SNo (Numbers only)
              </label>
              <input
                type="text"
                value={trSNoValue}
                onChange={(e) => {
                  const value = e.target.value.replace(/[^0-9]/g, '');
                  setTRSNoValue(value);
                }}
                placeholder="Enter transcript serial number"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowTRSNoModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!trSNoValue.trim()) {
                    toast.error('Please enter a transcript serial number');
                    return;
                  }
                  try {
                    setSavingTRSNo(true);
                    await candidateApi.patch(id, { transcript_serial_number: trSNoValue });
                    toast.success('Transcript serial number updated successfully');
                    queryClient.invalidateQueries(['candidate', id]);
                    setShowTRSNoModal(false);
                  } catch (error) {
                    toast.error(error.response?.data?.transcript_serial_number?.[0] || 'Failed to update transcript serial number');
                  } finally {
                    setSavingTRSNo(false);
                  }
                }}
                disabled={savingTRSNo}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {savingTRSNo ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper Components
const InfoItem = ({ label, value, fullWidth = false }) => (
  <div className={fullWidth ? 'col-span-2' : ''}>
    <dt className="text-sm font-medium text-gray-500">{label}</dt>
    <dd className="mt-1 text-sm text-gray-900">
      {value || <span className="text-gray-400">Not provided</span>}
    </dd>
  </div>
);

const DocumentItem = ({ label, file, type }) => (
  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
    <div className="flex items-center space-x-3">
      <FileText className="w-5 h-5 text-gray-400" />
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {file ? (
          <p className="text-xs text-gray-500">Uploaded</p>
        ) : (
          <p className="text-xs text-gray-400">Not uploaded</p>
        )}
      </div>
    </div>
    {file && (
      <div className="flex items-center space-x-2">
        <a
          href={file}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-600 hover:text-primary-700"
        >
          <Button variant="outline" size="sm">
            <Eye className="w-4 h-4 mr-2" />
            View
          </Button>
        </a>
        <a href={file} download>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4" />
          </Button>
        </a>
      </div>
    )}
  </div>
);

export default CandidateView;
