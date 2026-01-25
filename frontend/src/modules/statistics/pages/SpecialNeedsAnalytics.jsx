import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Heart, Globe, TrendingUp, Filter, ArrowLeft } from 'lucide-react';
import statisticsApi from '../services/statisticsApi';

const SpecialNeedsAnalytics = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [seriesList, setSeriesList] = useState([]);
    const [selectedSeries, setSelectedSeries] = useState('all');
    const [analytics, setAnalytics] = useState(null);

    useEffect(() => {
        fetchSeriesList();
    }, []);

    useEffect(() => {
        fetchAnalytics();
    }, [selectedSeries]);

    const fetchSeriesList = async () => {
        try {
            const response = await statisticsApi.getAssessmentSeriesList();
            setSeriesList(response.data);
        } catch (error) {
            console.error('Error fetching series list:', error);
        }
    };

    const fetchAnalytics = async () => {
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
        } finally {
            setLoading(false);
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
            {/* Header */}
            <div className="mb-6">
                <button
                    onClick={() => navigate('/statistics')}
                    className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Statistics
                </button>
                <h1 className="text-2xl font-bold text-gray-900">Special Needs & Refugee Candidates Analytics</h1>
                <p className="text-gray-600 mt-1">Comprehensive analysis of vulnerable groups with gender perspective</p>
            </div>

            {/* Filter Controls */}
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200 mb-6">
                <div className="flex items-center space-x-4">
                    <Filter className="w-5 h-5 text-gray-500" />
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Assessment Series</label>
                        <select
                            value={selectedSeries}
                            onChange={(e) => setSelectedSeries(e.target.value)}
                            className="w-full md:w-96 border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="all">All Series</option>
                            {seriesList.map((series) => (
                                <option key={series.id} value={series.id}>
                                    {series.name} ({series.year})
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {analytics && (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center">
                                    <div className="bg-red-100 p-3 rounded-lg mr-4">
                                        <Heart className="w-8 h-8 text-red-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Special Needs Candidates</p>
                                        <p className="text-3xl font-bold text-gray-900">{analytics.special_needs.total}</p>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                                <div className="text-center">
                                    <p className="text-gray-600">Male</p>
                                    <p className="text-xl font-semibold text-blue-600">{analytics.special_needs.male}</p>
                                    <p className="text-xs text-gray-500">
                                        ({getPercentage(analytics.special_needs.male, analytics.special_needs.total)}%)
                                    </p>
                                </div>
                                <div className="h-12 w-px bg-gray-200"></div>
                                <div className="text-center">
                                    <p className="text-gray-600">Female</p>
                                    <p className="text-xl font-semibold text-pink-600">{analytics.special_needs.female}</p>
                                    <p className="text-xs text-gray-500">
                                        ({getPercentage(analytics.special_needs.female, analytics.special_needs.total)}%)
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center">
                                    <div className="bg-green-100 p-3 rounded-lg mr-4">
                                        <Globe className="w-8 h-8 text-green-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Refugee Candidates</p>
                                        <p className="text-3xl font-bold text-gray-900">{analytics.refugee.total}</p>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                                <div className="text-center">
                                    <p className="text-gray-600">Male</p>
                                    <p className="text-xl font-semibold text-blue-600">{analytics.refugee.male}</p>
                                    <p className="text-xs text-gray-500">
                                        ({getPercentage(analytics.refugee.male, analytics.refugee.total)}%)
                                    </p>
                                </div>
                                <div className="h-12 w-px bg-gray-200"></div>
                                <div className="text-center">
                                    <p className="text-gray-600">Female</p>
                                    <p className="text-xl font-semibold text-pink-600">{analytics.refugee.female}</p>
                                    <p className="text-xs text-gray-500">
                                        ({getPercentage(analytics.refugee.female, analytics.refugee.total)}%)
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Disability Type Breakdown */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">Breakdown by Disability Type</h2>
                            <div className="space-y-3">
                                {analytics.special_needs.by_disability_type.filter(d => d.count > 0).map((disability, index) => (
                                    <div key={index}>
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-sm font-medium text-gray-700">{disability.name}</span>
                                            <span className="text-sm text-gray-600">
                                                Total: {disability.count} (M: {disability.male}, F: {disability.female})
                                            </span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div
                                                className="bg-red-500 h-2 rounded-full"
                                                style={{ width: `${getPercentage(disability.count, analytics.special_needs.total)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                                {analytics.special_needs.by_disability_type.filter(d => d.count > 0).length === 0 && (
                                    <p className="text-gray-500 text-sm">No data available</p>
                                )}
                            </div>
                        </div>

                        {/* Nationality Breakdown */}
                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">Refugee Candidates by Nationality</h2>
                            <div className="space-y-3">
                                {analytics.refugee.by_nationality.filter(n => n.count > 0).map((nat, index) => (
                                    <div key={index}>
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-sm font-medium text-gray-700">{nat.nationality}</span>
                                            <span className="text-sm text-gray-600">
                                                Total: {nat.count} (M: {nat.male}, F: {nat.female})
                                            </span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div
                                                className="bg-green-500 h-2 rounded-full"
                                                style={{ width: `${getPercentage(nat.count, analytics.refugee.total)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                                {analytics.refugee.by_nationality.filter(n => n.count > 0).length === 0 && (
                                    <p className="text-gray-500 text-sm">No data available</p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Performance by Assessment Series - Special Needs */}
                    <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Special Needs Candidates by Assessment Series</h2>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Series</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pass Rate</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {analytics.special_needs.by_series.filter(s => s.total > 0).map((series, index) => (
                                        <tr key={index} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {series.series_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{series.total}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">{series.male}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-600">{series.female}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {series.pass_rate}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Performance by Assessment Series - Refugees */}
                    <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Refugee Candidates by Assessment Series</h2>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Series</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pass Rate</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {analytics.refugee.by_series.filter(s => s.total > 0).map((series, index) => (
                                        <tr key={index} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {series.series_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{series.total}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">{series.male}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-600">{series.female}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {series.pass_rate}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default SpecialNeedsAnalytics;
