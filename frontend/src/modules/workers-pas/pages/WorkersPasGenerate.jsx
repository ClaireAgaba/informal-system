import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, Loader2, Search, Download, FileStack, CheckSquare, Square, Printer } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../../../services/apiClient';

const WorkersPasGenerate = () => {
  const navigate = useNavigate();
  const [occupations, setOccupations] = useState([]);
  const [series, setSeries] = useState([]);
  const [occupationId, setOccupationId] = useState('');
  const [seriesId, setSeriesId] = useState('');

  const [candidates, setCandidates] = useState([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [loadingCandidates, setLoadingCandidates] = useState(false);

  const [mode, setMode] = useState('a4_2up');
  const [generating, setGenerating] = useState(false);

  // Lookups
  useEffect(() => {
    (async () => {
      try {
        const [occRes, sRes] = await Promise.all([
          apiClient.get('/workers-pas/occupations/'),
          apiClient.get('/workers-pas/series/'),
        ]);
        setOccupations(occRes.data || []);
        setSeries(sRes.data || []);
        const current = (sRes.data || []).find((x) => x.is_current);
        if (current) setSeriesId(String(current.id));
      } catch (err) {
        toast.error('Failed to load lookups');
      }
    })();
  }, []);

  // Candidates list
  useEffect(() => {
    if (!occupationId || !seriesId) {
      setCandidates([]);
      return;
    }
    (async () => {
      setLoadingCandidates(true);
      try {
        const res = await apiClient.get(
          `/workers-pas/candidates/?occupation=${occupationId}&series=${seriesId}`,
        );
        setCandidates(res.data || []);
        setSelected(new Set());
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Failed to load candidates');
        setCandidates([]);
      } finally {
        setLoadingCandidates(false);
      }
    })();
  }, [occupationId, seriesId]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return candidates;
    return candidates.filter(
      (c) =>
        (c.full_name || '').toLowerCase().includes(q) ||
        (c.registration_number || '').toLowerCase().includes(q),
    );
  }, [candidates, search]);

  const allSelected = filtered.length > 0 && filtered.every((c) => selected.has(c.id));
  const selectAll = () => {
    const next = new Set(selected);
    filtered.forEach((c) => next.add(c.id));
    setSelected(next);
  };
  const clearAll = () => {
    const next = new Set(selected);
    filtered.forEach((c) => next.delete(c.id));
    setSelected(next);
  };
  const toggle = (id) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const handle2upA6Print = async () => {
    if (!occupationId || !seriesId) {
      toast.error('Select an occupation and series first.');
      return;
    }
    const ids = Array.from(selected);
    if (ids.length === 0 || ids.length > 2) {
      toast.error('Select exactly 1 or 2 candidates for 2-up A6 print.');
      return;
    }
    setGenerating(true);
    try {
      const res = await apiClient.post(
        '/workers-pas/2up-a6-print/',
        { occupation_id: occupationId, series_id: seriesId, candidate_ids: ids },
        { responseType: 'blob' },
      );
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      window.open(url, '_blank');
      const sheets = Math.ceil(ids.length / 2);
    toast.success(
        ids.length === 1
          ? 'A4 sheet ready (1 candidate, bottom half blank) — print duplex, flip on long edge, fold and staple.'
          : `${sheets} sheet${sheets > 1 ? 's' : ''} ready (${ids.length} candidates) — print duplex, flip on long edge, cut at the dashed line, rotate bottom halves 180°, fold and staple.`,
      );
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate 2-up A6 print.');
    } finally {
      setGenerating(false);
    }
  };

  const generate = async ({ bulk, printMode }) => {
    if (!occupationId || !seriesId) {
      toast.error('Select an occupation and series first.');
      return;
    }
    const ids = Array.from(selected);
    if (ids.length === 0) {
      toast.error('Select at least one candidate.');
      return;
    }
    if (!bulk && !printMode && ids.length !== 1) {
      toast.error('Pick exactly one candidate to preview.');
      return;
    }

    setGenerating(true);
    try {
      if (printMode) {
        // Print Booklet: works for 1 or more candidates
        if (ids.length === 1) {
          const res = await apiClient.post(
            '/workers-pas/generate/',
            { candidate_id: ids[0], occupation_id: occupationId, series_id: seriesId, mode: 'booklet_a4' },
            { responseType: 'blob' },
          );
          const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
          window.open(url, '_blank');
        } else {
          const res = await apiClient.post(
            '/workers-pas/bulk-generate/',
            { occupation_id: occupationId, series_id: seriesId, candidate_ids: ids, mode: 'booklet_a4_print' },
            { responseType: 'blob' },
          );
          const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
          window.open(url, '_blank');
        }
        toast.success(`Booklet ready — print duplex, flip on short edge.`);
      } else if (!bulk) {
        const res = await apiClient.post(
          '/workers-pas/generate/',
          { candidate_id: ids[0], occupation_id: occupationId, series_id: seriesId },
          { responseType: 'blob' },
        );
        const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
        window.open(url, '_blank');
        toast.success('Booklet generated.');
      } else {
        const res = await apiClient.post(
          '/workers-pas/bulk-generate/',
          { occupation_id: occupationId, series_id: seriesId, candidate_ids: ids, mode },
          { responseType: 'blob' },
        );
        const blob = new Blob([res.data], { type: 'application/zip' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const cd = res.headers['content-disposition'] || '';
        const match = cd.match(/filename="?([^"]+)"?/);
        a.download = match ? match[1] : `workers_pas_${ids.length}_candidates.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        toast.success(`Generated ${ids.length} booklets.`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/workers-pas')}
            className="p-2 hover:bg-gray-100 rounded-lg"
            title="Back"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BookOpen className="w-6 h-6 text-primary-600" /> Generate Worker's PAS booklets
            </h1>
            <p className="text-sm text-gray-500">Pick an occupation and series, choose candidates, then generate.</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5 mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Occupation</label>
          <select
            value={occupationId}
            onChange={(e) => setOccupationId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="">-- select --</option>
            {occupations.map((o) => (
              <option key={o.id} value={o.id}>
                {o.occ_name}{o.wp_code ? ` (${o.wp_code})` : ''}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">Only Worker's PAS occupations are listed.</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Assessment Series</label>
          <select
            value={seriesId}
            onChange={(e) => setSeriesId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="">-- select --</option>
            {series.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}{s.is_current ? ' (current)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5 mb-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Output mode</label>
            <div className="flex gap-3">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="radio"
                  checked={mode === 'a4_2up'}
                  onChange={() => setMode('a4_2up')}
                />
                <span><b>A4 (2 candidates per page)</b> — print, then cut horizontally</span>
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="radio"
                  checked={mode === 'single'}
                  onChange={() => setMode('single')}
                />
                <span>A5 (one PDF per candidate)</span>
              </label>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            <button
              disabled={generating || selected.size !== 1}
              onClick={() => generate({ bulk: false })}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
              title="Preview a single booklet (A5)"
            >
              {generating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
              Preview A5
            </button>
            <button
              disabled={generating || selected.size === 0}
              onClick={() => generate({ bulk: false, printMode: true })}
              className="inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              title="Generate A4 landscape booklet — print duplex, flip on short edge"
            >
              {generating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Printer className="w-4 h-4 mr-2" />}
              Print Booklet
            </button>
            <button
              disabled={generating || selected.size === 0}
              onClick={() => generate({ bulk: true })}
              className="inline-flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {generating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <FileStack className="w-4 h-4 mr-2" />}
              Generate {selected.size > 0 ? `${selected.size} ` : ''}booklets (.zip)
            </button>
            <button
              disabled={generating || selected.size === 0}
              onClick={handle2upA6Print}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              title="Generates A4 sheets with 2 A6 booklets each (candidates paired in selection order) — print duplex, flip on long edge, cut at dashed line, rotate bottom halves 180°, fold and staple."
            >
              {generating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Printer className="w-4 h-4 mr-2" />}
              Print 2-up A6 Booklets
            </button>
          </div>
        </div>
      </div>

      {occupationId && seriesId && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden mb-6">
          <div className="p-4 border-b border-gray-200 flex items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search candidate name or reg no…"
                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <span className="text-sm text-gray-500">
              {selected.size} selected of {filtered.length}
            </span>
            <div className="flex gap-2">
              <button
                onClick={selectAll}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded border border-primary-200"
              >
                <CheckSquare className="w-3.5 h-3.5" />
                Select all {filtered.length}
              </button>
              {selected.size > 0 && (
                <button
                  onClick={clearAll}
                  className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 rounded border border-gray-200"
                >
                  <Square className="w-3.5 h-3.5" />
                  Clear
                </button>
              )}
            </div>
          </div>

          {loadingCandidates ? (
            <div className="p-8 text-center text-gray-500"><Loader2 className="w-5 h-5 animate-spin inline mr-2" />Loading candidates…</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No candidates registered for this occupation in the selected series.</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={() => allSelected ? clearAll() : selectAll()}
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reg No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gender</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Book</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selected.has(c.id)}
                        onChange={() => toggle(c.id)}
                      />
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-700">{c.registration_number || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{c.full_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{c.gender}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {c.has_book ? (
                        <span className="text-green-700 font-mono">{c.book_number}</span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

    </div>
  );
};

export default WorkersPasGenerate;
