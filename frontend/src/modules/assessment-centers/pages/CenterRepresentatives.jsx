import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Users2,
  Plus,
  Edit2,
  Trash2,
  X,
  Phone,
  Mail,
  MapPin,
  CreditCard,
  Globe,
} from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../../../services/apiClient';
import assessmentCenterApi from '../services/assessmentCenterApi';

const CenterRepresentatives = () => {
  const { id: centerId } = useParams();
  const navigate = useNavigate();

  const [center, setCenter] = useState(null);
  const [representatives, setRepresentatives] = useState([]);
  const [designations, setDesignations] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingRep, setEditingRep] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [formErrors, setFormErrors] = useState({});

  const emptyForm = {
    assessment_center: centerId,
    designation: '',
    name: '',
    phone: '',
    email: '',
    nin: '',
    country: 'Uganda',
    district: '',
  };
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    fetchAll();
  }, [centerId]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      const [centerRes, repsRes, desRes, distRes] = await Promise.all([
        assessmentCenterApi.getById(centerId),
        assessmentCenterApi.representativePersons.getByCenter(centerId),
        assessmentCenterApi.designations.getAll(),
        apiClient.get('/configurations/districts/'),
      ]);
      setCenter(centerRes.data);
      const repsData = repsRes.data?.results || repsRes.data;
      setRepresentatives(Array.isArray(repsData) ? repsData : []);
      const desData = desRes.data?.results || desRes.data;
      setDesignations(Array.isArray(desData) ? desData : []);
      const distData = distRes.data?.results || distRes.data;
      setDistricts(Array.isArray(distData) ? distData : []);
    } catch (err) {
      console.error('Error loading data:', err);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingRep(null);
    setForm({ ...emptyForm, assessment_center: centerId });
    setFormErrors({});
    setShowModal(true);
  };

  const handleOpenEdit = (rep) => {
    setEditingRep(rep);
    setForm({
      assessment_center: centerId,
      designation: rep.designation || '',
      name: rep.name || '',
      phone: rep.phone || '',
      email: rep.email || '',
      nin: rep.nin || '',
      country: rep.country || 'Uganda',
      district: rep.district || '',
    });
    setFormErrors({});
    setShowModal(true);
  };

  const handleCloseModal = () => {
    if (!saving) {
      setShowModal(false);
      setEditingRep(null);
      setFormErrors({});
    }
  };

  const handleSave = async () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.designation) errs.designation = 'Designation is required';
    if (Object.keys(errs).length > 0) {
      setFormErrors(errs);
      return;
    }
    setFormErrors({});

    try {
      setSaving(true);
      const payload = {
        ...form,
        district: form.district || null,
      };
      if (editingRep) {
        await assessmentCenterApi.representativePersons.update(editingRep.id, payload);
        toast.success('Representative updated');
      } else {
        await assessmentCenterApi.representativePersons.create(payload);
        toast.success('Representative added');
      }
      setShowModal(false);
      setEditingRep(null);
      fetchAll();
    } catch (err) {
      console.error('Save error:', err);
      const msg = err.response?.data;
      if (msg && typeof msg === 'object') {
        const firstKey = Object.keys(msg)[0];
        const firstErr = Array.isArray(msg[firstKey]) ? msg[firstKey][0] : msg[firstKey];
        toast.error(String(firstErr));
      } else {
        toast.error('Failed to save representative');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (rep) => {
    if (!window.confirm(`Are you sure you want to remove ${rep.name}?`)) return;
    try {
      setDeleting(rep.id);
      await assessmentCenterApi.representativePersons.delete(rep.id);
      toast.success('Representative removed');
      fetchAll();
    } catch (err) {
      console.error('Delete error:', err);
      toast.error('Failed to remove representative');
    } finally {
      setDeleting(null);
    }
  };

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (formErrors[field]) setFormErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/assessment-centers/${centerId}`)}
          className="inline-flex items-center px-3 py-1.5 text-sm text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Center
        </button>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Users2 className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Center Representatives</h1>
              <p className="text-sm text-gray-500">
                {center?.center_name} — {center?.center_number}
              </p>
            </div>
          </div>
          <button
            onClick={handleOpenCreate}
            className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Representative
          </button>
        </div>
      </div>

      {/* Representatives List */}
      {representatives.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Users2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-700 mb-1">No representatives yet</h3>
          <p className="text-sm text-gray-500 mb-4">
            Add center representatives such as Head of Center, Academic Registrar, or Director of Studies.
          </p>
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add First Representative
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {representatives.map((rep) => (
            <div
              key={rep.id}
              className="bg-white rounded-lg shadow border border-gray-200 hover:border-purple-300 transition-colors"
            >
              <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">{rep.name}</h3>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 mt-1">
                      {rep.designation_name}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => handleOpenEdit(rep)}
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(rep)}
                      disabled={deleting === rep.id}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50"
                      title="Remove"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  {rep.phone && (
                    <div className="flex items-center text-gray-600">
                      <Phone className="w-3.5 h-3.5 mr-2 text-gray-400" />
                      {rep.phone}
                    </div>
                  )}
                  {rep.email && (
                    <div className="flex items-center text-gray-600">
                      <Mail className="w-3.5 h-3.5 mr-2 text-gray-400" />
                      {rep.email}
                    </div>
                  )}
                  {rep.nin && (
                    <div className="flex items-center text-gray-600">
                      <CreditCard className="w-3.5 h-3.5 mr-2 text-gray-400" />
                      {rep.nin}
                    </div>
                  )}
                  {rep.country && (
                    <div className="flex items-center text-gray-600">
                      <Globe className="w-3.5 h-3.5 mr-2 text-gray-400" />
                      {rep.country}
                    </div>
                  )}
                  {rep.district_name && (
                    <div className="flex items-center text-gray-600">
                      <MapPin className="w-3.5 h-3.5 mr-2 text-gray-400" />
                      {rep.district_name}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={handleCloseModal} />
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white z-10 flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users2 className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingRep ? 'Edit Representative' : 'Add Representative'}
                </h3>
              </div>
              {!saving && (
                <button onClick={handleCloseModal} className="p-1.5 hover:bg-gray-100 rounded-lg">
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              )}
            </div>

            {/* Modal Body */}
            <div className="px-6 py-5 space-y-4">
              {/* Center (auto-filled) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Center</label>
                <input
                  type="text"
                  value={center ? `${center.center_name} (${center.center_number})` : ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-600"
                />
              </div>

              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${formErrors.name ? 'border-red-400' : 'border-gray-300'}`}
                  placeholder="Full name"
                />
                {formErrors.name && <p className="text-xs text-red-500 mt-1">{formErrors.name}</p>}
              </div>

              {/* Designation */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Designation *</label>
                <select
                  value={form.designation}
                  onChange={(e) => updateField('designation', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${formErrors.designation ? 'border-red-400' : 'border-gray-300'}`}
                >
                  <option value="">-- Select Designation --</option>
                  {designations.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
                {formErrors.designation && <p className="text-xs text-red-500 mt-1">{formErrors.designation}</p>}
              </div>

              {/* Phone & Email */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="text"
                    value={form.phone}
                    onChange={(e) => updateField('phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g. +256700000000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => updateField('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="email@example.com"
                  />
                </div>
              </div>

              {/* NIN */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">NIN</label>
                <input
                  type="text"
                  value={form.nin}
                  onChange={(e) => updateField('nin', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="National ID Number"
                />
              </div>

              {/* Country & District */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                  <input
                    type="text"
                    value={form.country}
                    onChange={(e) => updateField('country', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="Country"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">District</label>
                  <select
                    value={form.district}
                    onChange={(e) => updateField('district', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">-- Select District --</option>
                    {districts.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 flex items-center justify-end space-x-3 px-6 py-4 border-t border-gray-200">
              <button
                onClick={handleCloseModal}
                disabled={saving}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium"
              >
                {saving ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  editingRep ? 'Update' : 'Save'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CenterRepresentatives;
