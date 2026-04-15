import { useMemo, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Database, Search, ChevronLeft, ChevronRight, Filter, X, Users, ImageOff } from 'lucide-react';
import ditLegacyApi from '../api/ditLegacyApi';

export default function DitLegacyIndex() {
  const [q, setQ] = useState('');
  const [name, setName] = useState('');
  const [regno, setRegno] = useState('');
  const [gender, setGender] = useState('');
  const [status, setStatus] = useState('');
  const [district, setDistrict] = useState('');
  const [trainingProvider, setTrainingProvider] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const trimmed = q.trim();
  const nameTrimmed = name.trim();
  const regnoTrimmed = regno.trim();
  const districtTrimmed = district.trim();
  const trainingProviderTrimmed = trainingProvider.trim();

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ['dit-legacy-search', trimmed, nameTrimmed, regnoTrimmed, gender, status, districtTrimmed, trainingProviderTrimmed, page],
    queryFn: () =>
      ditLegacyApi.search({
        q: trimmed,
        name: nameTrimmed,
        regno: regnoTrimmed,
        gender,
        status,
        district: districtTrimmed,
        training_provider: trainingProviderTrimmed,
        page,
        page_size: pageSize,
      }),
    keepPreviousData: true,
  });

  const results = useMemo(() => data?.data?.results || [], [data]);
  const totalCount = data?.data?.total_count || 0;
  const totalPages = data?.data?.total_pages || 1;
  const hasNext = data?.data?.has_next || false;
  const hasPrev = data?.data?.has_prev || false;

  const handleFilterChange = useCallback((setter) => (e) => {
    setter(e.target.value);
    setPage(1);
  }, []);

  const clearFilters = useCallback(() => {
    setQ('');
    setName('');
    setRegno('');
    setGender('');
    setStatus('');
    setDistrict('');
    setTrainingProvider('');
    setPage(1);
  }, []);

  const hasActiveFilters = trimmed || nameTrimmed || regnoTrimmed || gender || status || districtTrimmed || trainingProviderTrimmed;

  return (
    <div className="p-4 lg:p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Database className="h-7 w-7 text-cyan-600" />
              DIT Legacy Data
            </h1>
            <p className="text-gray-500 mt-1 text-sm">
              Search and browse legacy candidate records from the DIT database
            </p>
          </div>
          {totalCount > 0 && (
            <div className="hidden md:flex items-center gap-2 bg-cyan-50 text-cyan-700 px-4 py-2 rounded-lg">
              <Users className="h-5 w-5" />
              <span className="font-semibold">{totalCount.toLocaleString()}</span>
              <span className="text-cyan-600">records found</span>
            </div>
          )}
        </div>
      </div>

      {/* Filters Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-700">
              <Filter className="h-4 w-4" />
              <span className="font-medium text-sm">Filters</span>
            </div>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-600 transition-colors"
              >
                <X className="h-3 w-3" />
                Clear all
              </button>
            )}
          </div>
        </div>

        <div className="p-4">
          {/* Search Row */}
          <div className="flex items-center gap-3 bg-gray-50 rounded-lg px-4 py-3 mb-4">
            <Search className="h-5 w-5 text-gray-400" />
            <input
              value={q}
              onChange={handleFilterChange(setQ)}
              placeholder="Search by name..."
              className="flex-1 bg-transparent outline-none text-sm text-gray-700 placeholder-gray-400"
            />
          </div>

          {/* Filter Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Name
              </label>
              <input
                value={name}
                onChange={handleFilterChange(setName)}
                placeholder="e.g. John"
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Registration Number
              </label>
              <input
                value={regno}
                onChange={handleFilterChange(setRegno)}
                placeholder="e.g. UVQF/414/01/TL/03"
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Gender
              </label>
              <select
                value={gender}
                onChange={handleFilterChange(setGender)}
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-colors"
              >
                <option value="">All Genders</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Status
              </label>
              <select
                value={status}
                onChange={handleFilterChange(setStatus)}
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-colors"
              >
                <option value="">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="in_progress">In Progress</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                District
              </label>
              <input
                value={district}
                onChange={handleFilterChange(setDistrict)}
                placeholder="e.g. Wakiso"
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Training Provider
              </label>
              <input
                value={trainingProvider}
                onChange={handleFilterChange(setTrainingProvider)}
                placeholder="e.g. Industrial Hub"
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-colors"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {isLoading && !results.length ? (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600"></div>
            <span className="ml-3 text-gray-500">Loading...</span>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-16 text-red-500">
            <span>Failed to load data. Please try again.</span>
          </div>
        ) : results.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500">
            <Database className="h-12 w-12 text-gray-300 mb-3" />
            <span>No results found</span>
            <span className="text-sm text-gray-400 mt-1">Try adjusting your filters</span>
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3.5 text-center font-semibold text-gray-700 whitespace-nowrap w-16">Photo</th>
                    <th className="px-4 py-3.5 text-left font-semibold text-gray-700 whitespace-nowrap">Name</th>
                    <th className="px-4 py-3.5 text-left font-semibold text-gray-700 whitespace-nowrap">Reg. Number</th>
                    <th className="px-4 py-3.5 text-left font-semibold text-gray-700 whitespace-nowrap">Gender</th>
                    <th className="px-4 py-3.5 text-left font-semibold text-gray-700 whitespace-nowrap">Training Provider</th>
                    <th className="px-4 py-3.5 text-left font-semibold text-gray-700 whitespace-nowrap">District</th>
                    <th className="px-4 py-3.5 text-center font-semibold text-gray-700 whitespace-nowrap">Status</th>
                    <th className="px-4 py-3.5 text-center font-semibold text-gray-700 whitespace-nowrap w-24">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {results.map((r, idx) => {
                    const fullName = [r.first_name, r.other_name, r.surname]
                      .filter(Boolean)
                      .join(' ');
                    return (
                      <tr
                        key={r.person_id}
                        className={`hover:bg-cyan-50/50 transition-colors ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                      >
                        <td className="px-4 py-3 text-center">
                          {r.has_photo ? (
                            <img
                              src={`/api/dit-legacy/photo/${r.person_id}/`}
                              alt=""
                              className="h-8 w-8 rounded-full object-cover ring-2 ring-green-200 mx-auto"
                              loading="lazy"
                            />
                          ) : (
                            <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center mx-auto ring-2 ring-gray-200">
                              <ImageOff className="h-3.5 w-3.5 text-gray-400" />
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900 whitespace-nowrap">
                          {fullName || '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 font-mono text-xs whitespace-nowrap">
                          {r.registration_number || '—'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {r.gender ? (
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                              r.gender.toLowerCase() === 'male' || r.gender.toLowerCase() === 'm'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-pink-100 text-pink-700'
                            }`}>
                              {r.gender.toLowerCase() === 'm' ? 'Male' : r.gender.toLowerCase() === 'f' ? 'Female' : r.gender}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 max-w-xs truncate" title={r.training_provider}>
                          {r.training_provider || '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                          {r.district || '—'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {r.certificate_number ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                              Completed
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                              In Progress
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Link
                            to={`/dit-legacy-data/${encodeURIComponent(r.person_id)}`}
                            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-cyan-700 bg-cyan-50 hover:bg-cyan-100 rounded-lg transition-colors"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>
                  Showing <span className="font-medium">{((page - 1) * pageSize) + 1}</span>
                  {' '}-{' '}
                  <span className="font-medium">{Math.min(page * pageSize, totalCount)}</span>
                  {' '}of{' '}
                  <span className="font-medium">{totalCount.toLocaleString()}</span>
                </span>
                {isFetching && <span className="text-gray-400">(updating...)</span>}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={!hasPrev || isFetching}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </button>

                <div className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg">
                  Page <span className="font-medium mx-1">{page}</span> of <span className="font-medium mx-1">{totalPages}</span>
                </div>

                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={!hasNext || isFetching}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
