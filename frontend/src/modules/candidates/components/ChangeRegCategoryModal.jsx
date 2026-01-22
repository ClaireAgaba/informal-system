import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { X, Tag, AlertTriangle } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import Button from '@shared/components/Button';

const ChangeRegCategoryModal = ({ candidate, onClose }) => {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState('');

  const currentCategory = candidate.registration_category;
  const occupation = candidate.occupation_detail || candidate.occupation;

  // Determine which categories are available based on occupation
  const availableCategories = useMemo(() => {
    if (!occupation) return [];
    
    const categories = [];
    
    if (occupation.occ_category === 'formal') {
      // Formal occupations support formal and potentially modular
      if (currentCategory !== 'formal') {
        categories.push({ value: 'formal', label: 'Formal' });
      }
      if (occupation.has_modular && currentCategory !== 'modular') {
        categories.push({ value: 'modular', label: 'Modular' });
      }
    } else if (occupation.occ_category === 'workers_pas') {
      // Workers PAS occupations only support workers_pas
      if (currentCategory !== 'workers_pas') {
        categories.push({ value: 'workers_pas', label: "Worker's PAS" });
      }
    }
    
    return categories;
  }, [occupation, currentCategory]);

  // Change registration category mutation
  const changeRegCategoryMutation = useMutation({
    mutationFn: (newRegCategory) => candidateApi.changeRegistrationCategory(candidate.id, newRegCategory),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', candidate.id]);
      
      const { old_registration_number, new_registration_number } = response.data;
      
      let message = response.data.message;
      if (old_registration_number !== new_registration_number) {
        message += `\nReg No: ${old_registration_number} → ${new_registration_number}`;
      }
      
      toast.success(message, { duration: 5000 });
      onClose();
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to change registration category');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedCategory) {
      toast.error('Please select a registration category');
      return;
    }
    changeRegCategoryMutation.mutate(selectedCategory);
  };

  const getCategoryDisplay = (cat) => {
    const display = {
      'modular': 'Modular',
      'formal': 'Formal',
      'workers_pas': "Worker's PAS"
    };
    return display[cat] || cat;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Change Registration Category
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
                <strong>Candidate:</strong> {candidate.full_name}
              </p>
              <p className="text-sm text-blue-600 mt-1">
                <strong>Current Category:</strong> {getCategoryDisplay(currentCategory)}
              </p>
              {occupation && (
                <p className="text-sm text-blue-600 mt-1">
                  <strong>Occupation:</strong> {occupation.occ_name} ({occupation.occ_category === 'workers_pas' ? "Worker's PAS" : 'Formal'}{occupation.has_modular ? ', Modular enabled' : ''})
                </p>
              )}
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">Important:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Registration number will be regenerated</li>
                  <li>Only categories supported by current occupation are shown</li>
                </ul>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Tag className="w-4 h-4 inline mr-1" />
                Select New Registration Category
              </label>
              {availableCategories.length === 0 ? (
                <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
                  No other registration categories are available for the current occupation ({occupation?.occ_name || 'N/A'}).
                </div>
              ) : (
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">-- Select Category --</option>
                  {availableCategories.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              )}
              {availableCategories.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  {availableCategories.length} category option(s) available
                </p>
              )}
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
              loading={changeRegCategoryMutation.isPending}
              disabled={changeRegCategoryMutation.isPending || !selectedCategory || availableCategories.length === 0}
            >
              Change Category
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangeRegCategoryModal;
