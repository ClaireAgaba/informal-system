import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Eye, Edit, Plus, Search, Download, CheckSquare, Square } from 'lucide-react';
import * as XLSX from 'xlsx';
import assessmentCenterApi from '../services/assessmentCenterApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const AssessmentCenterList = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [page, setPage] = useState(1);
  const [selectedCenters, setSelectedCenters] = useState([]);
  const pageSize = 20;

  // Fetch assessment centers
  const { data, isLoading, error } = useQuery({
    queryKey: ['assessment-centers', page, searchTerm, categoryFilter],
    queryFn: () =>
      assessmentCenterApi.getAll({
        page,
        page_size: pageSize,
        search: searchTerm,
        assessment_category: categoryFilter,
      }),
  });

  const centers = data?.data?.results || [];
  const totalPages = data?.data?.count ? Math.ceil(data.data.count / pageSize) : 1;

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
  };

  const handleViewCenter = (id) => {
    navigate(`/assessment-centers/${id}`);
  };

  const handleSelectAll = () => {
    if (selectedCenters.length === centers.length) {
      setSelectedCenters([]);
    } else {
      setSelectedCenters(centers.map(center => center.id));
    }
  };

  const handleSelectCenter = (id) => {
    setSelectedCenters(prev => 
      prev.includes(id) 
        ? prev.filter(centerId => centerId !== id)
        : [...prev, id]
    );
  };

  const isAllSelected = centers.length > 0 && selectedCenters.length === centers.length;

  const [exporting, setExporting] = useState(false);

  const handleExportExcel = async () => {
    setExporting(true);
    try {
      let centersToExport;
      
      if (selectedCenters.length > 0) {
        // Export only selected items from current page
        centersToExport = centers.filter(c => selectedCenters.includes(c.id));
      } else {
        // Fetch ALL centers for export
        const response = await assessmentCenterApi.getAll({ page_size: 10000 });
        centersToExport = response?.data?.results || response?.data || [];
      }

      if (centersToExport.length === 0) {
        alert('No centers to export');
        setExporting(false);
        return;
      }

      // Export centers data
      const centersData = centersToExport.map(center => ({
        'Center Code': center.center_number,
        'Center Name': center.center_name,
        'Category': center.assessment_category_display || center.assessment_category,
        'District': center.district_name || 'N/A',
        'Village': center.village_name || 'N/A',
        'Contact 1': center.contact_1 || 'N/A',
        'Contact 2': center.contact_2 || 'N/A',
        'Email': center.email || 'N/A',
        'Status': center.is_active ? 'Active' : 'Inactive',
      }));

      // Fetch branches for all selected centers
      const branchPromises = centersToExport.map(center => 
        assessmentCenterApi.branches.getByCenter(center.id)
      );
      const branchResponses = await Promise.all(branchPromises);
      
      // Flatten all branches and add center info
      const allBranches = [];
      branchResponses.forEach((response, index) => {
        const branches = response?.data?.results || response?.data || [];
        const center = centersToExport[index];
        branches.forEach(branch => {
          allBranches.push({
            'Center Code': center.center_number,
            'Center Name': center.center_name,
            'Branch Code': branch.branch_code || 'N/A',
            'Branch Name': branch.branch_name || 'N/A',
            'District': branch.district_name || 'N/A',
            'Village': branch.village_name || 'N/A',
            'Status': branch.is_active ? 'Active' : 'Inactive',
          });
        });
      });

      // Create workbook with two sheets
      const workbook = XLSX.utils.book_new();
      
      const centersSheet = XLSX.utils.json_to_sheet(centersData);
      XLSX.utils.book_append_sheet(workbook, centersSheet, 'Assessment Centers');
      
      if (allBranches.length > 0) {
        const branchesSheet = XLSX.utils.json_to_sheet(allBranches);
        XLSX.utils.book_append_sheet(workbook, branchesSheet, 'Center Branches');
      }
      
      XLSX.writeFile(workbook, `assessment_centers_${new Date().toISOString().split('T')[0]}.xlsx`);
    } catch (error) {
      console.error('Export error:', error);
      alert('Error exporting data');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Assessment Centers</h1>
            <p className="text-gray-600 mt-1">Manage assessment centers and branches</p>
          </div>
          <div className="flex items-center space-x-2">
            {selectedCenters.length > 0 && (
              <Button
                variant="outline"
                size="md"
                onClick={() => setSelectedCenters([])}
              >
                Clear Selection ({selectedCenters.length})
              </Button>
            )}
            <Button
              variant="outline"
              size="md"
              onClick={handleExportExcel}
              disabled={exporting}
            >
              <Download className="w-4 h-4 mr-2" />
              {exporting ? 'Exporting...' : `Export Excel ${selectedCenters.length > 0 ? `(${selectedCenters.length})` : ''}`}
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate('/assessment-centers/new')}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Center
            </Button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <Card.Content className="p-4">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search by center number or name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              {/* Category Filter */}
              <div>
                <select
                  value={categoryFilter}
                  onChange={(e) => {
                    setCategoryFilter(e.target.value);
                    setPage(1);
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">All Categories</option>
                  <option value="VTI">Vocational Training Institute</option>
                  <option value="TTI">Technical Training Institute</option>
                  <option value="workplace">Workplace</option>
                </select>
              </div>
            </div>
          </form>
        </Card.Content>
      </Card>

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left">
                  <button
                    onClick={handleSelectAll}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    {isAllSelected ? (
                      <CheckSquare className="w-5 h-5" />
                    ) : (
                      <Square className="w-5 h-5" />
                    )}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Center Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Center Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  District
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Village
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="9" className="px-6 py-4 text-center text-gray-500">
                    Loading assessment centers...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="9" className="px-6 py-4 text-center text-red-500">
                    Error loading centers: {error.message}
                  </td>
                </tr>
              ) : centers.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-6 py-4 text-center text-gray-500">
                    No assessment centers found
                  </td>
                </tr>
              ) : (
                centers.map((center) => (
                  <tr
                    key={center.id}
                    className={`hover:bg-gray-50 cursor-pointer ${selectedCenters.includes(center.id) ? 'bg-primary-50' : ''}`}
                    onClick={() => handleViewCenter(center.id)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleSelectCenter(center.id)}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        {selectedCenters.includes(center.id) ? (
                          <CheckSquare className="w-5 h-5 text-primary-600" />
                        ) : (
                          <Square className="w-5 h-5" />
                        )}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {center.center_number}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-900">{center.center_name}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
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
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {center.district_name || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {center.village_name || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {center.contact_1 || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          center.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {center.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewCenter(center.id);
                          }}
                          className="text-primary-600 hover:text-primary-900"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/assessment-centers/${center.id}/edit`);
                          }}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Page {page} of {totalPages}
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default AssessmentCenterList;
