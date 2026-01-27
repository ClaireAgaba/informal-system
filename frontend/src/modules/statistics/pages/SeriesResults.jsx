import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Users, TrendingUp, FileText, Award, ChevronDown, ArrowLeft } from 'lucide-react';
import statisticsApi from '../services/statisticsApi';

const SeriesResults = () => {
    const { seriesId } = useParams();
    const navigate = useNavigate();
    const [seriesList, setSeriesList] = useState([]);
    const [selectedSeriesId, setSelectedSeriesId] = useState(seriesId || '');
    const [results, setResults] = useState(null);
    const [loadingList, setLoadingList] = useState(true);
    const [loading, setLoading] = useState(false);
    const [exportingExcel, setExportingExcel] = useState(false);

    useEffect(() => {
        fetchSeriesList();
        if (seriesId) { // If seriesId is present in URL, fetch results for it
            fetchSeriesResults(seriesId);
        }
    }, []);

    // Changed: Don't auto-fetch, wait for Generate button
    const handleSeriesChange = (id) => {
        setSelectedSeriesId(id);
        setResults(null); // Clear previous results
    };

    const handleGenerateReport = async () => {
        if (!selectedSeriesId) {
            alert('Please select an assessment series first');
            return;
        }
        fetchSeriesResults(selectedSeriesId);
    };


    const handleExportExcel = async () => {
        if (!selectedSeriesId) {
            alert('Please select an assessment series first');
            return;
        }

        try {
            setExportingExcel(true);
            const response = await statisticsApi.exportSeriesExcel(selectedSeriesId);

            // Get filename from Content-Disposition header
            const contentDisposition = response.headers['content-disposition'];
            let filename = 'series_results.xlsx';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            // Download the file
            const blob = new Blob([response.data], {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            });
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

    const fetchSeriesList = async () => {
        try {
            setLoadingList(true);
            console.log('Fetching series list...');
            const response = await statisticsApi.getAssessmentSeriesList();
            console.log('Series list response:', response);
            console.log('Series data:', response.data);
            setSeriesList(response.data);
            console.log('Series list set successfully, count:', response.data.length);
        } catch (error) {
            console.error('Error fetching series list:', error);
            console.error('Error response:', error.response);
        } finally {
            setLoadingList(false);
        }
    };

    const fetchSeriesResults = async (id) => {
        try {
            setLoading(true);
            const response = await statisticsApi.getSeriesResults(id);
            setResults(response.data);
        } catch (error) {
            console.error('Error fetching series results:', error);
        } finally {
            setLoading(false);
        }
    };

    const getPercentage = (value, total) => {
        if (total === 0) return '0.0';
        return ((value / total) * 100).toFixed(1);
    };

    if (loadingList) {
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
                <h1 className="text-2xl font-bold text-gray-900">Assessment Series Results Analysis</h1>
                <p className="text-gray-600 mt-1">Detailed performance metrics with gender breakdowns</p>
            </div>

            {/* Series Selector */}
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200 mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Assessment Series to Analyze</label>
                <select
                    value={selectedSeriesId}
                    onChange={(e) => handleSeriesChange(e.target.value)}
                    className="w-full md:w-96 border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="">-- Select a series --</option>
                    {seriesList.map((series) => (
                        <option key={series.id} value={series.id}>
                            {series.name} ({series.year}) - {series.total_candidates} candidates
                        </option>
                    ))}
                </select>

                {/* Action Buttons */}
                <div className="flex gap-3 mt-4">
                    <button
                        onClick={handleGenerateReport}
                        disabled={!selectedSeriesId || loading}
                        className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                        {loading ? (
                            <>
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Generating...
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                Generate Report
                            </>
                        )}
                    </button>

                    <button
                        onClick={handleExportExcel}
                        disabled={!selectedSeriesId || exportingExcel}
                        className="px-6 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                        {exportingExcel ? (
                            <>
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Exporting...
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                Export to Excel
                            </>
                        )}
                    </button>
                </div>

                {!selectedSeriesId && (
                    <p className="mt-3 text-sm text-gray-500">
                        Please select an assessment series above, then click "Generate Report" to view detailed results
                    </p>
                )}
            </div>

            {/* Results section - only shows after Generate Report is clicked */}
            {results && (
                <>
                    {/* Overview Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Total Candidates</p>
                                    <p className="text-3xl font-bold text-gray-900">{results.overview.total_candidates}</p>
                                    <p className="text-xs text-gray-500">
                                        Male: {results.overview.male} | Female: {results.overview.female}
                                    </p>
                                </div>
                                <div className="bg-blue-100 p-3 rounded-lg">
                                    <Users className="w-8 h-8 text-blue-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Overall Pass Rate</p>
                                    <p className="text-3xl font-bold text-gray-900">{results.overview.pass_rate}%</p>
                                    <p className="text-xs text-gray-500">
                                        M: {results.overview.male_pass_rate}% | F: {results.overview.female_pass_rate}%
                                    </p>
                                </div>
                                <div className="bg-green-100 p-3 rounded-lg">
                                    <TrendingUp className="w-8 h-8 text-green-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Total Results</p>
                                    <p className="text-3xl font-bold text-gray-900">{results.overview.total_results}</p>
                                    <p className="text-xs text-gray-500">All assessments</p>
                                </div>
                                <div className="bg-yellow-100 p-3 rounded-lg">
                                    <FileText className="w-8 h-8 text-yellow-600" />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Series Period</p>
                                    <p className="text-lg font-bold text-gray-900">{results.series.name}</p>
                                    <p className="text-xs text-gray-500">
                                        {new Date(results.series.start_date).toLocaleDateString()} - {new Date(results.series.end_date).toLocaleDateString()}
                                    </p>
                                </div>
                                <div className="bg-purple-100 p-3 rounded-lg">
                                    <Award className="w-8 h-8 text-purple-600" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Pass Rate Comparison */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">Pass Rate by Gender</h2>
                            <div className="space-y-4">
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center">
                                            <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                                            <span className="text-sm text-gray-700">Male</span>
                                        </div>
                                        <span className="text-sm font-medium text-blue-600">
                                            {results.overview.male_pass_rate}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-3">
                                        <div
                                            className="bg-blue-500 h-3 rounded-full"
                                            style={{ width: `${results.overview.male_pass_rate}% ` }}
                                        ></div>
                                    </div>
                                </div>

                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center">
                                            <div className="w-3 h-3 rounded-full bg-pink-500 mr-2"></div>
                                            <span className="text-sm text-gray-700">Female</span>
                                        </div>
                                        <span className="text-sm font-medium text-pink-600">
                                            {results.overview.female_pass_rate}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-3">
                                        <div
                                            className="bg-pink-500 h-3 rounded-full"
                                            style={{ width: `${results.overview.female_pass_rate}% ` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Grade Distribution */}
                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">Grade Distribution</h2>
                            <div className="space-y-2">
                                {Object.entries(results.grade_distribution).length > 0 ? (
                                    Object.entries(results.grade_distribution)
                                        .sort((a, b) => b[1].total - a[1].total)
                                        .slice(0, 5)
                                        .map(([grade, data]) => (
                                            <div key={grade} className="flex items-center justify-between text-sm">
                                                <span className="font-medium text-gray-700">{grade}</span>
                                                <div className="flex items-center space-x-4">
                                                    <span className="text-blue-600">M: {data.male}</span>
                                                    <span className="text-pink-600">F: {data.female}</span>
                                                    <span className="font-semibold text-gray-900">Total: {data.total}</span>
                                                </div>
                                            </div>
                                        ))
                                ) : (
                                    <p className="text-gray-500 text-sm">No grade data available</p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Performance by Category */}
                    <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance by Registration Category</h2>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male Passed</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female Passed</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Passed</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male Pass %</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female Pass %</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Overall Pass %</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {Object.entries(results.by_category).map(([category, data]) => (
                                        <tr key={category} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="text-sm font-medium text-gray-900 capitalize">
                                                    {category === 'workers_pas' ? "Worker's PAS" : category}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data.total}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">{data.male}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-600">{data.female}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-700 font-medium">{data.male_passed}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-700 font-medium">{data.female_passed}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">{data.total_passed}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-800 font-semibold">{data.male_pass_rate}%</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-800 font-semibold">{data.female_pass_rate}%</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-green-700 font-bold">
                                                {data.pass_rate}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Performance by Sector */}
                    {results.by_sector && results.by_sector.length > 0 && (
                        <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance by Sector</h2>
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male Passed</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female Passed</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Passed</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male Pass %</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female Pass %</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Overall Pass %</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {results.by_sector.map((sector, index) => (
                                            <tr key={index} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                    {sector.sector_name}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{sector.total}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">{sector.male}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-600">{sector.female}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-700 font-medium">{sector.male_passed}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-700 font-medium">{sector.female_passed}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">{sector.total_passed}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-800 font-semibold">{sector.male_pass_rate}%</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-800 font-semibold">{sector.female_pass_rate}%</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-700 font-bold">{sector.pass_rate}%</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Performance by Occupation */}
                    <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance by Occupation</h2>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Occupation</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male Passed</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female Passed</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Passed</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male Pass %</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female Pass %</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Overall Pass %</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {results.by_occupation.map((occ, index) => (
                                        <tr key={index} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {occ.occupation_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{occ.occupation_code}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{occ.total}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">{occ.male}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-600">{occ.female}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-700 font-medium">{occ.male_passed}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-700 font-medium">{occ.female_passed}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">{occ.total_passed}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-800 font-semibold">{occ.male_pass_rate}%</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-pink-808 font-semibold">{occ.female_pass_rate}%</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-green-700 font-bold">{occ.pass_rate}%</td>
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

export default SeriesResults;
