import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Search, ChevronLeft, ChevronRight, User, Filter, ArrowLeft, Download, X, Edit2, Upload, CheckCircle, AlertCircle, FileSpreadsheet, ClipboardList, Paperclip, Printer } from 'lucide-react';
import * as XLSX from 'xlsx';
import { toast } from 'sonner';
import apiClient from '../../../services/apiClient';
import SignaturePad from '../../../shared/components/SignaturePad';

const TranscriptLogs = () => {
  const navigate = useNavigate();
  const [awards, setAwards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [showCollectionModal, setShowCollectionModal] = useState(false);
  const [selectedAward, setSelectedAward] = useState(null);
  const [collectionForm, setCollectionForm] = useState({
    collected: false,
    collector_name: '',
    collector_phone: '',
    collection_date: '',
  });
  const [saving, setSaving] = useState(false);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [selectAllFiltered, setSelectAllFiltered] = useState(false);
  const [uniqueCenters, setUniqueCenters] = useState([]);
  const [exporting, setExporting] = useState(false);
  const itemsPerPage = 50;
  const searchTimerRef = useRef(null);

  // Bulk upload states
  const [showBulkUploadModal, setShowBulkUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResults, setUploadResults] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // Collect transcripts states
  const [showCollectModal, setShowCollectModal] = useState(false);
  const [collectForm, setCollectForm] = useState({
    designation: '',
    nin: '',
    collector_name: '',
    collector_phone: '',
    email: '',
    collection_date: new Date().toISOString().slice(0, 10),
    signature_data: '',
    supporting_document: null,
  });
  const [collecting, setCollecting] = useState(false);
  const [collectErrors, setCollectErrors] = useState({});
  const [receiptData, setReceiptData] = useState(null);
  const supportingDocRef = useRef(null);
  const [configDesignations, setConfigDesignations] = useState([]);
  const [centerRepPersons, setCenterRepPersons] = useState([]);
  const [collectFieldsLocked, setCollectFieldsLocked] = useState(false);

  // Build designation options: config items + static Candidate / Other Person
  const DESIGNATION_OPTIONS = [
    ...configDesignations.map((d) => ({ value: d.name, label: d.name, isConfig: true })),
    { value: 'candidate', label: 'Candidate', isConfig: false },
    { value: 'other_person', label: 'Other Person', isConfig: false },
  ];

  // Filter states
  const [filters, setFilters] = useState({
    center: '',
    collection_status: '',
  });

  const buildQueryParams = useCallback((page = 1, overrides = {}) => {
    const params = new URLSearchParams();
    params.set('page', page);
    params.set('page_size', itemsPerPage);
    params.set('printed', 'yes');
    const search = overrides.search !== undefined ? overrides.search : searchQuery;
    if (search) params.set('search', search);
    const f = overrides.filters || filters;
    if (f.center) params.set('center', f.center);
    if (f.collection_status) params.set('collection_status', f.collection_status);
    return params.toString();
  }, [searchQuery, filters]);

  const fetchPrintedAwards = useCallback(async (page = 1, overrides = {}) => {
    try {
      setLoading(true);
      const qs = buildQueryParams(page, overrides);
      const response = await apiClient.get(`/awards/?${qs}`);
      setAwards(response.data.results || []);
      setTotalCount(response.data.count || 0);
      setTotalPages(response.data.num_pages || 1);
      setCurrentPage(response.data.current_page || page);
      setError(null);
    } catch (err) {
      console.error('Error fetching awards:', err);
      setError('Failed to load transcript logs');
    } finally {
      setLoading(false);
    }
  }, [buildQueryParams]);

  const fetchFilterOptions = async () => {
    try {
      const response = await apiClient.get('/awards/filter-options/');
      setUniqueCenters(response.data.centers || []);
    } catch (err) {
      console.error('Error fetching filter options:', err);
    }
  };

  useEffect(() => {
    fetchPrintedAwards(1);
    fetchFilterOptions();
  }, []);

  // Debounced search
  const handleSearchChange = (value) => {
    setSearchQuery(value);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      setCurrentPage(1);
      setSelectedCandidates([]);
      setSelectAllFiltered(false);
      fetchPrintedAwards(1, { search: value });
    }, 400);
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
    setSelectedCandidates([]);
    setSelectAllFiltered(false);
    fetchPrintedAwards(1, { filters: newFilters });
  };

  // Clear filters
  const handleClearFilters = () => {
    const empty = { center: '', collection_status: '' };
    setFilters(empty);
    setSearchQuery('');
    setCurrentPage(1);
    setSelectedCandidates([]);
    setSelectAllFiltered(false);
    fetchPrintedAwards(1, { search: '', filters: empty });
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    setSelectedCandidates([]);
    fetchPrintedAwards(page);
  };

  const startIndex = (currentPage - 1) * itemsPerPage;

  // Open collection modal
  const handleOpenCollectionModal = (award, e) => {
    e.stopPropagation();
    setSelectedAward(award);
    setCollectionForm({
      collected: award.transcript_collected || false,
      collector_name: award.transcript_collector_name || '',
      collector_phone: award.transcript_collector_phone || '',
      collection_date: award.transcript_collection_date || '',
    });
    setShowCollectionModal(true);
  };

  // Save collection status
  const handleSaveCollection = async () => {
    if (collectionForm.collected && !collectionForm.collector_name) {
      toast.error('Collector name is required');
      return;
    }
    try {
      setSaving(true);
      await apiClient.post('/awards/update-collection-status/', {
        candidate_id: selectedAward.id,
        collected: collectionForm.collected,
        collector_name: collectionForm.collector_name,
        collector_phone: collectionForm.collector_phone,
        collection_date: collectionForm.collection_date || null,
      });
      toast.success('Collection status updated');
      setShowCollectionModal(false);
      fetchPrintedAwards(currentPage);
    } catch (err) {
      console.error('Error updating collection status:', err);
      toast.error(err.response?.data?.error || 'Failed to update collection status');
    } finally {
      setSaving(false);
    }
  };

  // Selection handlers
  const handleSelectAll = () => {
    if (selectedCandidates.length === awards.length && !selectAllFiltered) {
      setSelectedCandidates([]);
      setSelectAllFiltered(false);
    } else {
      setSelectedCandidates(awards.map((a) => a.id));
    }
  };

  const handleSelectAllFiltered = () => {
    setSelectAllFiltered(true);
    setSelectedCandidates(awards.map((a) => a.id));
  };

  const handleClearSelection = () => {
    setSelectedCandidates([]);
    setSelectAllFiltered(false);
  };

  const handleSelectCandidate = (id, e) => {
    e.stopPropagation();
    setSelectAllFiltered(false);
    if (selectedCandidates.includes(id)) {
      setSelectedCandidates(selectedCandidates.filter((cId) => cId !== id));
    } else {
      setSelectedCandidates([...selectedCandidates, id]);
    }
  };

  // Export to Excel handler
  const handleExportExcel = async (exportType) => {
    try {
      setExporting(true);
      let dataToExport = [];

      if (exportType === 'selected' && !selectAllFiltered) {
        dataToExport = awards.filter((a) => selectedCandidates.includes(a.id));
      } else {
        const qs = buildQueryParams(1);
        const params = new URLSearchParams(qs);
        params.set('page_size', '0');
        const response = await apiClient.get(`/awards/?${params.toString()}`);
        dataToExport = response.data.results || [];
      }

      if (dataToExport.length === 0) {
        toast.error('No data to export');
        return;
      }

      const exportData = dataToExport.map((award, index) => ({
        '#': index + 1,
        'Reg No': award.registration_number || '',
        'Name': award.full_name || '',
        'Center': award.center_name || '',
        'TR SNo': award.tr_sno || '',
        'Collection Status': award.transcript_collected ? 'Taken' : 'Not Taken',
        'Collector Name': award.transcript_collector_name || '',
        'Collector No': award.transcript_collector_phone || '',
        'Collection Date': award.transcript_collection_date || '',
      }));

      const worksheet = XLSX.utils.json_to_sheet(exportData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Transcript Logs');

      const colWidths = Object.keys(exportData[0]).map((key) => ({
        wch: Math.max(key.length, ...exportData.map((row) => String(row[key]).length)) + 2,
      }));
      worksheet['!cols'] = colWidths;

      const filename = exportType === 'selected'
        ? `Transcript_Logs_Selected_${dataToExport.length}_${new Date().toISOString().slice(0, 10)}.xlsx`
        : `Transcript_Logs_All_${dataToExport.length}_${new Date().toISOString().slice(0, 10)}.xlsx`;
      XLSX.writeFile(workbook, filename);
      toast.success(`Exported ${dataToExport.length} record(s) to Excel`);
    } catch (err) {
      console.error('Export error:', err);
      toast.error('Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  // Bulk upload handler
  const handleBulkUpload = async () => {
    if (!uploadFile) {
      toast.error('Please select an Excel file');
      return;
    }
    try {
      setUploading(true);
      setUploadProgress(0);
      setUploadResults(null);

      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await apiClient.post('/awards/bulk-upload-serial-numbers/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(pct);
        },
      });

      setUploadResults(response.data);
      if (response.data.success_count > 0) {
        toast.success(`${response.data.success_count} serial number(s) uploaded successfully`);
        fetchPrintedAwards(currentPage);
      }
      if (response.data.error_count > 0) {
        toast.error(`${response.data.error_count} row(s) had errors`);
      }
    } catch (err) {
      console.error('Bulk upload error:', err);
      const msg = err.response?.data?.error || 'Failed to upload file';
      toast.error(msg);
      setUploadResults({ error: msg });
    } finally {
      setUploading(false);
    }
  };

  const handleCloseBulkUpload = () => {
    setShowBulkUploadModal(false);
    setUploadFile(null);
    setUploadProgress(0);
    setUploadResults(null);
    setDragOver(false);
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      setUploadFile(file);
      setUploadResults(null);
    } else {
      toast.error('Please upload an Excel file (.xlsx or .xls)');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadFile(file);
      setUploadResults(null);
    }
  };

  // --- Collect Transcripts Logic ---

  // Get selected candidates' data
  const getSelectedAwards = () => awards.filter((a) => selectedCandidates.includes(a.id));

  // Check if all selected candidates are from the same center
  const getSelectedCenter = () => {
    const selected = getSelectedAwards();
    if (selected.length === 0) return null;
    const centers = [...new Set(selected.map((a) => a.center_name))];
    return centers.length === 1 ? centers[0] : null;
  };

  // Check if any selected candidate is already collected
  const hasAlreadyCollected = () => getSelectedAwards().some((a) => a.transcript_collected);

  // Can collect: same center, none already collected, not select-all-filtered (need concrete IDs)
  const canCollect = () => {
    if (selectAllFiltered) return false;
    if (selectedCandidates.length === 0) return false;
    if (hasAlreadyCollected()) return false;
    return getSelectedCenter() !== null;
  };

  const handleOpenCollectModal = async () => {
    const centerName = getSelectedCenter();
    if (!centerName) {
      toast.error('All selected candidates must belong to the same center');
      return;
    }
    if (hasAlreadyCollected()) {
      toast.error('Some selected candidates have already had their transcripts collected');
      return;
    }
    setCollectForm({
      designation: '',
      nin: '',
      collector_name: '',
      collector_phone: '',
      email: '',
      collection_date: new Date().toISOString().slice(0, 10),
      signature_data: '',
      supporting_document: null,
    });
    setCollectErrors({});
    setReceiptData(null);
    setCollectFieldsLocked(false);

    // Fetch config designations + center rep persons for this center
    try {
      const selected = getSelectedAwards();
      const centerId = selected[0]?.center_id;
      const [desRes, repsRes] = await Promise.all([
        apiClient.get('/configurations/center-representatives/'),
        centerId ? apiClient.get('/assessment-centers/representative-persons/', { params: { assessment_center: centerId } }) : Promise.resolve({ data: [] }),
      ]);
      const desData = desRes.data?.results || desRes.data;
      setConfigDesignations(Array.isArray(desData) ? desData.filter((d) => d.is_active) : []);
      const repsData = repsRes.data?.results || repsRes.data;
      setCenterRepPersons(Array.isArray(repsData) ? repsData : []);
    } catch (err) {
      console.error('Error fetching designations/reps:', err);
      setConfigDesignations([]);
      setCenterRepPersons([]);
    }

    setShowCollectModal(true);
  };

  const handleCloseCollectModal = () => {
    if (!collecting) {
      setShowCollectModal(false);
      setCollectErrors({});
      setReceiptData(null);
    }
  };

  const handleCollectTranscripts = async () => {
    // Client-side validation
    const errs = {};
    if (!collectForm.designation) errs.designation = 'Required';
    if (!collectForm.nin) errs.nin = 'Required';
    if (!collectForm.collector_name) errs.collector_name = 'Required';
    if (!collectForm.collector_phone) errs.collector_phone = 'Required';
    if (!collectForm.email) errs.email = 'Required';
    if (['candidate', 'other_person'].includes(collectForm.designation) && !collectForm.supporting_document) {
      errs.supporting_document = 'Supporting document is required for this designation';
    }
    if (Object.keys(errs).length > 0) {
      setCollectErrors(errs);
      return;
    }
    setCollectErrors({});

    try {
      setCollecting(true);
      const formData = new FormData();
      formData.append('candidate_ids', selectedCandidates.join(','));
      formData.append('designation', collectForm.designation);
      formData.append('nin', collectForm.nin);
      formData.append('collector_name', collectForm.collector_name);
      formData.append('collector_phone', collectForm.collector_phone);
      formData.append('email', collectForm.email);
      formData.append('collection_date', collectForm.collection_date);
      if (collectForm.signature_data) {
        formData.append('signature_data', collectForm.signature_data);
      }
      if (collectForm.supporting_document) {
        formData.append('supporting_document', collectForm.supporting_document);
      }

      const response = await apiClient.post('/awards/collect-transcripts/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setReceiptData(response.data.receipt);
      toast.success(response.data.message);
      fetchPrintedAwards(currentPage);
      setSelectedCandidates([]);
      setSelectAllFiltered(false);
    } catch (err) {
      console.error('Collect transcripts error:', err);
      if (err.response?.data?.errors) {
        setCollectErrors(err.response.data.errors);
      } else {
        toast.error(err.response?.data?.error || 'Failed to collect transcripts');
      }
    } finally {
      setCollecting(false);
    }
  };

  const handlePrintReceipt = async () => {
    if (!receiptData) return;

    // Get logged-in user
    let clearedByName = '';
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{}');
      clearedByName = (u.first_name && u.last_name) ? `${u.first_name} ${u.last_name}` : u.first_name || u.username || '';
    } catch (_) {}

    // Generate QR code
    const qrText = [
      `Collection Reference: ${receiptData.receipt_number}`,
      `Collector Name: ${receiptData.collector_name}`,
      `Center: ${receiptData.center_name}`,
      `Collection Date & Time: ${receiptData.collection_date}`,
      `Collector Type: ${receiptData.designation}`,
    ].join('\n');
    let qrDataUrl = '';
    try {
      const QRCode = (await import('qrcode')).default;
      qrDataUrl = await QRCode.toDataURL(qrText, { width: 120, margin: 1 });
    } catch (_) {}

    const logoUrl = window.location.origin + '/uvtab-logo.png';

    const candidateRows = receiptData.candidates.map((c, i) =>
      `<tr><td style="padding:6px 12px;border:1px solid #ddd;text-align:center">${i + 1}</td><td style="padding:6px 12px;border:1px solid #ddd">${c.registration_number}</td><td style="padding:6px 12px;border:1px solid #ddd">${c.full_name}</td><td style="padding:6px 12px;border:1px solid #ddd">${c.tr_sno}</td></tr>`
    ).join('');

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Collection Receipt - ${receiptData.receipt_number}</title>
        <style>
          body { font-family: 'Times New Roman', Times, serif; padding: 30px; color: #333; max-width: 800px; margin: 0 auto; }
          .header { text-align: center; border-bottom: 2px solid #1a237e; padding-bottom: 15px; margin-bottom: 25px; }
          .header h2 { font-size: 16px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 10px; }
          .header-content { display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 10px; }
          .header-left { text-align: right; font-size: 12px; line-height: 1.6; }
          .header-right { text-align: left; font-size: 12px; line-height: 1.6; }
          .header-logo img { width: 70px; height: 70px; }
          .header-title { font-size: 14px; font-weight: bold; text-transform: uppercase; margin-top: 8px; }
          .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 30px; margin-bottom: 20px; padding: 12px; border: 1px solid #ddd; border-radius: 4px; }
          .info-item { display: flex; }
          .info-label { font-weight: bold; font-size: 12px; color: #555; min-width: 130px; }
          .info-value { font-size: 12px; }
          table { width: 100%; border-collapse: collapse; margin-top: 10px; }
          th { background: #f3f4f6; padding: 8px 12px; text-align: left; border: 1px solid #ddd; font-size: 11px; text-transform: uppercase; color: #555; }
          td { font-size: 13px; }
          .footer { margin-top: 30px; display: flex; justify-content: space-between; }
          .sig-box { width: 250px; text-align: center; }
          .sig-box .line { border-top: 1px solid #333; margin-top: 50px; padding-top: 5px; font-size: 12px; color: #666; }
          .official-section { margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px; }
          .official-title { font-weight: bold; font-size: 14px; font-style: italic; }
          .cleared-by { font-size: 13px; color: #333; margin-top: 4px; }
          .cleared-by em { font-style: italic; font-weight: bold; }
          .qr-section { text-align: center; margin-top: 15px; }
          @media print { body { padding: 15px; } }
        </style>
      </head>
      <body>
        <div class="header">
          <h2>Uganda Vocational and Technical Assessment Board</h2>
          <div class="header-content">
            <div class="header-left">
              Address: P.O.Box 1499,<br/>
              Kampala,<br/>
              Email: info@uvtab.go.ug
            </div>
            <div class="header-logo">
              <img src="${logoUrl}" alt="UVTAB Logo" />
            </div>
            <div class="header-right">
              Tel: 0392002468
            </div>
          </div>
          <div class="header-title">Transcript Collection Receipt</div>
        </div>
        <div class="info-grid">
          <div class="info-item"><span class="info-label">Reference:</span><span class="info-value">${receiptData.receipt_number}</span></div>
          <div class="info-item"><span class="info-label">Collection Date:</span><span class="info-value">${receiptData.collection_date}</span></div>
          <div class="info-item"><span class="info-label">Collector Name:</span><span class="info-value">${receiptData.collector_name}</span></div>
          <div class="info-item"><span class="info-label">Center:</span><span class="info-value">${receiptData.center_name}</span></div>
          <div class="info-item"><span class="info-label">NIN:</span><span class="info-value">${receiptData.nin}</span></div>
          <div class="info-item"><span class="info-label">Candidates:</span><span class="info-value">${receiptData.candidate_count}</span></div>
          <div class="info-item"><span class="info-label">Designation:</span><span class="info-value">${receiptData.designation}</span></div>
          <div class="info-item"><span class="info-label">Phone:</span><span class="info-value">${receiptData.collector_phone}</span></div>
          <div class="info-item"><span class="info-label">Email:</span><span class="info-value">${receiptData.email}</span></div>
        </div>
        <h3 style="font-size:14px;margin-bottom:5px;">Candidates (${receiptData.candidate_count})</h3>
        <table>
          <thead><tr><th>#</th><th>Reg No</th><th>Name</th><th>TR SNo</th></tr></thead>
          <tbody>${candidateRows}</tbody>
        </table>
        <div class="footer">
          <div class="sig-box">
            ${collectForm.signature_data
              ? `<img src="${collectForm.signature_data}" style="max-width:250px;max-height:80px;display:block;margin:0 auto 5px;" /><div style="border-top:1px solid #333;padding-top:5px;font-size:12px;color:#666;">Collector Signature</div>`
              : `<div class="line">Collector Signature</div>`
            }
          </div>
          <div class="sig-box"><div class="line">Authorized Officer</div></div>
        </div>
        <div class="official-section">
          <div class="official-title">Official</div>
          <div class="cleared-by">Issued By: <em>${clearedByName}</em></div>
        </div>
        ${qrDataUrl ? `<div class="qr-section"><img src="${qrDataUrl}" alt="QR Code" style="width:120px;height:120px;" /></div>` : ''}
        <script>window.onload = function() { window.print(); }</script>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-600 p-4 rounded-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/awards')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="p-2 bg-blue-100 rounded-lg">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transcript Logs</h1>
            <p className="text-sm text-gray-500">
              Candidates whose transcripts have been printed
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/awards/collection-receipts')}
            className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
          >
            <ClipboardList className="w-4 h-4 mr-2" />
            Collection Receipts
          </button>
          <button
            onClick={() => setShowBulkUploadModal(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            <Upload className="w-4 h-4 mr-2" />
            Bulk Upload Serial No
          </button>
          <button
            onClick={() => handleExportExcel('all')}
            className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export All ({totalCount})
          </button>
          <div className="text-sm text-gray-500">
            Total: <span className="font-semibold text-gray-900">{totalCount}</span> printed
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, reg no, center, TR SNo, collector name..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center px-4 py-2 rounded-lg border ${
                showFilters ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-4 border-t">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Center</label>
                <select
                  value={filters.center}
                  onChange={(e) => handleFilterChange({ ...filters, center: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  {uniqueCenters.map((center) => (
                    <option key={center} value={center}>{center}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Collection Status</label>
                <select
                  value={filters.collection_status}
                  onChange={(e) => handleFilterChange({ ...filters, collection_status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  <option value="taken">Taken</option>
                  <option value="not_taken">Not Taken</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleClearFilters}
                  className="w-full px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {(selectedCandidates.length > 0 || selectAllFiltered) && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-blue-900">
                {selectAllFiltered ? (
                  <>All {totalCount} candidates selected</>
                ) : (
                  <>{selectedCandidates.length} candidate(s) selected</>
                )}
              </span>
              {selectedCandidates.length === awards.length && !selectAllFiltered && totalCount > itemsPerPage && (
                <button
                  onClick={handleSelectAllFiltered}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Select all {totalCount} candidates
                </button>
              )}
              <button
                onClick={handleClearSelection}
                className="text-sm text-gray-600 hover:text-gray-800 underline"
              >
                Clear selection
              </button>
            </div>
            <div className="flex items-center space-x-2">
              {!selectAllFiltered && selectedCandidates.length > 0 && (
                <button
                  onClick={handleOpenCollectModal}
                  disabled={!canCollect()}
                  className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title={!canCollect() ? (
                    hasAlreadyCollected() ? 'Some candidates already collected' :
                    !getSelectedCenter() ? 'Selected candidates must be from the same center' :
                    'Cannot collect'
                  ) : 'Collect Transcripts'}
                >
                  <ClipboardList className="w-4 h-4 mr-2" />
                  Collect Transcripts
                </button>
              )}
              <button
                onClick={() => handleExportExcel('selected')}
                className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Export Selected
              </button>
            </div>
          </div>
          {/* Same-center warning */}
          {!selectAllFiltered && selectedCandidates.length > 1 && !getSelectedCenter() && (
            <div className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-1.5">
              Selected candidates are from different centers. To collect transcripts, all must be from the same center.
            </div>
          )}
          {!selectAllFiltered && selectedCandidates.length > 0 && hasAlreadyCollected() && (
            <div className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-1.5">
              Some selected candidates have already had their transcripts collected. Remove them from selection to collect.
            </div>
          )}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={awards.length > 0 && selectedCandidates.length === awards.length}
                    onChange={handleSelectAll}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Image
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reg No
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Center
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  TR SNo
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collector Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collector No
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {awards.length === 0 ? (
                <tr>
                  <td colSpan="11" className="px-4 py-8 text-center text-gray-500">
                    No printed transcripts found
                  </td>
                </tr>
              ) : (
                awards.map((award) => (
                  <tr
                    key={award.id}
                    className={`hover:bg-gray-50 ${selectedCandidates.includes(award.id) ? 'bg-blue-50' : ''}`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedCandidates.includes(award.id)}
                        onChange={(e) => handleSelectCandidate(award.id, e)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {award.passport_photo ? (
                        <img
                          src={award.passport_photo}
                          alt={award.full_name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                          <User className="w-5 h-5 text-gray-400" />
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-blue-600">
                      {award.registration_number || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {award.full_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.center_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.tr_sno || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        award.transcript_collected
                          ? 'bg-green-100 text-green-700'
                          : 'bg-orange-100 text-orange-700'
                      }`}>
                        {award.transcript_collected ? 'Taken' : 'Not Taken'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.transcript_collector_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.transcript_collector_phone || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.transcript_collection_date || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <button
                        onClick={(e) => handleOpenCollectionModal(award, e)}
                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"
                        title="Update collection status"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, totalCount)} of {totalCount} results
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={`px-3 py-1 rounded-lg ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Collection Status Modal */}
      {showCollectionModal && selectedAward && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setShowCollectionModal(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Update Collection Status</h3>
              <button
                onClick={() => setShowCollectionModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">{selectedAward.full_name}</span> — {selectedAward.registration_number}
              </p>
              <p className="text-xs text-gray-500">TR SNo: {selectedAward.tr_sno}</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Collection Status</label>
                <select
                  value={collectionForm.collected ? 'taken' : 'not_taken'}
                  onChange={(e) => {
                    const isTaken = e.target.value === 'taken';
                    setCollectionForm({
                      ...collectionForm,
                      collected: isTaken,
                      collector_name: isTaken ? collectionForm.collector_name : '',
                      collector_phone: isTaken ? collectionForm.collector_phone : '',
                      collection_date: isTaken ? collectionForm.collection_date : '',
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="not_taken">Not Taken</option>
                  <option value="taken">Taken</option>
                </select>
              </div>

              {collectionForm.collected && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Collector Name *</label>
                    <input
                      type="text"
                      value={collectionForm.collector_name}
                      onChange={(e) => setCollectionForm({ ...collectionForm, collector_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Name of person collecting"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Collector Phone No</label>
                    <input
                      type="text"
                      value={collectionForm.collector_phone}
                      onChange={(e) => setCollectionForm({ ...collectionForm, collector_phone: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. 0700000000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Collection Date</label>
                    <input
                      type="date"
                      value={collectionForm.collection_date}
                      onChange={(e) => setCollectionForm({ ...collectionForm, collection_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCollectionModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCollection}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Transcript Collection Form Modal */}
      {showCollectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={handleCloseCollectModal}
          />
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white z-10 flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <ClipboardList className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Transcript Collection Form</h3>
              </div>
              {!collecting && (
                <button onClick={handleCloseCollectModal} className="p-1.5 hover:bg-gray-100 rounded-lg">
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              )}
            </div>

            {!receiptData ? (
              <>
                {/* Form Body */}
                <div className="px-6 py-5">
                  <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                    {/* Left Column */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Designation *</label>
                      <select
                        value={collectForm.designation}
                        onChange={(e) => {
                          const val = e.target.value;
                          const opt = DESIGNATION_OPTIONS.find((o) => o.value === val);
                          if (supportingDocRef.current) supportingDocRef.current.value = '';
                          setCollectErrors((prev) => ({ ...prev, designation: undefined, supporting_document: undefined }));

                          if (opt?.isConfig) {
                            // Look up center rep person matching this designation name
                            const rep = centerRepPersons.find((r) => r.designation_name === val);
                            if (rep) {
                              setCollectForm({
                                ...collectForm,
                                designation: val,
                                collector_name: rep.name || '',
                                collector_phone: rep.phone || '',
                                nin: rep.nin || '',
                                email: rep.email || '',
                                supporting_document: null,
                              });
                              setCollectFieldsLocked(true);
                            } else {
                              // Config designation but no rep person registered for this center
                              setCollectForm({
                                ...collectForm,
                                designation: val,
                                collector_name: '',
                                collector_phone: '',
                                nin: '',
                                email: '',
                                supporting_document: null,
                              });
                              setCollectFieldsLocked(false);
                              toast.info(`No ${val} registered for this center. Please fill in details manually.`);
                            }
                          } else {
                            // Candidate or Other Person — manual entry
                            setCollectForm({
                              ...collectForm,
                              designation: val,
                              collector_name: '',
                              collector_phone: '',
                              nin: '',
                              email: '',
                              supporting_document: null,
                            });
                            setCollectFieldsLocked(false);
                          }
                        }}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${collectErrors.designation ? 'border-red-400' : 'border-gray-300'}`}
                      >
                        <option value="">-- Select Designation --</option>
                        {DESIGNATION_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                      {collectErrors.designation && <p className="text-xs text-red-500 mt-1">{collectErrors.designation}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Collector Name *</label>
                      <input
                        type="text"
                        value={collectForm.collector_name}
                        onChange={(e) => { if (!collectFieldsLocked) { setCollectForm({ ...collectForm, collector_name: e.target.value }); setCollectErrors((prev) => ({ ...prev, collector_name: undefined })); } }}
                        readOnly={collectFieldsLocked}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${collectFieldsLocked ? 'bg-gray-50 text-gray-600' : ''} ${collectErrors.collector_name ? 'border-red-400' : 'border-gray-300'}`}
                        placeholder="Full name of collector"
                      />
                      {collectErrors.collector_name && <p className="text-xs text-red-500 mt-1">{collectErrors.collector_name}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
                      <input
                        type="text"
                        value={collectForm.collector_phone}
                        onChange={(e) => { if (!collectFieldsLocked) { setCollectForm({ ...collectForm, collector_phone: e.target.value }); setCollectErrors((prev) => ({ ...prev, collector_phone: undefined })); } }}
                        readOnly={collectFieldsLocked}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${collectFieldsLocked ? 'bg-gray-50 text-gray-600' : ''} ${collectErrors.collector_phone ? 'border-red-400' : 'border-gray-300'}`}
                        placeholder="e.g. +256700000000"
                      />
                      {collectErrors.collector_phone && <p className="text-xs text-red-500 mt-1">{collectErrors.collector_phone}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">NIN *</label>
                      <input
                        type="text"
                        value={collectForm.nin}
                        onChange={(e) => { if (!collectFieldsLocked) { setCollectForm({ ...collectForm, nin: e.target.value }); setCollectErrors((prev) => ({ ...prev, nin: undefined })); } }}
                        readOnly={collectFieldsLocked}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${collectFieldsLocked ? 'bg-gray-50 text-gray-600' : ''} ${collectErrors.nin ? 'border-red-400' : 'border-gray-300'}`}
                        placeholder="National ID Number"
                      />
                      {collectErrors.nin && <p className="text-xs text-red-500 mt-1">{collectErrors.nin}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                      <input
                        type="email"
                        value={collectForm.email}
                        onChange={(e) => { if (!collectFieldsLocked) { setCollectForm({ ...collectForm, email: e.target.value }); setCollectErrors((prev) => ({ ...prev, email: undefined })); } }}
                        readOnly={collectFieldsLocked}
                        className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 ${collectFieldsLocked ? 'bg-gray-50 text-gray-600' : ''} ${collectErrors.email ? 'border-red-400' : 'border-gray-300'}`}
                        placeholder="Receipt will be sent here"
                      />
                      {collectErrors.email && <p className="text-xs text-red-500 mt-1">{collectErrors.email}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Exam Center</label>
                      <input
                        type="text"
                        value={getSelectedCenter() || ''}
                        disabled
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-600"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Date of Collection</label>
                      <input
                        type="date"
                        value={collectForm.collection_date}
                        onChange={(e) => setCollectForm({ ...collectForm, collection_date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    {/* Supporting Document — only for Candidate and Other Person */}
                    {['candidate', 'other_person'].includes(collectForm.designation) && (
                      <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Supporting Document * <span className="text-xs text-gray-400 font-normal">(Required for {DESIGNATION_OPTIONS.find((o) => o.value === collectForm.designation)?.label})</span>
                        </label>
                        <div className={`flex items-center space-x-3 px-3 py-2 border rounded-lg ${collectErrors.supporting_document ? 'border-red-400 bg-red-50' : 'border-gray-300'}`}>
                          <Paperclip className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          <input
                            ref={supportingDocRef}
                            type="file"
                            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                            onChange={(e) => {
                              setCollectForm({ ...collectForm, supporting_document: e.target.files[0] || null });
                              setCollectErrors((prev) => ({ ...prev, supporting_document: undefined }));
                            }}
                            className="flex-1 text-sm text-gray-600 file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
                          />
                        </div>
                        {collectErrors.supporting_document && <p className="text-xs text-red-500 mt-1">{collectErrors.supporting_document}</p>}
                      </div>
                    )}

                    {/* Signature pad */}
                    <div>
                      <SignaturePad
                        label="Signature"
                        height={130}
                        value={collectForm.signature_data}
                        onChange={(data) => setCollectForm({ ...collectForm, signature_data: data })}
                        showHardwareToggle={true}
                      />
                    </div>

                    {/* Candidates info */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Candidates ({selectedCandidates.length})
                      </label>
                      <div className="border border-gray-200 rounded-lg p-2 max-h-32 overflow-y-auto bg-gray-50">
                        <div className="flex flex-wrap gap-1.5">
                          {getSelectedAwards().map((a) => (
                            <span
                              key={a.id}
                              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-700 border border-purple-200"
                              title={a.full_name}
                            >
                              {a.registration_number} - {a.full_name.length > 15 ? a.full_name.slice(0, 15) + '...' : a.full_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Modal Footer - Form */}
                <div className="sticky bottom-0 bg-gray-50 flex items-center justify-between px-6 py-4 border-t border-gray-200">
                  <button
                    onClick={handleCloseCollectModal}
                    disabled={collecting}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    CANCEL
                  </button>
                  <button
                    onClick={handleCollectTranscripts}
                    disabled={collecting}
                    className="flex items-center px-5 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors font-medium"
                  >
                    {collecting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Printer className="w-4 h-4 mr-2" />
                        SAVE AND PRINT
                      </>
                    )}
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Receipt View */}
                <div className="px-6 py-5">
                  <div className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg mb-5">
                    <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-green-700">Collection recorded successfully!</p>
                      <p className="text-xs text-green-600">Receipt No: {receiptData.receipt_number}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                    <div><span className="text-gray-500">Designation:</span> <span className="font-medium">{receiptData.designation}</span></div>
                    <div><span className="text-gray-500">Collector:</span> <span className="font-medium">{receiptData.collector_name}</span></div>
                    <div><span className="text-gray-500">NIN:</span> <span className="font-medium">{receiptData.nin}</span></div>
                    <div><span className="text-gray-500">Phone:</span> <span className="font-medium">{receiptData.collector_phone}</span></div>
                    <div><span className="text-gray-500">Center:</span> <span className="font-medium">{receiptData.center_name}</span></div>
                    <div><span className="text-gray-500">Email:</span> <span className="font-medium">{receiptData.email}</span></div>
                    <div><span className="text-gray-500">Date:</span> <span className="font-medium">{receiptData.collection_date}</span></div>
                    <div><span className="text-gray-500">Candidates:</span> <span className="font-medium">{receiptData.candidate_count}</span></div>
                  </div>

                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Collected Transcripts</p>
                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                      <table className="min-w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">#</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Reg No</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Name</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">TR SNo</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {receiptData.candidates.map((c, i) => (
                            <tr key={i}>
                              <td className="px-3 py-2 text-gray-500">{i + 1}</td>
                              <td className="px-3 py-2 text-blue-600 font-medium">{c.registration_number}</td>
                              <td className="px-3 py-2">{c.full_name}</td>
                              <td className="px-3 py-2 text-gray-500">{c.tr_sno}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Modal Footer - Receipt */}
                <div className="sticky bottom-0 bg-gray-50 flex items-center justify-end space-x-3 px-6 py-4 border-t border-gray-200">
                  <button
                    onClick={handleCloseCollectModal}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100"
                  >
                    Close
                  </button>
                  <button
                    onClick={handlePrintReceipt}
                    className="flex items-center px-5 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium"
                  >
                    <Printer className="w-4 h-4 mr-2" />
                    Print Receipt
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Bulk Upload Serial Numbers Modal */}
      {showBulkUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={!uploading ? handleCloseBulkUpload : undefined}
          />
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FileSpreadsheet className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Bulk Upload Serial Numbers</h3>
                  <p className="text-xs text-gray-500">Excel file with columns: Registration Number, TR SNo</p>
                </div>
              </div>
              {!uploading && (
                <button
                  onClick={handleCloseBulkUpload}
                  className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              )}
            </div>

            {/* Modal Body */}
            <div className="px-6 py-5">
              {/* File Drop Zone */}
              {!uploadResults && (
                <div
                  onDrop={handleFileDrop}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onClick={() => !uploading && fileInputRef.current?.click()}
                  className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                    dragOver
                      ? 'border-blue-400 bg-blue-50'
                      : uploadFile
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={uploading}
                  />
                  {uploadFile ? (
                    <div className="flex flex-col items-center">
                      <div className="p-3 bg-green-100 rounded-full mb-3">
                        <FileSpreadsheet className="w-8 h-8 text-green-600" />
                      </div>
                      <p className="text-sm font-medium text-gray-900">{uploadFile.name}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {(uploadFile.size / 1024).toFixed(1)} KB
                      </p>
                      {!uploading && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setUploadFile(null);
                            setUploadResults(null);
                          }}
                          className="mt-2 text-xs text-red-500 hover:text-red-700 underline"
                        >
                          Remove file
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <div className="p-3 bg-gray-100 rounded-full mb-3">
                        <Upload className="w-8 h-8 text-gray-400" />
                      </div>
                      <p className="text-sm font-medium text-gray-700">Drop your Excel file here</p>
                      <p className="text-xs text-gray-400 mt-1">or click to browse</p>
                      <p className="text-xs text-gray-400 mt-2">Supported: .xlsx, .xls</p>
                    </div>
                  )}
                </div>
              )}

              {/* Progress Bar */}
              {uploading && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Processing...</span>
                    <span className="text-sm font-medium text-blue-600">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Please wait while the file is being processed...</p>
                </div>
              )}

              {/* Upload Results */}
              {uploadResults && !uploadResults.error && (
                <div className="space-y-4">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-gray-900">{uploadResults.total_rows}</p>
                      <p className="text-xs text-gray-500">Total Rows</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-green-600">{uploadResults.success_count}</p>
                      <p className="text-xs text-green-600">Successful</p>
                    </div>
                    <div className={`rounded-lg p-3 text-center ${uploadResults.error_count > 0 ? 'bg-red-50' : 'bg-gray-50'}`}>
                      <p className={`text-2xl font-bold ${uploadResults.error_count > 0 ? 'text-red-600' : 'text-gray-400'}`}>{uploadResults.error_count}</p>
                      <p className={`text-xs ${uploadResults.error_count > 0 ? 'text-red-600' : 'text-gray-400'}`}>Errors</p>
                    </div>
                  </div>

                  {/* Success message */}
                  {uploadResults.success_count > 0 && uploadResults.error_count === 0 && (
                    <div className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                      <p className="text-sm text-green-700">
                        All {uploadResults.success_count} serial number(s) uploaded successfully!
                      </p>
                    </div>
                  )}

                  {/* Detailed Results */}
                  {uploadResults.results && uploadResults.results.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-2">Details</p>
                      <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-lg divide-y divide-gray-100">
                        {uploadResults.results.map((r, i) => (
                          <div
                            key={i}
                            className={`flex items-start space-x-3 px-3 py-2.5 text-sm ${
                              r.status === 'success' ? 'bg-white' : 'bg-red-50'
                            }`}
                          >
                            {r.status === 'success' ? (
                              <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                            ) : (
                              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                            )}
                            <div className="flex-1 min-w-0">
                              <p className={`font-medium ${
                                r.status === 'success' ? 'text-gray-900' : 'text-red-800'
                              }`}>
                                Row {r.row}: {r.registration_number}
                                {r.candidate_name && <span className="font-normal text-gray-500"> — {r.candidate_name}</span>}
                              </p>
                              <p className={`text-xs mt-0.5 ${
                                r.status === 'success' ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {r.message}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Error message (file-level) */}
              {uploadResults?.error && (
                <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg mt-4">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                  <p className="text-sm text-red-700">{uploadResults.error}</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
              {!uploadResults ? (
                <>
                  <button
                    onClick={handleCloseBulkUpload}
                    disabled={uploading}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleBulkUpload}
                    disabled={!uploadFile || uploading}
                    className="flex items-center px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {uploading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4 mr-2" />
                        Upload
                      </>
                    )}
                  </button>
                </>
              ) : (
                <>
                  {uploadResults.error_count > 0 && (
                    <button
                      onClick={() => {
                        setUploadFile(null);
                        setUploadResults(null);
                        setUploadProgress(0);
                      }}
                      className="px-4 py-2 text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
                    >
                      Upload Another File
                    </button>
                  )}
                  <button
                    onClick={handleCloseBulkUpload}
                    className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Done
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TranscriptLogs;
