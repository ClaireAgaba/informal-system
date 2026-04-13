import { useMemo, useState, useRef, useCallback } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft, Database, Award, BookOpen, User, MapPin, Shield,
  Pencil, Save, X, Upload, Clock, CheckCircle,
} from 'lucide-react';
import ditLegacyApi from '../api/ditLegacyApi';

function fmtDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString();
}

function fmtDateInput(value) {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toISOString().slice(0, 10);
}

function fmtDateTime(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function gradeColor(grade) {
  if (!grade) return 'bg-gray-100 text-gray-600';
  const g = grade.toUpperCase().replace(/[^A-E+\-]/g, '');
  if (g.startsWith('A')) return 'bg-green-100 text-green-700';
  if (g.startsWith('B')) return 'bg-blue-100 text-blue-700';
  if (g.startsWith('C')) return 'bg-yellow-100 text-yellow-700';
  if (g.startsWith('D')) return 'bg-orange-100 text-orange-700';
  return 'bg-red-100 text-red-700';
}

function commentColor(comment) {
  if (!comment) return 'text-gray-500';
  const c = comment.toLowerCase();
  if (c.includes('pass') || c.includes('success')) return 'text-green-600';
  if (c.includes('fail') || c.includes('unsuccess')) return 'text-red-600';
  return 'text-gray-600';
}

/* ── Editable row ── */
function EditableRow({ label, fieldKey, value, editing, form, onChange }) {
  if (!editing) {
    return (
      <div className="flex justify-between gap-4 py-1.5 border-b border-gray-50 last:border-0">
        <div className="text-gray-500 text-xs uppercase tracking-wide">{label}</div>
        <div className="text-gray-900 text-sm text-right font-medium">{value || '—'}</div>
      </div>
    );
  }
  const inputVal = form[fieldKey] ?? value ?? '';
  return (
    <div className="flex justify-between items-center gap-4 py-1 border-b border-gray-50 last:border-0">
      <div className="text-gray-500 text-xs uppercase tracking-wide shrink-0">{label}</div>
      <input
        value={inputVal}
        onChange={(e) => onChange(fieldKey, e.target.value)}
        className="text-sm text-right w-full max-w-[200px] rounded border border-gray-300 px-2 py-1 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none"
      />
    </div>
  );
}

function EditableDateRow({ label, fieldKey, value, editing, form, onChange }) {
  if (!editing) {
    return (
      <div className="flex justify-between gap-4 py-1.5 border-b border-gray-50 last:border-0">
        <div className="text-gray-500 text-xs uppercase tracking-wide">{label}</div>
        <div className="text-gray-900 text-sm text-right font-medium">{fmtDate(value)}</div>
      </div>
    );
  }
  const inputVal = form[fieldKey] ?? fmtDateInput(value) ?? '';
  return (
    <div className="flex justify-between items-center gap-4 py-1 border-b border-gray-50 last:border-0">
      <div className="text-gray-500 text-xs uppercase tracking-wide shrink-0">{label}</div>
      <input
        type="date"
        value={inputVal}
        onChange={(e) => onChange(fieldKey, e.target.value)}
        className="text-sm text-right w-full max-w-[200px] rounded border border-gray-300 px-2 py-1 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none"
      />
    </div>
  );
}

function EditableSelectRow({ label, fieldKey, value, editing, form, onChange, options }) {
  if (!editing) {
    return (
      <div className="flex justify-between gap-4 py-1.5 border-b border-gray-50 last:border-0">
        <div className="text-gray-500 text-xs uppercase tracking-wide">{label}</div>
        <div className="text-gray-900 text-sm text-right font-medium">{value || '—'}</div>
      </div>
    );
  }
  const inputVal = form[fieldKey] ?? value ?? '';
  return (
    <div className="flex justify-between items-center gap-4 py-1 border-b border-gray-50 last:border-0">
      <div className="text-gray-500 text-xs uppercase tracking-wide shrink-0">{label}</div>
      <select
        value={inputVal}
        onChange={(e) => onChange(fieldKey, e.target.value)}
        className="text-sm text-right w-full max-w-[200px] rounded border border-gray-300 px-2 py-1 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between gap-4 py-1.5 border-b border-gray-50 last:border-0">
      <div className="text-gray-500 text-xs uppercase tracking-wide">{label}</div>
      <div className="text-gray-900 text-sm text-right font-medium">{value || '—'}</div>
    </div>
  );
}

/* ── Card header with edit/save/cancel buttons ── */
function CardHeader({ icon: Icon, title, editing, onEdit, onSave, onCancel, saving }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
        <Icon className="h-4 w-4 text-cyan-700" />
        {title}
      </div>
      <div className="flex items-center gap-1">
        {editing ? (
          <>
            <button
              onClick={onCancel}
              disabled={saving}
              className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded transition-colors"
            >
              <X className="h-3 w-3" /> Cancel
            </button>
            <button
              onClick={onSave}
              disabled={saving}
              className="inline-flex items-center gap-1 text-xs text-white bg-cyan-600 hover:bg-cyan-700 px-3 py-1 rounded transition-colors disabled:opacity-50"
            >
              {saving ? (
                <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Save className="h-3 w-3" />
              )}
              Save
            </button>
          </>
        ) : (
          <button
            onClick={onEdit}
            className="inline-flex items-center gap-1 text-xs text-cyan-700 hover:text-cyan-800 hover:bg-cyan-50 px-2 py-1 rounded transition-colors"
          >
            <Pencil className="h-3 w-3" /> Edit
          </button>
        )}
      </div>
    </div>
  );
}


