import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  GraduationCap, 
  FileText, 
  ClipboardList, 
  LogOut, 
  CheckCircle, 
  Clock,
  MapPin,
  Phone,
  Mail,
  Calendar,
  Building
} from 'lucide-react';
import apiClient from '../services/apiClient';

const CandidatePortal = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('bio');
  const [candidateData, setCandidateData] = useState(null);
  const [portalData, setPortalData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const storedCandidate = localStorage.getItem('candidateData');
    if (!storedCandidate) {
      navigate('/candidate-login');
      return;
    }

    const candidate = JSON.parse(storedCandidate);
    setCandidateData(candidate);

    // Fetch full portal data
    fetchPortalData(candidate.registration_number);
  }, [navigate]);

  const fetchPortalData = async (regNo) => {
    try {
      const response = await apiClient.get(`/candidates/candidate-portal/${regNo}/`);
      setPortalData(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load your data. Please try again.');
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('candidateToken');
    localStorage.removeItem('candidateData');
    navigate('/candidate-login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your portal...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/candidate-login')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'bio', label: 'Bio Data', icon: User },
    { id: 'occupation', label: 'Occupation', icon: GraduationCap },
    { id: 'enrollments', label: 'Enrollments', icon: ClipboardList },
    { id: 'results', label: 'Results', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img
              src="/uvtab-logo.png"
              alt="UVTAB Logo"
              className="w-12 h-12 object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-gray-800">Candidate Portal</h1>
              <p className="text-sm text-gray-500">Uganda Vocational & Technical Assessment Board</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-medium text-gray-800">{candidateData?.full_name}</p>
              <p className="text-sm text-gray-500">{candidateData?.registration_number}</p>
            </div>
            {candidateData?.photo && (
              <img
                src={candidateData.photo}
                alt="Profile"
                className="w-10 h-10 rounded-full object-cover border-2 border-gray-200"
              />
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-gray-600 hover:text-red-600 transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Status Banner */}
      <div className={`py-2 px-4 text-center text-sm font-medium ${
        portalData?.is_verified 
          ? 'bg-green-100 text-green-800' 
          : 'bg-yellow-100 text-yellow-800'
      }`}>
        {portalData?.is_verified ? (
          <span className="flex items-center justify-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Your registration is verified
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <Clock className="w-4 h-4" />
            Your registration is pending verification
          </span>
        )}
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="flex border-b overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          {/* Bio Data Tab */}
          {activeTab === 'bio' && portalData?.bio_data && (
            <div className="space-y-6">
              {/* Photo and Name Header */}
              <div className="flex items-center gap-6 pb-4 border-b">
                {portalData.bio_data.photo ? (
                  <img
                    src={portalData.bio_data.photo}
                    alt="Candidate Photo"
                    className="w-24 h-24 rounded-lg object-cover border-2 border-gray-200 shadow-sm"
                  />
                ) : (
                  <div className="w-24 h-24 rounded-lg bg-gray-100 flex items-center justify-center border-2 border-gray-200">
                    <User className="w-12 h-12 text-gray-400" />
                  </div>
                )}
                <div>
                  <h2 className="text-xl font-bold text-gray-800">{portalData.bio_data.full_name}</h2>
                  <p className="text-sm text-gray-500">{portalData.bio_data.registration_number}</p>
                  <p className="text-sm text-blue-600 font-medium">Payment Code: {portalData.bio_data.payment_code}</p>
                </div>
              </div>

              <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Personal Information</h2>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <InfoItem icon={User} label="Full Name" value={portalData.bio_data.full_name} />
                <InfoItem icon={FileText} label="Registration Number" value={portalData.bio_data.registration_number} />
                <InfoItem icon={FileText} label="Payment Code" value={portalData.bio_data.payment_code} />
                <InfoItem icon={User} label="Gender" value={portalData.bio_data.gender} />
                <InfoItem icon={Calendar} label="Date of Birth" value={portalData.bio_data.date_of_birth} />
                <InfoItem icon={MapPin} label="Nationality" value={portalData.bio_data.nationality} />
              </div>

              <h2 className="text-lg font-semibold text-gray-800 border-b pb-2 mt-8">Contact & Location</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <InfoItem icon={Phone} label="Contact" value={portalData.bio_data.contact || 'Not provided'} />
                <InfoItem icon={MapPin} label="District" value={portalData.bio_data.district || 'Not provided'} />
                <InfoItem icon={MapPin} label="Village" value={portalData.bio_data.village || 'Not provided'} />
              </div>

              <h2 className="text-lg font-semibold text-gray-800 border-b pb-2 mt-8">Additional Information</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <InfoItem 
                  icon={User} 
                  label="Refugee Status" 
                  value={portalData.bio_data.is_refugee ? 'Yes' : 'No'} 
                />
                {portalData.bio_data.is_refugee && (
                  <InfoItem icon={FileText} label="Refugee Number" value={portalData.bio_data.refugee_number || 'Not provided'} />
                )}
                <InfoItem 
                  icon={User} 
                  label="Disability Status" 
                  value={portalData.bio_data.has_disability ? 'Yes' : 'No'} 
                />
                {portalData.bio_data.has_disability && (
                  <InfoItem icon={User} label="Disability" value={portalData.bio_data.disability || 'Not specified'} />
                )}
              </div>
            </div>
          )}

          {/* Occupation Tab */}
          {activeTab === 'occupation' && portalData?.occupation_info && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Occupation & Assessment Information</h2>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <InfoItem icon={GraduationCap} label="Registration Category" value={portalData.occupation_info.registration_category} />
                <InfoItem icon={GraduationCap} label="Occupation" value={portalData.occupation_info.occupation} />
                <InfoItem icon={FileText} label="Occupation Code" value={portalData.occupation_info.occupation_code} />
                <InfoItem icon={Building} label="Assessment Center" value={portalData.occupation_info.assessment_center} />
                <InfoItem icon={Calendar} label="Entry Year" value={portalData.occupation_info.entry_year} />
                <InfoItem icon={Calendar} label="Intake" value={portalData.occupation_info.intake} />
                <InfoItem icon={FileText} label="Preferred Language" value={portalData.occupation_info.preferred_language} />
              </div>
            </div>
          )}

          {/* Enrollments Tab */}
          {activeTab === 'enrollments' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Assessment Enrollments</h2>
              
              {portalData?.enrollments?.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Assessment Series</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Level</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Enrolled Date</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Fee</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {portalData.enrollments.map((enrollment, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-800">{enrollment.assessment_series}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{enrollment.level || 'N/A'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {new Date(enrollment.enrolled_date).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            UGX {enrollment.total_amount.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <ClipboardList className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No enrollments found</p>
                </div>
              )}
            </div>
          )}

          {/* Results Tab */}
          {activeTab === 'results' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Assessment Results</h2>
              <p className="text-sm text-gray-500 mb-4">
                Results are only displayed after official release by UVTAB.
              </p>
              
              {portalData?.results?.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Assessment Series</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Subject</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Type</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Grade</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Remark</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {portalData.results.map((result, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-800">{result.assessment_series}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {result.module || result.exam_or_paper || result.paper || 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{result.type}</td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              result.mark_status === 'Uploaded' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {result.mark_status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-800">{result.grade || '-'}</td>
                          <td className="px-4 py-3">
                            <span className={`text-sm font-medium ${
                              result.comment === 'Successful' 
                                ? 'text-green-600' 
                                : 'text-red-600'
                            }`}>
                              {result.comment || '-'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No results available yet</p>
                  <p className="text-sm mt-2">Results will appear here after they are officially released</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-8 py-4 text-center text-sm text-gray-500">
        © Uganda Vocational & Technical Assessment Board | Education Management Information System
      </footer>
    </div>
  );
};

const InfoItem = ({ icon: Icon, label, value }) => (
  <div className="flex items-start gap-3">
    <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
      <Icon className="w-5 h-5 text-blue-600" />
    </div>
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="font-medium text-gray-800">{value || 'Not provided'}</p>
    </div>
  </div>
);

export default CandidatePortal;
