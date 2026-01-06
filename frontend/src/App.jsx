import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from '@layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import CandidateList from '@modules/candidates/pages/CandidateList';
import CandidateView from '@modules/candidates/pages/CandidateView';
import CandidateEdit from '@modules/candidates/pages/CandidateEdit';
import CandidateCreate from '@modules/candidates/pages/CandidateCreate';
import OccupationList from '@modules/occupations/pages/OccupationList';
import OccupationView from '@modules/occupations/pages/OccupationView';
import OccupationEdit from '@modules/occupations/pages/OccupationEdit';
import OccupationCreate from '@modules/occupations/pages/OccupationCreate';
import ModuleCreate from '@modules/occupations/pages/ModuleCreate';
import ModuleEdit from '@modules/occupations/pages/ModuleEdit';
import PaperCreate from '@modules/occupations/pages/PaperCreate';
import PaperEdit from '@modules/occupations/pages/PaperEdit';
import AssessmentCenterList from '@modules/assessment-centers/pages/AssessmentCenterList';
import AssessmentCenterView from '@modules/assessment-centers/pages/AssessmentCenterView';
import AssessmentCenterEdit from '@modules/assessment-centers/pages/AssessmentCenterEdit';
import AssessmentCenterCreate from '@modules/assessment-centers/pages/AssessmentCenterCreate';
import BranchEdit from '@modules/assessment-centers/pages/BranchEdit';
import AssessmentSeriesList from '@modules/assessment-series/pages/AssessmentSeriesList';
import AssessmentSeriesView from '@modules/assessment-series/pages/AssessmentSeriesView';
import AssessmentSeriesEdit from '@modules/assessment-series/pages/AssessmentSeriesEdit';
import AssessmentSeriesCreate from '@modules/assessment-series/pages/AssessmentSeriesCreate';
import UsersIndex from '@modules/users/pages/UsersIndex';
import StaffList from '@modules/users/staff/pages/StaffList';
import StaffView from '@modules/users/staff/pages/StaffView';
import StaffEdit from '@modules/users/staff/pages/StaffEdit';
import SupportStaffList from '@modules/users/support-staff/pages/SupportStaffList';
import SupportStaffView from '@modules/users/support-staff/pages/SupportStaffView';
import SupportStaffEdit from '@modules/users/support-staff/pages/SupportStaffEdit';
import CenterRepresentativeList from '@modules/users/center-representatives/pages/CenterRepresentativeList';
import CenterRepresentativeView from '@modules/users/center-representatives/pages/CenterRepresentativeView';
import CenterRepresentativeEdit from '@modules/users/center-representatives/pages/CenterRepresentativeEdit';
import ReportsIndex from '@modules/reports/pages/ReportsIndex';
import Albums from '@modules/reports/pages/Albums';
import ResultLists from '@modules/reports/pages/ResultLists';
import FeesModule from '@modules/fees';
import MarksheetsModule from '@modules/marksheets';
import ComplaintsList from '@modules/complaints/pages/ComplaintsList';
import ComplaintDetail from '@modules/complaints/pages/ComplaintDetail';
import CreateComplaint from '@modules/complaints/pages/CreateComplaint';
import StatisticsDashboard from '@modules/statistics/pages/StatisticsDashboard';
import SeriesStatistics from '@modules/statistics/pages/SeriesStatistics';

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      
      {/* Dashboard - Full screen without sidebar */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      
      {/* Protected routes with sidebar layout */}
      <Route path="/" element={<DashboardLayout />}>
        {/* Candidate routes */}
        <Route path="candidates" element={<CandidateList />} />
        <Route path="candidates/new" element={<CandidateCreate />} />
        <Route path="candidates/:id" element={<CandidateView />} />
        <Route path="candidates/:id/edit" element={<CandidateEdit />} />
        
        {/* Occupation routes */}
        <Route path="occupations" element={<OccupationList />} />
        <Route path="occupations/new" element={<OccupationCreate />} />
        <Route path="occupations/:id" element={<OccupationView />} />
        <Route path="occupations/:id/edit" element={<OccupationEdit />} />
        <Route path="occupations/:occupationId/modules/new" element={<ModuleCreate />} />
        <Route path="occupations/modules/:id/edit" element={<ModuleEdit />} />
        <Route path="occupations/:occupationId/papers/new" element={<PaperCreate />} />
        <Route path="occupations/papers/:id/edit" element={<PaperEdit />} />
        
        {/* Assessment Center routes */}
        <Route path="assessment-centers" element={<AssessmentCenterList />} />
        <Route path="assessment-centers/new" element={<AssessmentCenterCreate />} />
        <Route path="assessment-centers/:id" element={<AssessmentCenterView />} />
        <Route path="assessment-centers/:id/edit" element={<AssessmentCenterEdit />} />
        <Route path="assessment-centers/:centerId/branches/new" element={<BranchEdit />} />
        <Route path="assessment-centers/branches/:branchId/edit" element={<BranchEdit />} />
        
        {/* Assessment Series routes */}
        <Route path="assessment-series" element={<AssessmentSeriesList />} />
        <Route path="assessment-series/new" element={<AssessmentSeriesCreate />} />
        <Route path="assessment-series/:id" element={<AssessmentSeriesView />} />
        <Route path="assessment-series/:id/edit" element={<AssessmentSeriesEdit />} />
        
        {/* Users routes */}
        <Route path="users" element={<UsersIndex />} />
        <Route path="users/staff" element={<StaffList />} />
        <Route path="users/staff/new" element={<StaffEdit />} />
        <Route path="users/staff/:id" element={<StaffView />} />
        <Route path="users/staff/:id/edit" element={<StaffEdit />} />
        <Route path="users/support-staff" element={<SupportStaffList />} />
        <Route path="users/support-staff/new" element={<SupportStaffEdit />} />
        <Route path="users/support-staff/:id" element={<SupportStaffView />} />
        <Route path="users/support-staff/:id/edit" element={<SupportStaffEdit />} />
        <Route path="users/center-representatives" element={<CenterRepresentativeList />} />
        <Route path="users/center-representatives/create" element={<CenterRepresentativeEdit />} />
        <Route path="users/center-representatives/:id" element={<CenterRepresentativeView />} />
        <Route path="users/center-representatives/:id/edit" element={<CenterRepresentativeEdit />} />
        
        {/* Reports routes */}
        <Route path="reports" element={<ReportsIndex />} />
        <Route path="reports/albums" element={<Albums />} />
        <Route path="reports/result-lists" element={<ResultLists />} />
        
        {/* Fees routes */}
        <Route path="fees/*" element={<FeesModule />} />
        
        {/* Marksheets routes */}
        <Route path="marksheets/*" element={<MarksheetsModule />} />
        
        {/* Complaints routes */}
        <Route path="complaints" element={<ComplaintsList />} />
        <Route path="complaints/create" element={<CreateComplaint />} />
        <Route path="complaints/:id" element={<ComplaintDetail />} />
        
        {/* Statistics routes */}
        <Route path="statistics" element={<StatisticsDashboard />} />
        <Route path="statistics/series/:id" element={<SeriesStatistics />} />
        
        <Route path="*" element={<div className="p-6"><h1 className="text-2xl">404 - Page Not Found</h1></div>} />
      </Route>
    </Routes>
  );
}

export default App;
