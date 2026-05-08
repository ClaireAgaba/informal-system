import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Loader2, ShieldCheck, AlertTriangle, User } from 'lucide-react';
import apiClient from '../../../services/apiClient';

const WorkersPasVerify = () => {
  const { bookSlug } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get(`/workers-pas/verify/${bookSlug}/`);
        setData(res.data);
      } catch (err) {
        if (err.response?.status === 404) {
          setError('No booklet found for this code. The book number may be incorrect.');
        } else {
          setError('Unable to verify this booklet. Please try again later.');
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [bookSlug]);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-green-100 rounded-full mb-3">
            <ShieldCheck className="w-7 h-7 text-green-600" />
          </div>
          <h1 className="text-xl font-bold text-gray-900">UVTAB Worker's PAS</h1>
          <p className="text-sm text-gray-500">Official verification record</p>
        </div>

        {loading && (
          <div className="bg-white rounded-xl shadow p-8 text-center text-gray-500">
            <Loader2 className="w-6 h-6 animate-spin inline mr-2" />
            Verifying booklet…
          </div>
        )}

        {error && (
          <div className="bg-white rounded-xl shadow p-8 text-center">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-3" />
            <p className="text-gray-700 font-medium mb-1">Verification failed</p>
            <p className="text-sm text-gray-500">{error}</p>
          </div>
        )}

        {data && (
          <div className="bg-white rounded-xl shadow overflow-hidden">
            {/* Photo + primary identity */}
            <div className="flex gap-4 p-5 border-b border-gray-100">
              <div className="flex-shrink-0">
                {data.photo_url ? (
                  <img
                    src={data.photo_url}
                    alt={data.full_name}
                    className="w-20 h-24 object-cover rounded-lg border border-gray-200"
                  />
                ) : (
                  <div className="w-20 h-24 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center">
                    <User className="w-8 h-8 text-gray-400" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-gray-900 text-base leading-tight mb-1">
                  {data.full_name}
                </p>
                <p className="text-xs font-mono text-gray-500 mb-2">
                  {data.registration_number}
                </p>
                <p className="text-sm text-gray-700 leading-snug">
                  {data.occupation_name}
                </p>
                {data.levels && data.levels.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {data.levels.map((lvl) => (
                      <span
                        key={lvl}
                        className="inline-block px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs rounded font-medium"
                      >
                        {lvl}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Book details */}
            <div className="px-5 py-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Book number</span>
                <span className="font-mono font-medium text-gray-800">{data.book_number}</span>
              </div>
              {data.issued_date && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Issued</span>
                  <span className="text-gray-800">
                    {new Date(data.issued_date).toLocaleDateString('en-GB', {
                      day: '2-digit', month: 'long', year: 'numeric',
                    })}
                  </span>
                </div>
              )}
            </div>

            {/* Verified badge */}
            <div className="bg-green-50 border-t border-green-100 px-5 py-3 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-green-600 flex-shrink-0" />
              <span className="text-sm font-medium text-green-700">
                Verified by Uganda Vocational Training and Apprenticeship Board (UVTAB)
              </span>
            </div>
          </div>
        )}


      </div>
    </div>
  );
};

export default WorkersPasVerify;
