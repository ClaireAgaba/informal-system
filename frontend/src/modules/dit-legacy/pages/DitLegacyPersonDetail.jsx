import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Database } from 'lucide-react';
import ditLegacyApi from '../api/ditLegacyApi';

function fmtDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString();
}

export default function DitLegacyPersonDetail() {
  const { personId } = useParams();

  const { data: personResp, isLoading: personLoading } = useQuery({
    queryKey: ['dit-legacy-person', personId],
    queryFn: () => ditLegacyApi.getPerson(personId),
    enabled: !!personId,
  });

  const { data: resultsResp, isLoading: resultsLoading } = useQuery({
    queryKey: ['dit-legacy-results', personId],
    queryFn: () => ditLegacyApi.getPersonResults(personId, { limit: 200 }),
    enabled: !!personId,
  });

  const person = personResp?.data;
  const results = useMemo(() => resultsResp?.data?.results || [], [resultsResp]);

  const fullName = [person?.first_name, person?.other_name, person?.surname]
    .filter(Boolean)
    .join(' ');

  const photoUrl = personId
    ? `/api/dit-legacy/person/${encodeURIComponent(personId)}/photo/`
    : null;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Database className="h-4 w-4 text-cyan-700" />
            <span>DIT Legacy data</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">{fullName || 'Candidate'}</h1>
          <div className="mt-1 text-sm text-gray-600">Person ID: {personId}</div>
        </div>

        <Link
          to="/dit-legacy-data"
          className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to search
        </Link>
      </div>

      {personLoading ? (
        <div className="text-sm text-gray-600">Loading candidate...</div>
      ) : !person ? (
        <div className="text-sm text-red-600">Candidate not found.</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="text-sm font-semibold text-gray-900">Passport photo</div>
              <div className="mt-3">
                {photoUrl ? (
                  <img
                    src={photoUrl}
                    alt="Passport"
                    className="w-full max-w-[260px] aspect-[3/4] object-cover rounded-md border border-gray-200 bg-gray-50"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      const next = e.currentTarget.nextSibling;
                      if (next && next.style) next.style.display = 'flex';
                    }}
                  />
                ) : null}

                <div
                  style={{ display: photoUrl ? 'none' : 'flex' }}
                  className="w-full max-w-[260px] aspect-[3/4] rounded-md border border-gray-200 bg-gray-50 items-center justify-center text-xs text-gray-500"
                >
                  No photo
                </div>
              </div>
            </div>

            <div className="mt-6 rounded-lg border border-gray-200 bg-white p-4">
              <div className="text-sm font-semibold text-gray-900">Biodata</div>
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Registration No</div>
                  <div className="text-gray-900 text-right">{person.registration_number || '—'}</div>
                </div>
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Gender</div>
                  <div className="text-gray-900 text-right">{person.gender || '—'}</div>
                </div>
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Birth date</div>
                  <div className="text-gray-900 text-right">{fmtDate(person.birth_date)}</div>
                </div>
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Nationality</div>
                  <div className="text-gray-900 text-right">{person.nationality || '—'}</div>
                </div>
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Residence</div>
                  <div className="text-gray-900 text-right">{person.residence || '—'}</div>
                </div>
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Village</div>
                  <div className="text-gray-900 text-right">{person.village || '—'}</div>
                </div>
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">District</div>
                  <div className="text-gray-900 text-right">{person.district || '—'}</div>
                </div>
              </div>
            </div>

            <div className="mt-6 rounded-lg border border-gray-200 bg-white p-4">
              <div className="text-sm font-semibold text-gray-900">Special needs</div>
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Has disability</div>
                  <div className="text-gray-900 text-right">
                    {person.is_disabled ? 'Yes' : 'No'}
                  </div>
                </div>
                <div className="flex justify-between gap-4">
                  <div className="text-gray-600">Disability</div>
                  <div className="text-gray-900 text-right">{person.disability || '—'}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="text-sm font-semibold text-gray-900">Training</div>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-600">Training provider</div>
                  <div className="text-gray-900">{person.training_provider || '—'}</div>
                </div>
                <div>
                  <div className="text-gray-600">Ownership</div>
                  <div className="text-gray-900">{person.ownership || '—'}</div>
                </div>
                <div>
                  <div className="text-gray-600">Level</div>
                  <div className="text-gray-900">{person.level || '—'}</div>
                </div>
                <div>
                  <div className="text-gray-600">Actual date</div>
                  <div className="text-gray-900">{fmtDate(person.actual_date)}</div>
                </div>
                <div>
                  <div className="text-gray-600">Certificate number</div>
                  <div className="text-gray-900">{person.certificate_number || '—'}</div>
                </div>
              </div>
            </div>

            <div className="mt-6 rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-gray-900">Results</div>
                <div className="text-xs text-gray-500">Showing up to 200 rows</div>
              </div>

              {resultsLoading ? (
                <div className="mt-3 text-sm text-gray-600">Loading results...</div>
              ) : results.length === 0 ? (
                <div className="mt-3 text-sm text-gray-600">No results found for this candidate.</div>
              ) : (
                <div className="mt-3 overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50 text-gray-700">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium">Type</th>
                        <th className="px-3 py-2 text-left font-medium">Last Modified</th>
                        <th className="px-3 py-2 text-left font-medium">Provider</th>
                        <th className="px-3 py-2 text-left font-medium">Module</th>
                        <th className="px-3 py-2 text-left font-medium">Papers</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {results.map((r, idx) => (
                        <tr key={`${r.source_table}-${idx}`} className="hover:bg-gray-50">
                          <td className="px-3 py-2 text-gray-900">{r.result_type || '—'}</td>
                          <td className="px-3 py-2 text-gray-700">{fmtDate(r.last_modified)}</td>
                          <td className="px-3 py-2 text-gray-700">{r.training_provider || '—'}</td>
                          <td className="px-3 py-2 text-gray-700">
                            {[r.module_assessed, r.second_module_assessed].filter(Boolean).join(', ') || '—'}
                          </td>
                          <td className="px-3 py-2 text-gray-700">
                            {(r.papers || []).length === 0
                              ? '—'
                              : (r.papers || [])
                                  .map((p) => `${p.paper || 'paper'}: ${p.results ?? '—'} (${p.grade || '—'})`)
                                  .join(' | ')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
