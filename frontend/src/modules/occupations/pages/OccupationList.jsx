import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Eye, Edit, Trash2, Plus, Search, Filter } from 'lucide-react';
import occupationApi from '../services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const OccupationList = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Fetch occupations
  const { data, isLoading, error } = useQuery({
    queryKey: ['occupations', page, searchTerm, categoryFilter, sectorFilter],
    queryFn: () =>
      occupationApi.getAll({
        page,
        page_size: pageSize,
        search: searchTerm,
        occ_category: categoryFilter,
        sector: sectorFilter,
      }),
  });

  // Fetch sectors for filter
  const { data: sectorsData } = useQuery({
    queryKey: ['sectors'],
    queryFn: () => occupationApi.sectors.getAll(),
  });

  const occupations = data?.data?.results || [];
  const totalPages = data?.data?.count ? Math.ceil(data.data.count / pageSize) : 1;
  const sectors = sectorsData?.data?.results || [];

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
  };

  const handleViewOccupation = (id) => {
    navigate(`/occupations/${id}`);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Occupations</h1>
            <p className="text-gray-600 mt-1">Manage occupations and trades</p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/occupations/new')}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Occupation
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <Card.Content className="p-4">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search by code or name..."
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
                  <option value="formal">Formal</option>
                  <option value="workers_pas">Worker's PAS</option>
                </select>
              </div>

              {/* Sector Filter */}
              <div>
                <select
                  value={sectorFilter}
                  onChange={(e) => {
                    setSectorFilter(e.target.value);
                    setPage(1);
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">All Sectors</option>
                  {sectors.map((sector) => (
                    <option key={sector.id} value={sector.id}>
                      {sector.name}
                    </option>
                  ))}
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occ Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occ Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sector
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Levels
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
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    Loading occupations...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-red-500">
                    Error loading occupations: {error.message}
                  </td>
                </tr>
              ) : occupations.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    No occupations found
                  </td>
                </tr>
              ) : (
                occupations.map((occupation) => (
                  <tr
                    key={occupation.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleViewOccupation(occupation.id)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">
                        {occupation.occ_code}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-900">{occupation.occ_name}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          occupation.occ_category === 'formal'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-purple-100 text-purple-800'
                        }`}
                      >
                        {occupation.occ_category_display}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {occupation.sector_name || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {occupation.levels_count || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          occupation.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {occupation.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewOccupation(occupation.id);
                          }}
                          className="text-primary-600 hover:text-primary-900"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/occupations/${occupation.id}/edit`);
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

export default OccupationList;
