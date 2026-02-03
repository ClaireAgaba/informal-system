import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Database, Search } from 'lucide-react';
import ditLegacyApi from '../api/ditLegacyApi';

export default function DitLegacyIndex() {
  const [q, setQ] = useState('');
  const [gender, setGender] = useState('');
  const [district, setDistrict] = useState('');
  const [trainingProvider, setTrainingProvider] = useState('');

  const trimmed = q.trim();
  const districtTrimmed = district.trim();
  const trainingProviderTrimmed = trainingProvider.trim();

  const { data, isLoading, error } = useQuery({
    queryKey: ['dit-legacy-search', trimmed, gender, districtTrimmed, trainingProviderTrimmed],
    queryFn: () =>
      ditLegacyApi.search({
        q: trimmed,
        gender,
        district: districtTrimmed,
        training_provider: trainingProviderTrimmed,
        limit: 50,
      }),
  });

  const results = useMemo(() => data?.data?.results || [], [data]);
  <p className="text-xs text-gray-500 mt-1">
          Tip: leave search empty to browse recent records (max 50).
        </p>
      
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Database className="h-8 w-8 text-cyan-700" />
          DIT Legacy data
        </h1>
        <p className="text-gray-600 mt-1">
          Search legacy candidates by registration number or name.
        </p>
      </div>

      <div className="max-w-5xl">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="text-gray-500">
              <Search className="h-5 w-5" />
            </div>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search by registration number or name"
              className="w-full outline-none text-sm"
            />
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <div className="text-xs font-medium text-gray-600 mb-1">Gender</div>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
              >
                <option value="">All</option>
                <option value="m">Male</option>
                <option value="f">Female</option>
              </select>
            </div>

            <div>
              <div className="text-xs font-medium text-gray-600 mb-1">District</div>
              <input
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                placeholder="e.g. Wakiso"
                className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
              />
            </div>

            <div>
              <div className="text-xs font-medium text-gray-600 mb-1">Training provider</div>
              <input
                value={trainingProvider}
                onChange={(e) => setTrainingProvider(e.target.value)}
                placeholder="e.g. Industrial Hub"
                className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>

        <div className="mt-4">
          {isLoading ? (
            <div className="text-sm text-gray-600">Searching...</div>
          ) : error ? (
            <div className="text-sm text-red-600">Failed to search.</div>
          ) : results.length === 0 ? (
            <div className="text-sm text-gray-600">No results found.</div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 text-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium">Name</th>
                      <th className="px-4 py-3 text-left font-medium">Reg No</th>
                      <th className="px-4 py-3 text-left font-medium">Gender</th>
                      <th className="px-4 py-3 text-left font-medium">Training Provider</th>
                      <th className="px-4 py-3 text-left font-medium">District</th>
                      <th className="px-4 py-3 text-left font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {results.map((r) => {
                      const fullName = [r.first_name, r.other_name, r.surname]
                        .filter(Boolean)
                        .join(' ');
                      return (
                        <tr key={r.person_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-gray-900">{fullName || '—'}</td>
                          <td className="px-4 py-3 text-gray-700">{r.registration_number || '—'}</td>
                          <td className="px-4 py-3 text-gray-700">{r.gender || '—'}</td>
                          <td className="px-4 py-3 text-gray-700">{r.training_provider || '—'}</td>
                          <td className="px-4 py-3 text-gray-700">{r.district || '—'}</td>
                          <td className="px-4 py-3">
                            <Link
                              to={`/dit-legacy-data/${encodeURIComponent(r.person_id)}`}
                              className="text-cyan-700 hover:text-cyan-900 font-medium"
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
