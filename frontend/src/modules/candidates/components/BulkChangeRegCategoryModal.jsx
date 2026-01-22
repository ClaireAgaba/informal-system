import { useState } from 'react';
import { X, Tag, AlertTriangle } from 'lucide-react';
import Button from '@shared/components/Button';

const BulkChangeRegCategoryModal = ({ selectedCount, onClose, onConfirm, isLoading }) => {
  const [selectedCategory, setSelectedCategory] = useState('');

  const categories = [
    { value: 'modular', label: 'Modular' },
    { value: 'formal', label: 'Formal' },
    { value: 'workers_pas', label: "Worker's PAS" },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedCategory) {
      onConfirm(selectedCategory);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Bulk Change Registration Category
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                <strong>{selectedCount}</strong> candidate(s) selected
              </p>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">Important:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Registration numbers will be regenerated</li>
                  <li>Only candidates without enrollments/results will be changed</li>
                  <li>Candidate's occupation must support the target category</li>
                </ul>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Tag className="w-4 h-4 inline mr-1" />
                Select New Registration Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="">-- Select Category --</option>
                {categories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Candidates whose occupation doesn't support this category will be skipped
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t bg-gray-50 rounded-b-lg">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={isLoading}
              disabled={isLoading || !selectedCategory}
            >
              Change Category
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BulkChangeRegCategoryModal;
