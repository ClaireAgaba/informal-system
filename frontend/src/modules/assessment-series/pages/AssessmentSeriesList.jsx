import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronRight, Plus, Eye, Edit, Calendar, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import assessmentSeriesApi from '../services/assessmentSeriesApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';

const AssessmentSeriesList = () => {
  const navigate = useNavigate();
  const [expandedYears, setExpandedYears] = useState(new Set([new Date().getFullYear()]));
  const currentYear = new Date().getFullYear();

  // Fetch all assessment series
  const { data, isLoading, error } = useQuery({
    queryKey: ['assessment-series'],
    queryFn: () => assessmentSeriesApi.getAll(),
  });

  const series = data?.data?.results || [];

  // Group series by year
  const seriesByYear = useMemo(() => {
    const grouped = {};
    
    series.forEach((s) => {
      const year = new Date(s.start_date).getFullYear();
      if (!grouped[year]) {
        grouped[year] = [];
      }
      grouped[year].push(s);
    });

    // Sort years in descending order and series within each year by start_date
    const sortedYears = Object.keys(grouped).sort((a, b) => b - a);
    sortedYears.forEach(year => {
      grouped[year].sort((a, b) => new Date(b.start_date) - new Date(a.start_date));
    });

    return { grouped, years: sortedYears };
  }, [series]);

  const toggleYear = (year) => {
    const newExpanded = new Set(expandedYears);
    if (newExpanded.has(year)) {
      newExpanded.delete(year);
    } else {
      newExpanded.add(year);
    }
    setExpandedYears(newExpanded);
  };

  const getStatusBadge = (series) => {
    const today = new Date();
    const startDate = new Date(series.start_date);
    const endDate = new Date(series.end_date);

    if (series.is_current) {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Current
        </span>
      );
    } else if (today < startDate) {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
          <Clock className="w-3 h-3 mr-1" />
          Upcoming
        </span>
      );
    } else if (today >= startDate && today <= endDate) {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
          <AlertCircle className="w-3 h-3 mr-1" />
          Ongoing
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
          Completed
        </span>
      );
    }
  };

  // Generate years from 2025 to current year + 2
  const availableYears = useMemo(() => {
    const years = [];
    for (let year = currentYear + 2; year >= 2025; year--) {
      years.push(year);
    }
    return years;
  }, [currentYear]);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Assessment Series</h1>
            <p className="text-gray-600 mt-1">Manage assessment periods and schedules</p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/assessment-series/new')}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Series
          </Button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <Card>
          <Card.Content className="py-12 text-center text-gray-500">
            Loading assessment series...
          </Card.Content>
        </Card>
      ) : error ? (
        <Card>
          <Card.Content className="py-12 text-center text-red-500">
            Error loading series: {error.message}
          </Card.Content>
        </Card>
      ) : (
        <div className="space-y-4">
          {availableYears.map((year) => {
            const yearSeries = seriesByYear.grouped[year] || [];
            const isExpanded = expandedYears.has(year);
            const seriesCount = yearSeries.length;

            return (
              <Card key={year}>
                {/* Year Header */}
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => toggleYear(year)}
                >
                  <div className="flex items-center space-x-3">
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-500" />
                    )}
                    <Calendar className="w-5 h-5 text-primary-600" />
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{year}</h3>
                      <p className="text-sm text-gray-600">
                        {seriesCount} {seriesCount === 1 ? 'series' : 'series'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {year === currentYear && (
                      <span className="px-2 py-1 text-xs font-medium bg-primary-100 text-primary-800 rounded-full">
                        This Year
                      </span>
                    )}
                  </div>
                </div>

                {/* Year Content */}
                {isExpanded && (
                  <div className="border-t border-gray-200">
                    {yearSeries.length === 0 ? (
                      <div className="p-8 text-center text-gray-500">
                        No assessment series for {year} yet.
                      </div>
                    ) : (
                      <div className="divide-y divide-gray-200">
                        {yearSeries.map((s) => (
                          <div
                            key={s.id}
                            className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                            onClick={() => navigate(`/assessment-series/${s.id}`)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-3 mb-2">
                                  <h4 className="text-base font-semibold text-gray-900">
                                    {s.name}
                                  </h4>
                                  {getStatusBadge(s)}
                                  {s.results_released && (
                                    <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                                      Results Released
                                    </span>
                                  )}
                                  {s.dont_charge && (
                                    <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                                      Don't Charge
                                    </span>
                                  )}
                                </div>
                                <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                                  <div>
                                    <span className="font-medium">Start:</span>{' '}
                                    {formatDate(s.start_date)}
                                  </div>
                                  <div>
                                    <span className="font-medium">End:</span>{' '}
                                    {formatDate(s.end_date)}
                                  </div>
                                  <div>
                                    <span className="font-medium">Results:</span>{' '}
                                    {formatDate(s.date_of_release)}
                                  </div>
                                </div>
                              </div>
                              <div
                                className="flex items-center space-x-2 ml-4"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <button
                                  onClick={() => navigate(`/assessment-series/${s.id}`)}
                                  className="text-gray-600 hover:text-primary-600"
                                  title="View"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => navigate(`/assessment-series/${s.id}/edit`)}
                                  className="text-gray-600 hover:text-primary-600"
                                  title="Edit"
                                >
                                  <Edit className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AssessmentSeriesList;
