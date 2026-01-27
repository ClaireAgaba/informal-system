import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Globe } from 'lucide-react';
import statisticsApi from '../services/statisticsApi';
import axios from 'axios';

const SpecialNeedsAnalytics = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [exportingExcel, setExportingExcel] = useState(false);
    const [seriesList, setSeriesList] = useState([]);
    const [selectedSeries, setSelectedSeries] = useState('all');
    const [analytics, setAnalytics] = useState(null);

    useEffect(() => {
        fetchSeriesList();
    }, []);

    const fetchSeriesList = async () => {
        try {
            const response = await statisticsApi.getAssessmentSeriesList();
            setSeriesList(response.data);
        } catch (error) {
            console.error('Error fetching series list:', error);
        }
    };

    const handleGenerateReport = async () => {
        try {
            setLoading(true);
            const params = {};
            if (selectedSeries !== 'all') {
                params.series_id = selectedSeries;
            }
            const response = await statisticsApi.getSpecialNeedsAnalytics(params);
            setAnalytics(response.data);
        } catch (error) {
            console.error('Error fetching analytics:', error);
            alert('Failed to fetch analytics. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleExportExcel = async () => {
        try {
            setExportingExcel(true);

            // Build query params
            const params = {};
            if (selectedSeries !== 'all') {
                params.series_id = selectedSeries;
            }

            const response = await axios.get('/api/statistics/special-needs/export-excel/', {
                params,
                responseType: 'blob', // Important for Excel file download
            });

            const contentDisposition = response.headers['content-disposition'];
            let filename = 'special_needs_analytics.xlsx';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/["']/g, '');
                }
            }

            const blob = response.data;
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            alert('Failed to export to Excel. Please try again.');
        } finally {
            setExportingExcel(false);
        }
    };

    const getPercentage = (value, total) => {
        if (total === 0) return '0.0';
        return ((value / total) * 100).toFixed(1);
    };

    if (loading && !analytics) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Special Needs & Refugee Analytics</h1>
                <p className="text-gray-600 mt-1">Comprehensive analysis with gender-based performance metrics</p>
            </div>

            <div className="bg-white p-4 rounded-lg shadow border border-gray-200 mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Assessment Series</label>
                <select
                    value={selectedSeries}
                    onChange={(e) => setSelectedSeries(e.target.value)}
                    className="w-full md:w-96 border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 mb-4"
                >
                    <option value="all">All Series</option>
                    {seriesList.map((series) => (
                        <option key={series.id} value={series.id}>
                            {series.name} ({series.year})
                        </option>
                    ))}
                </select>

                <div className="flex gap-3">
                    <button
                        onClick={handleGenerateReport}
                        disabled={loading}
                        className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                        {loading ? 'Generating...' : 'Generate Report'}
                    </button>

                    <button
                        onClick={handleExportExcel}
                        disabled={exportingExcel}
                        className="px-6 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                        {exportingExcel ? 'Exporting...' : 'Export to Excel'}
                    </button>
                </div>
            </div>

            {analytics && (
                <>
                    {/* Special Needs Section */}
                    <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
                        <div className="flex items-center mb-4">
                            <Heart className="w-6 h-6 text-red-600 mr-2" />
                            <h2 className="text-xl font-semibold text-gray-900">Special Needs Candidates</h2>
                        </div>
                        <div className="grid grid-cols-4 gap-4 mb-4">
                            <div className="text-center p-3 bg-gray-50 rounded">
                                <p className="text-sm text-gray-600">Total</p>
                                <p className="text-2xl font-bold">{analytics.special_needs.overview.total}</p>
                            </div>
                            <div className="text-center p-3 bg-blue-50 rounded">
                                <p className="text-sm text-gray-600">Male</p>
                                <p className="text-2xl font-bold text-blue-600">{analytics.special_needs.overview.male}</p>
                            </div>
                            <div className="text-center p-3 bg-pink-50 rounded">
                                <p className="text-sm text-gray-600">Female</p>
                                <p className="text-2xl font-bold text-pink-600">{analytics.special_needs.overview.female}</p>
                            </div>
                            <div className="text-center p-3 bg-green-50 rounded">
                                <p className="text-sm text-gray-600">Pass Rate</p>
                                <p className="text-2xl font-bold text-green-600">{analytics.special_needs.overview.pass_rate}%</p>
                            </div>
                        </div>

                        {/* Disability Types */}
                        {analytics.special_needs.by_disability_type && analytics.special_needs.by_disability_type.length > 0 && (
                            <div className="mt-4">
                                <h3 className="font-semibold mb-2">By Disability Type</h3>
                                {analytics.special_needs.by_disability_type.map((d, i) => (
                                    <div key={i} className="mb-2">
                                        <div className="flex justify-between text-sm mb-1">
                                            <span>{d.name}</span>
                                            <span>{d.total} (M:{d.male} F:{d.female}) - {d.pass_rate}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded h-2">
                                            <div className="bg-red-500 h-2 rounded" style={{ width: `${d.pass_rate}%` }}></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Special Needs by Sector */}
                        {analytics.special_needs.by_sector && analytics.special_needs.by_sector.length > 0 && (
                            <div className="mt-4">
                                <h3 className="font-semibold mb-2">By Sector</h3>
                                <table className="min-w-full text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left">Sector</th>
                                            <th className="px-4 py-2 text-center">Total</th>
                                            <th className="px-4 py-2 text-center">Male</th>
                                            <th className="px-4 py-2 text-center">Female</th>
                                            <th className="px-4 py-2 text-center">M Passed</th>
                                            <th className="px-4 py-2 text-center">F Passed</th>
                                            <th className="px-4 py-2 text-center">Total Passed</th>
                                            <th className="px-4 py-2 text-center">M Pass %</th>
                                            <th className="px-4 py-2 text-center">F Pass %</th>
                                            <th className="px-4 py-2 text-center">Overall %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {analytics.special_needs.by_sector.map((s, i) => (
                                            <tr key={i} className="border-t hover:bg-gray-50">
                                                <td className="px-4 py-2">{s.sector_name}</td>
                                                <td className="px-4 py-2 text-center">{s.total}</td>
                                                <td className="px-4 py-2 text-center text-blue-600">{s.male}</td>
                                                <td className="px-4 py-2 text-center text-pink-600">{s.female}</td>
                                                <td className="px-4 py-2 text-center text-blue-700 font-medium">{s.male_passed}</td>
                                                <td className="px-4 py-2 text-center text-pink-700 font-medium">{s.female_passed}</td>
                                                <td className="px-4 py-2 text-center font-semibold">{s.total_passed}</td>
                                                <td className="px-4 py-2 text-center text-blue-600">{s.male_pass_rate}%</td>
                                                <td className="px-4 py-2 text-center text-pink-600">{s.female_pass_rate}%</td>
                                                <td className="px-4 py-2 text-center font-bold text-green-600">{s.pass_rate}%</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>

                    {/* Refugee Section */}
                    <div className="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-lg shadow border border-green-200">
                        <div className="flex items-center mb-4">
                            <Globe className="w-6 h-6 text-green-600 mr-2" />
                            <h2 className="text-xl font-semibold text-gray-900">Refugee Candidates</h2>
                        </div>
                        <div className="grid grid-cols-4 gap-4 mb-4">
                            <div className="text-center p-3 bg-white rounded">
                                <p className="text-sm text-gray-600">Total</p>
                                <p className="text-2xl font-bold">{analytics.refugee.overview.total}</p>
                            </div>
                            <div className="text-center p-3 bg-white rounded">
                                <p className="text-sm text-gray-600">Male</p>
                                <p className="text-2xl font-bold text-blue-600">{analytics.refugee.overview.male}</p>
                            </div>
                            <div className="text-center p-3 bg-white rounded">
                                <p className="text-sm text-gray-600">Female</p>
                                <p className="text-2xl font-bold text-pink-600">{analytics.refugee.overview.female}</p>
                            </div>
                            <div className="text-center p-3 bg-white rounded">
                                <p className="text-sm text-gray-600">Pass Rate</p>
                                <p className="text-2xl font-bold text-green-600">{analytics.refugee.overview.pass_rate}%</p>
                            </div>
                        </div>

                        {/* Refugee by Sector */}
                        {analytics.refugee.by_sector && analytics.refugee.by_sector.length > 0 && (
                            <div className="mt-4 bg-white p-4 rounded">
                                <h3 className="font-semibold mb-2">By Sector</h3>
                                <table className="min-w-full text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left">Sector</th>
                                            <th className="px-4 py-2 text-center">Total</th>
                                            <th className="px-4 py-2 text-center">Male</th>
                                            <th className="px-4 py-2 text-center">Female</th>
                                            <th className="px-4 py-2 text-center">M Passed</th>
                                            <th className="px-4 py-2 text-center">F Passed</th>
                                            <th className="px-4 py-2 text-center">Total Passed</th>
                                            <th className="px-4 py-2 text-center">M Pass %</th>
                                            <th className="px-4 py-2 text-center">F Pass %</th>
                                            <th className="px-4 py-2 text-center">Overall %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {analytics.refugee.by_sector.map((s, i) => (
                                            <tr key={i} className="border-t hover:bg-gray-50">
                                                <td className="px-4 py-2">{s.sector_name}</td>
                                                <td className="px-4 py-2 text-center">{s.total}</td>
                                                <td className="px-4 py-2 text-center text-blue-600">{s.male}</td>
                                                <td className="px-4 py-2 text-center text-pink-600">{s.female}</td>
                                                <td className="px-4 py-2 text-center text-blue-700 font-medium">{s.male_passed}</td>
                                                <td className="px-4 py-2 text-center text-pink-700 font-medium">{s.female_passed}</td>
                                                <td className="px-4 py-2 text-center font-semibold">{s.total_passed}</td>
                                                <td className="px-4 py-2 text-center text-blue-600">{s.male_pass_rate}%</td>
                                                <td className="px-4 py-2 text-center text-pink-600">{s.female_pass_rate}%</td>
                                                <td className="px-4 py-2 text-center font-bold text-green-600">{s.pass_rate}%</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default SpecialNeedsAnalytics;
