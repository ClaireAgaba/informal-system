import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Receipt, Printer, Download, Phone, Mail, FileText } from 'lucide-react';
import QRCode from 'qrcode';
import apiClient from '../../../services/apiClient';

const CollectionReceiptDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [receipt, setReceipt] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const res = await apiClient.get(`/awards/collection-receipts/${id}/`);
        setReceipt(res.data);
      } catch (err) {
        console.error('Error fetching receipt detail:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
      ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  };

  const handlePrint = async () => {
    if (!receipt) return;

    // Get logged-in user
    let clearedByName = '';
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{}');
      clearedByName = (u.first_name && u.last_name) ? `${u.first_name} ${u.last_name}` : u.first_name || u.username || '';
    } catch (_) {}

    // Generate QR code with collection details
    const qrText = [
      `Collection Reference: ${receipt.receipt_number}`,
      `Collector Name: ${receipt.collector_name}`,
      `Center: ${receipt.center_name}`,
      `Collection Date & Time: ${receipt.created_at || ''}`,
      `Collector Type: ${receipt.designation}`,
    ].join('\n');
    let qrDataUrl = '';
    try { qrDataUrl = await QRCode.toDataURL(qrText, { width: 120, margin: 1 }); } catch (_) {}

    const logoUrl = window.location.origin + '/uvtab-logo.png';

    const candidateRows = (receipt.candidates || []).map((c) => `
      <tr>
        <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;">${c.registration_number || ''}</td>
        <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;">${c.full_name || ''}</td>
        <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;">${c.center_name || ''}</td>
        <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;">${c.transcript_serial_number || ''}</td>
        <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;">${c.transcript_type || 'Transcript'}</td>
      </tr>
    `).join('');

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const html = `<!DOCTYPE html>
<html><head><title>Collection Receipt - ${receipt.receipt_number}</title>
<style>
  body { font-family: 'Times New Roman', Times, serif; margin: 30px; color: #333; }
  .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #1a237e; padding-bottom: 15px; }
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
  th { background: #f3f4f6; padding: 8px 10px; text-align: left; font-size: 11px; text-transform: uppercase; color: #555; border-bottom: 2px solid #ddd; }
  .sig-section { margin-top: 30px; display: flex; justify-content: space-between; }
  .sig-box { width: 45%; text-align: center; }
  .sig-line { border-top: 1px solid #333; padding-top: 5px; font-size: 12px; color: #666; margin-top: 40px; }
  .official-section { margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px; }
  .official-title { font-weight: bold; font-size: 14px; font-style: italic; }
  .cleared-by { font-size: 13px; color: #333; margin-top: 4px; }
  .cleared-by em { font-style: italic; font-weight: bold; }
  .qr-section { text-align: center; margin-top: 15px; }
  @media print { body { margin: 15px; } }
</style>
</head><body>
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
  <div class="info-item"><span class="info-label">Reference:</span><span class="info-value">${receipt.receipt_number}</span></div>
  <div class="info-item"><span class="info-label">Created On:</span><span class="info-value">${formatDateTime(receipt.created_at)}</span></div>
  <div class="info-item"><span class="info-label">Collector Name:</span><span class="info-value">${receipt.collector_name}</span></div>
  <div class="info-item"><span class="info-label">Center:</span><span class="info-value">${receipt.center_name}</span></div>
  <div class="info-item"><span class="info-label">NIN:</span><span class="info-value">${receipt.nin}</span></div>
  <div class="info-item"><span class="info-label">Candidates:</span><span class="info-value">${receipt.candidate_count}</span></div>
  <div class="info-item"><span class="info-label">Designation:</span><span class="info-value">${receipt.designation}</span></div>
  <div class="info-item"><span class="info-label">Phone:</span><span class="info-value">${receipt.collector_phone}</span></div>
  <div class="info-item"><span class="info-label">Email:</span><span class="info-value">${receipt.email}</span></div>
  <div class="info-item"><span class="info-label">Collection Date:</span><span class="info-value">${formatDate(receipt.collection_date)}</span></div>
</div>
<h3 style="font-size:14px;margin-bottom:5px;">Candidates</h3>
<table>
  <thead><tr>
    <th>Registration Number</th><th>Name</th><th>Center</th><th>Transcript Number</th><th>Transcript Type</th>
  </tr></thead>
  <tbody>${candidateRows}</tbody>
</table>
<div class="sig-section">
  <div class="sig-box">
    ${receipt.signature_data
      ? `<img src="${receipt.signature_data}" style="max-width:200px;max-height:60px;display:block;margin:0 auto 5px;" /><div style="border-top:1px solid #333;padding-top:5px;font-size:12px;color:#666;">Collector Signature</div>`
      : `<div class="sig-line">Collector Signature</div>`
    }
  </div>
  <div class="sig-box"><div class="sig-line">Authorized Officer</div></div>
</div>
<div class="official-section">
  <div class="official-title">Official</div>
  <div class="cleared-by">Issued By: <em>${clearedByName}</em></div>
</div>
${qrDataUrl ? `<div class="qr-section"><img src="${qrDataUrl}" alt="QR Code" style="width:120px;height:120px;" /></div>` : ''}
</body></html>`;

    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => printWindow.print(), 500);
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!receipt) {
    return (
      <div className="p-6">
        <div className="text-center py-12 text-gray-500">Receipt not found</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/awards/collection-receipts')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <Receipt className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              Collection Receipt / <span className="text-purple-600">{receipt.receipt_number}</span>
            </h1>
          </div>
        </div>
        <button
          onClick={handlePrint}
          className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
        >
          <Printer className="w-4 h-4 mr-2" />
          Print
        </button>
      </div>

      {/* Info Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-8">
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Reference</p>
            <p className="text-sm font-medium text-gray-900">{receipt.receipt_number}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Created On</p>
            <p className="text-sm text-gray-700">{formatDateTime(receipt.created_at)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Collection Date</p>
            <p className="text-sm text-gray-700">{formatDate(receipt.collection_date)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Collector Name</p>
            <p className="text-sm font-medium text-gray-900">{receipt.collector_name}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Center</p>
            <p className="text-sm text-gray-700">{receipt.center_name}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Candidates</p>
            <p className="text-sm font-semibold text-purple-700">{receipt.candidate_count}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">NIN</p>
            <p className="text-sm text-gray-700 font-mono">{receipt.nin}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Designation</p>
            <p className="text-sm text-gray-700">{receipt.designation}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Phone</p>
            <p className="text-sm text-gray-700 flex items-center">
              <Phone className="w-3.5 h-3.5 mr-1 text-gray-400" />
              {receipt.collector_phone}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold mb-0.5">Email</p>
            <p className="text-sm text-gray-700 flex items-center">
              <Mail className="w-3.5 h-3.5 mr-1 text-gray-400" />
              {receipt.email}
            </p>
          </div>
        </div>
      </div>

      {/* Candidates Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center">
            <FileText className="w-4 h-4 mr-2 text-purple-500" />
            Candidates
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Registration Number</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Name</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Center</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Transcript Number</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Transcript Type</th>
              </tr>
            </thead>
            <tbody>
              {(receipt.candidates || []).map((c) => (
                <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-purple-700 font-medium">{c.registration_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-800">{c.full_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{c.center_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{c.transcript_serial_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{c.transcript_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default CollectionReceiptDetail;
