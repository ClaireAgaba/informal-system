import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/apiClient';
import { X, Search } from 'lucide-react';

const CenterMultiSelect = ({ selectedCenters, onChange }) => {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const wrapperRef = useRef(null);

    useEffect(() => {
        // Close suggestions when clicking outside
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [wrapperRef]);

    useEffect(() => {
        const fetchCenters = async () => {
            if (query.length < 2) {
                setSuggestions([]);
                return;
            }
            setLoading(true);
            try {
                // Determine if we need to query paginated or full
                const response = await apiClient.get('/assessment-centers/centers/', {
                    params: { search: query }
                });

                // Handle pagination if present (DRF default might be paginated)
                const results = Array.isArray(response.data) ? response.data : (response.data.results || []);
                setSuggestions(results);
                setShowSuggestions(true);
            } catch (error) {
                console.error("Error searching centers:", error);
            } finally {
                setLoading(false);
            }
        };

        const timeoutId = setTimeout(fetchCenters, 300);
        return () => clearTimeout(timeoutId);
    }, [query]);

    const handleSelect = (center) => {
        if (!selectedCenters.find(c => c.id === center.id)) {
            onChange([...selectedCenters, center]);
        }
        setQuery('');
        setSuggestions([]);
        setShowSuggestions(false);
    };

    const handleRemove = (centerId) => {
        onChange(selectedCenters.filter(c => c.id !== centerId));
    };

    return (
        <div className="relative" ref={wrapperRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Center(s)</label>
            <div className="flex flex-wrap gap-2 mb-2 p-1 border border-gray-300 rounded-md bg-white min-h-[42px] focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
                {selectedCenters.map(center => (
                    <span key={center.id} className="inline-flex items-center px-2 py-1 rounded bg-blue-100 text-blue-800 text-xs font-medium">
                        {center.center_number} - {center.center_name}
                        <button onClick={() => handleRemove(center.id)} className="ml-1 text-blue-600 hover:text-blue-800 focus:outline-none">
                            <X size={14} />
                        </button>
                    </span>
                ))}
                <input
                    type="text"
                    className="flex-grow outline-none text-sm min-w-[150px] p-1 bg-transparent"
                    placeholder={selectedCenters.length === 0 ? "Type center name or number..." : "Add another..."}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => query.length >= 2 && setShowSuggestions(true)}
                />
            </div>

            {loading && query.length >= 2 && (
                <div className="absolute right-3 top-9">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
                </div>
            )}

            {showSuggestions && suggestions.length > 0 && (
                <div className="absolute z-50 w-full bg-white shadow-lg rounded-md border border-gray-200 mt-1 max-h-60 overflow-auto">
                    {suggestions.map(center => (
                        <div
                            key={center.id}
                            className="p-2 hover:bg-gray-100 cursor-pointer text-sm border-b border-gray-50 last:border-b-0"
                            onClick={() => handleSelect(center)}
                        >
                            <span className="font-semibold text-gray-900">{center.center_number}</span> <span className="text-gray-600">- {center.center_name}</span>
                        </div>
                    ))}
                </div>
            )}
            {showSuggestions && query.length >= 2 && suggestions.length === 0 && !loading && (
                <div className="absolute z-50 w-full bg-white shadow-lg rounded-md border border-gray-200 mt-1 p-2 text-sm text-gray-500 text-center">
                    No centers found
                </div>
            )}
        </div>
    );
};

export default CenterMultiSelect;