export default function DitLegacyPersonDetail() {
  const { personId } = useParams();
  const queryClient = useQueryClient();
  const photoInputRef = useRef(null);

  // ── Section edit states ──
  const [editingBio, setEditingBio] = useState(false);
  const [editingLocation, setEditingLocation] = useState(false);
  const [editingSpecial, setEditingSpecial] = useState(false);
  const [bioForm, setBioForm] = useState({});
  const [locForm, setLocForm] = useState({});
  const [specForm, setSpecForm] = useState({});
  const [saveMsg, setSaveMsg] = useState(null);

  const handleBioChange = useCallback((k, v) => setBioForm((p) => ({ ...p, [k]: v })), []);
  const handleLocChange = useCallback((k, v) => setLocForm((p) => ({ ...p, [k]: v })), []);
  const handleSpecChange = useCallback((k, v) => setSpecForm((p) => ({ ...p, [k]: v })), []);

  // ── Queries ──
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

  const { data: logsResp, isLoading: logsLoading } = useQuery({
    queryKey: ['dit-legacy-audit-logs', personId],
    queryFn: () => ditLegacyApi.getAuditLogs(personId),
    enabled: !!personId,
  });

  const person = personResp?.data;
  const registrations = useMemo(() => resultsResp?.data?.results || [], [resultsResp]);
  const examResults = useMemo(() => resultsResp?.data?.exam_results || [], [resultsResp]);
  const auditLogs = useMemo(() => logsResp?.data?.logs || [], [logsResp]);

  const fullName = [person?.first_name, person?.other_name, person?.surname]
    .filter(Boolean)
    .join(' ');

  const photoUrl = personId
    ? `/api/dit-legacy/person/${encodeURIComponent(personId)}/photo/`
    : null;

  // ── Mutations ──
  const showSaveMsg = (msg, type = 'success') => {
    setSaveMsg({ msg, type });
    setTimeout(() => setSaveMsg(null), 3000);
  };

  const updateMutation = useMutation({
    mutationFn: (data) => ditLegacyApi.updatePerson(personId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dit-legacy-person', personId] });
      queryClient.invalidateQueries({ queryKey: ['dit-legacy-audit-logs', personId] });
      showSaveMsg('Changes saved successfully');
    },
    onError: (err) => {
      showSaveMsg(err?.response?.data?.detail || 'Failed to save changes', 'error');
    },
  });

  const photoMutation = useMutation({
    mutationFn: (file) => ditLegacyApi.uploadPhoto(personId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dit-legacy-person', personId] });
      queryClient.invalidateQueries({ queryKey: ['dit-legacy-audit-logs', personId] });
      showSaveMsg('Photo uploaded successfully');
    },
    onError: () => {
      showSaveMsg('Failed to upload photo', 'error');
    },
  });

  // ── Save handlers ──
  const saveBio = () => {
    if (!Object.keys(bioForm).length) { setEditingBio(false); return; }
    updateMutation.mutate(bioForm, {
      onSuccess: () => { setEditingBio(false); setBioForm({}); },
    });
  };
  const saveLoc = () => {
    if (!Object.keys(locForm).length) { setEditingLocation(false); return; }
    updateMutation.mutate(locForm, {
      onSuccess: () => { setEditingLocation(false); setLocForm({}); },
    });
  };
  const saveSpec = () => {
    if (!Object.keys(specForm).length) { setEditingSpecial(false); return; }
    updateMutation.mutate(specForm, {
      onSuccess: () => { setEditingSpecial(false); setSpecForm({}); },
    });
  };

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) photoMutation.mutate(file);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Database className="h-4 w-4 text-cyan-700" />
            <span>DIT Legacy data</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">{fullName || 'Candidate'}</h1>
          <div className="mt-1 text-sm text-gray-500">Person ID: {personId}</div>
        </div>
        <Link
          to="/dit-legacy-data"
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to search
        </Link>
      </div>

      {/* Save notification */}
      {saveMsg && (
        <div className={`mb-4 flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium ${
          saveMsg.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
        }`}>
          <CheckCircle className="h-4 w-4" />
          {saveMsg.msg}
        </div>
      )}

      {personLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-12 justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-cyan-600 border-t-transparent" />
          Loading candidate...
        </div>
      ) : !person ? (
        <div className="text-sm text-red-600 py-12 text-center">Candidate not found.</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ─── Left column ─── */}
          <div className="lg:col-span-1 space-y-5">
            {/* Photo card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
                  <User className="h-4 w-4 text-cyan-700" />
                  Passport photo
                </div>
                <button
                  onClick={() => photoInputRef.current?.click()}
                  disabled={photoMutation.isPending}
                  className="inline-flex items-center gap-1 text-xs text-cyan-700 hover:text-cyan-800 hover:bg-cyan-50 px-2 py-1 rounded transition-colors"
                >
                  {photoMutation.isPending ? (
                    <div className="h-3 w-3 animate-spin rounded-full border-2 border-cyan-600 border-t-transparent" />
                  ) : (
                    <Upload className="h-3 w-3" />
                  )}
                  Upload
                </button>
                <input
                  ref={photoInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handlePhotoUpload}
                />
              </div>
              <div className="flex justify-center">
                {photoUrl ? (
                  <img
                    key={photoMutation.data ? 'refreshed' : 'initial'}
                    src={photoUrl + `?t=${Date.now()}`}
                    alt="Passport"
                    className="w-full max-w-[220px] aspect-[3/4] object-cover rounded-lg border border-gray-200 bg-gray-50 shadow-sm"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      const next = e.currentTarget.nextSibling;
                      if (next && next.style) next.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div
                  style={{ display: photoUrl ? 'none' : 'flex' }}
                  className="w-full max-w-[220px] aspect-[3/4] rounded-lg border border-dashed border-gray-300 bg-gray-50 items-center justify-center text-xs text-gray-400"
                >
                  No photo available
                </div>
              </div>
            </div>

            {/* Biodata card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <CardHeader
                icon={User}
                title="Biodata"
                editing={editingBio}
                saving={updateMutation.isPending}
                onEdit={() => { setEditingBio(true); setBioForm({}); }}
                onCancel={() => { setEditingBio(false); setBioForm({}); }}
                onSave={saveBio}
              />
              <div className="space-y-0.5">
                <EditableRow label="First name" fieldKey="first_name" value={person.first_name} editing={editingBio} form={bioForm} onChange={handleBioChange} />
                <EditableRow label="Other name" fieldKey="other_name" value={person.other_name} editing={editingBio} form={bioForm} onChange={handleBioChange} />
                <EditableRow label="Surname" fieldKey="surname" value={person.surname} editing={editingBio} form={bioForm} onChange={handleBioChange} />
                <InfoRow label="Registration No" value={person.registration_number} />
                <EditableSelectRow
                  label="Gender" fieldKey="gender" value={person.gender}
                  editing={editingBio} form={bioForm} onChange={handleBioChange}
                  options={[
                    { value: '', label: '—' },
                    { value: 'Male', label: 'Male' },
                    { value: 'Female', label: 'Female' },
                  ]}
                />
                <EditableDateRow label="Birth date" fieldKey="birth_date" value={person.birth_date} editing={editingBio} form={bioForm} onChange={handleBioChange} />
                <EditableRow label="National ID" fieldKey="national_id" value={person.national_id} editing={editingBio} form={bioForm} onChange={handleBioChange} />
                <EditableRow label="Telephone" fieldKey="telephone" value={person.telephone} editing={editingBio} form={bioForm} onChange={handleBioChange} />
                <EditableRow label="Email" fieldKey="email" value={person.email} editing={editingBio} form={bioForm} onChange={handleBioChange} />
              </div>
            </div>

            {/* Location card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <CardHeader
                icon={MapPin}
                title="Location"
                editing={editingLocation}
                saving={updateMutation.isPending}
                onEdit={() => { setEditingLocation(true); setLocForm({}); }}
                onCancel={() => { setEditingLocation(false); setLocForm({}); }}
                onSave={saveLoc}
              />
              <div className="space-y-0.5">
                <EditableRow label="District" fieldKey="district" value={person.district} editing={editingLocation} form={locForm} onChange={handleLocChange} />
                <EditableRow label="Sub county" fieldKey="subcounty" value={person.subcounty} editing={editingLocation} form={locForm} onChange={handleLocChange} />
                <EditableRow label="Village" fieldKey="village" value={person.village} editing={editingLocation} form={locForm} onChange={handleLocChange} />
                <EditableRow label="Home address" fieldKey="home_address" value={person.home_address} editing={editingLocation} form={locForm} onChange={handleLocChange} />
              </div>
            </div>

            {/* Special needs card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <CardHeader
                icon={Shield}
                title="Special needs"
                editing={editingSpecial}
                saving={updateMutation.isPending}
                onEdit={() => { setEditingSpecial(true); setSpecForm({}); }}
                onCancel={() => { setEditingSpecial(false); setSpecForm({}); }}
                onSave={saveSpec}
              />
              <div className="space-y-0.5">
                <EditableSelectRow
                  label="Has disability" fieldKey="disability_option"
                  value={person.disability_option || (person.disability_name ? 'Yes' : 'No')}
                  editing={editingSpecial} form={specForm} onChange={handleSpecChange}
                  options={[
                    { value: 'No', label: 'No' },
                    { value: 'Yes', label: 'Yes' },
                  ]}
                />
                <EditableRow label="Disability" fieldKey="disability_name" value={person.disability_name} editing={editingSpecial} form={specForm} onChange={handleSpecChange} />
              </div>
            </div>
          </div>

          {/* ─── Right column ─── */}
          <div className="lg:col-span-2 space-y-5">
            {/* Training card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-4">
                <BookOpen className="h-4 w-4 text-cyan-700" />
                Training
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 text-sm">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Training provider</div>
                  <div className="text-gray-900 font-medium mt-0.5">{person.training_provider || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">District</div>
                  <div className="text-gray-900 font-medium mt-0.5">{person.training_provider_district || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Occupation</div>
                  <div className="text-gray-900 font-medium mt-0.5">{person.occupation || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Level</div>
                  <div className="text-gray-900 font-medium mt-0.5">{person.level || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Assessment date</div>
                  <div className="text-gray-900 font-medium mt-0.5">{fmtDate(person.actual_assessment_date)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Certificate number</div>
                  <div className="text-gray-900 font-medium mt-0.5">{person.certificate_number || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Academic level</div>
                  <div className="text-gray-900 font-medium mt-0.5">{person.academic_level || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Academic school</div>
                  <div className="text-gray-900 font-medium mt-0.5">{person.academic_school || '—'}</div>
                </div>
              </div>
            </div>

            {/* Exam Results card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
                  <Award className="h-4 w-4 text-cyan-700" />
                  Exam Results
                </div>
                {examResults.length > 0 && (
                  <span className="text-xs text-gray-500">{examResults.length} paper{examResults.length !== 1 ? 's' : ''}</span>
                )}
              </div>

              {resultsLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-600 border-t-transparent" />
                  Loading results...
                </div>
              ) : examResults.length > 0 ? (
                <div className="overflow-x-auto -mx-5 px-5">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Paper</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Exam Date</th>
                        <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Mark</th>
                        <th className="px-3 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Grade</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Comment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {examResults.map((r, idx) => (
                        <tr key={idx} className={`hover:bg-gray-50/50 transition-colors ${idx % 2 === 0 ? '' : 'bg-gray-50/30'}`}>
                          <td className="px-3 py-2.5 text-gray-900 font-medium whitespace-nowrap">{r.paper || '—'}</td>
                          <td className="px-3 py-2.5 text-gray-600 whitespace-nowrap">{r.exam_date || '—'}</td>
                          <td className="px-3 py-2.5 text-right font-mono text-gray-900">{r.exam_mark || '—'}</td>
                          <td className="px-3 py-2.5 text-center">
                            {r.exam_grade ? (
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${gradeColor(r.exam_grade)}`}>
                                {r.exam_grade}
                              </span>
                            ) : '—'}
                          </td>
                          <td className={`px-3 py-2.5 text-sm font-medium ${commentColor(r.exam_comment)}`}>
                            {r.exam_comment || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : registrations.length > 0 ? (
                <div className="text-sm text-gray-500 py-2">
                  No detailed exam results available yet. Registration data shown below.
                </div>
              ) : (
                <div className="text-sm text-gray-500 py-2">No results found for this candidate.</div>
              )}
            </div>

            {/* Registration History card */}
            {registrations.length > 0 && (
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-4">
                  <Database className="h-4 w-4 text-cyan-700" />
                  Registration History
                </div>
                <div className="overflow-x-auto -mx-5 px-5">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Provider</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Occupation</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Level</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Year</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Modules</th>
                        <th className="px-3 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {registrations.map((r, idx) => (
                        <tr key={idx} className="hover:bg-gray-50/50 transition-colors">
                          <td className="px-3 py-2.5 text-gray-900 font-medium max-w-[200px] truncate" title={r.training_provider}>
                            {r.training_provider || '—'}
                          </td>
                          <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap">{r.occupation || '—'}</td>
                          <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap">{r.level || '—'}</td>
                          <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap">{r.assessment_year || '—'}</td>
                          <td className="px-3 py-2.5 text-gray-600 font-mono text-xs">{r.modules_assessed || '—'}</td>
                          <td className="px-3 py-2.5 text-center">
                            {r.completed ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                Completed
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                Pending
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Audit Logs card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-4">
                <Clock className="h-4 w-4 text-cyan-700" />
                Audit Logs
              </div>
              {logsLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-600 border-t-transparent" />
                  Loading logs...
                </div>
              ) : auditLogs.length > 0 ? (
                <div className="overflow-x-auto -mx-5 px-5">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Date</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Field</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Old Value</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">New Value</th>
                        <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Changed By</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {auditLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-gray-50/50 transition-colors">
                          <td className="px-3 py-2.5 text-gray-600 whitespace-nowrap text-xs">
                            {fmtDateTime(log.changed_at)}
                          </td>
                          <td className="px-3 py-2.5 text-gray-900 font-medium whitespace-nowrap">
                            {log.field_name}
                          </td>
                          <td className="px-3 py-2.5 text-red-600 max-w-[150px] truncate" title={log.old_value}>
                            {log.old_value || '—'}
                          </td>
                          <td className="px-3 py-2.5 text-green-600 max-w-[150px] truncate" title={log.new_value}>
                            {log.new_value || '—'}
                          </td>
                          <td className="px-3 py-2.5 text-gray-600 whitespace-nowrap">
                            {log.changed_by_name || 'System'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-gray-500 py-2">No changes recorded for this candidate.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
