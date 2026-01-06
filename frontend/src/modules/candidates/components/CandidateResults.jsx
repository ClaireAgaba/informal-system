import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, AlertCircle, Plus, Edit } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import Button from '@shared/components/Button';
import AddResultsModal from './AddResultsModal';
import EditResultsModal from './EditResultsModal';
import FormalAddResultsModal from './FormalAddResultsModal';
import FormalEditResultsModal from './FormalEditResultsModal';
import WorkersPasAddResultsModal from './WorkersPasAddResultsModal';
import {
  getGrade,
  getComment,
  getGradeColor,
  getCommentColor,
  getStatusBadgeColor,
} from '../utils/gradingSystem';

const CandidateResults = ({ candidateId, registrationCategory, hasEnrollments, enrollments }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // Load current user from localStorage
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setCurrentUser(user);
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);
  // Fetch results based on registration category
  const { data: resultsData, isLoading, error } = useQuery({
    queryKey: ['candidate-results', candidateId, registrationCategory],
    queryFn: () => candidateApi.getResults(candidateId),
    enabled: !!candidateId && hasEnrollments,
  });

  const results = resultsData?.data || [];
  
  // Debug logging
  console.log('Registration Category:', registrationCategory);
  console.log('Results Data:', resultsData);
  console.log('Results:', results);
  
  // Check if candidate is enrolled
  if (!hasEnrollments) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-orange-400 mx-auto mb-4" />
        <p className="text-lg font-semibold text-gray-900">Candidate Not Enrolled</p>
        <p className="text-sm text-gray-500 mt-2">
          This candidate must be enrolled in an assessment series before results can be recorded.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading results...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">Failed to load results</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  // Render based on registration category
  if (registrationCategory === 'modular') {
    return (
      <>
        <ModularResults 
          results={results} 
          onAddResults={() => setShowAddModal(true)}
          onEditResults={() => setShowEditModal(true)}
          isCenterRep={currentUser?.user_type === 'center_representative'}
        />
        <AddResultsModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          candidateId={candidateId}
          enrollments={enrollments || []}
        />
        <EditResultsModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          candidateId={candidateId}
          results={results}
        />
      </>
    );
  }

  // Formal results
  if (registrationCategory === 'formal') {
    return (
      <>
        <FormalResults 
          results={results} 
          onAddResults={() => setShowAddModal(true)}
          isCenterRep={currentUser?.user_type === 'center_representative'}
          onEditResults={() => setShowEditModal(true)}
        />
        <FormalAddResultsModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          candidateId={candidateId}
          enrollments={enrollments || []}
        />
        <FormalEditResultsModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          candidateId={candidateId}
          results={results}
        />
      </>
    );
  }

  // Workers PAS results
  if (registrationCategory === 'workers_pas') {
    return (
      <>
        <WorkersPasResults 
          results={results} 
          onAddResults={() => setShowAddModal(true)}
          isCenterRep={currentUser?.user_type === 'center_representative'}
        />
        <WorkersPasAddResultsModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          candidate={{ id: candidateId }}
          enrollments={enrollments || []}
        />
      </>
    );
  }

  // Placeholder for other categories
  return (
    <div className="text-center py-12">
      <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <p className="text-gray-600">
        Results view for {registrationCategory} category coming soon...
      </p>
    </div>
  );
};

// Modular Results Component
const ModularResults = ({ results, onAddResults, onEditResults, isCenterRep }) => {
  const hasResults = results && results.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          Modular Assessment Results
        </h3>
        <div className="flex items-center gap-3">
          {hasResults && (
            <div className="text-sm text-gray-500">
              Total Modules: {results.length}
            </div>
          )}
          {/* Hide Add/Edit buttons for center representatives */}
          {!isCenterRep && (
            hasResults ? (
              <Button
                variant="primary"
                size="sm"
                onClick={onEditResults}
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit Results
              </Button>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={onAddResults}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Results
              </Button>
            )
          )}
        </div>
      </div>

      {/* Results Table */}
      {!hasResults ? (
        <div className="text-center py-12 border border-gray-200 rounded-lg bg-gray-50">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No results available yet</p>
          <p className="text-sm text-gray-500 mt-2">
            Results will appear here once marks are entered
          </p>
        </div>
      ) : (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Assessment Series
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Module
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mark
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Grade
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Comment
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Entered By
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {results.map((result, index) => {
              const type = result.type?.toLowerCase() || 'practical';
              const grade = getGrade(result.mark, type);
              const comment = getComment(result.mark, type);

              return (
                <tr key={result.id || index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {result.assessment_series_name || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    <div>
                      <div className="font-medium">{result.module_name || '-'}</div>
                      <div className="text-xs text-gray-500">{result.module_code || ''}</div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    <span className="capitalize">{result.type || 'Practical'}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-center font-semibold text-gray-900">
                    {isCenterRep 
                      ? (result.mark !== null && result.mark !== undefined ? 'Uploaded' : '-')
                      : (result.mark !== null && result.mark !== undefined ? result.mark : '-')
                    }
                  </td>
                  <td className={`px-4 py-3 text-sm text-center ${getGradeColor(grade)}`}>
                    {grade}
                  </td>
                  <td className={`px-4 py-3 text-sm text-center ${getCommentColor(comment)}`}>
                    {comment}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeColor(result.status)}`}>
                      {result.status || 'Normal'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {result.entered_by || '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      )}
    </div>
  );
};

// Formal Results Component
const FormalResults = ({ results, onAddResults, onEditResults, isCenterRep }) => {
  const hasResults = results && results.length > 0;

  // Group results by level and exam/paper
  const groupedResults = hasResults ? results.reduce((acc, result) => {
    const levelKey = result.level?.name || 'Unknown Level';
    if (!acc[levelKey]) {
      acc[levelKey] = {
        level: result.level,
        items: []
      };
    }
    
    const itemKey = result.exam_or_paper || 'Unknown';
    let item = acc[levelKey].items.find(i => i.name === itemKey);
    
    if (!item) {
      item = {
        name: itemKey,
        isExam: result.is_exam,
        results: []
      };
      acc[levelKey].items.push(item);
    }
    
    item.results.push(result);
    return acc;
  }, {}) : {};

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          {registrationCategory === 'Modular' ? 'Modular' : registrationCategory === 'Workers PAS' ? 'Workers PAS' : 'Formal'} Assessment Results
        </h3>
        <div className="flex items-center gap-3">
          {hasResults && (
            <div className="text-sm text-gray-500">
              Total Results: {results.length}
            </div>
          )}
          {/* Hide Add/Edit buttons for center representatives */}
          {!isCenterRep && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={onAddResults}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Results
              </Button>
              {hasResults && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onEditResults}
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Results
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Results Table */}
      {!hasResults ? (
        <div className="text-center py-12 border border-gray-200 rounded-lg bg-gray-50">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No results available yet</p>
          <p className="text-sm text-gray-500 mt-2">
            Results will appear here once marks are entered
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedResults).map(([levelName, levelData]) => (
            <div key={levelName} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* Level Header */}
              <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
                <h4 className="text-sm font-semibold text-gray-900">
                  {levelName}
                  <span className="ml-2 text-xs font-normal text-gray-500">
                    ({levelData.level?.structure_type === 'modules' ? 'Module-based' : 'Paper-based'})
                  </span>
                </h4>
              </div>

              {/* Results Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Assessment Series
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Level
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Mark
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Grade
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Comment
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Entered By
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {levelData.items.map((item) => 
                      item.results.map((result, index) => {
                        const type = result.type?.toLowerCase() || 'practical';
                        const grade = getGrade(result.mark, type);
                        const comment = getComment(result.mark, type);

                        return (
                          <tr key={result.id || index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {result.assessment_series?.name || '-'}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              <div className="font-medium">{levelName}</div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              <span className="capitalize">{result.type || 'Practical'}</span>
                            </td>
                            <td className="px-4 py-3 text-sm text-center font-semibold text-gray-900">
                              {isCenterRep 
                                ? (result.mark !== null && result.mark !== undefined ? 'Uploaded' : '-')
                                : (result.mark !== null && result.mark !== undefined ? result.mark : '-')
                              }
                            </td>
                            <td className={`px-4 py-3 text-sm text-center font-semibold ${getGradeColor(grade)}`}>
                              {grade}
                            </td>
                            <td className={`px-4 py-3 text-sm text-center ${getCommentColor(comment)}`}>
                              {comment}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeColor(result.status)}`}>
                                {result.status || 'Normal'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {result.entered_by || '-'}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Workers PAS Results Component
const WorkersPasResults = ({ results, onAddResults, isCenterRep }) => {
  const hasResults = results && results.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          Worker's PAS Assessment Results
        </h3>
        <div className="flex items-center gap-3">
          {hasResults && (
            <div className="text-sm text-gray-500">
              Total Papers: {results.length}
            </div>
          )}
          {/* Hide Add Results button for center representatives */}
          {!isCenterRep && (
            <Button
              variant="primary"
              size="sm"
              onClick={onAddResults}
            >
              <Plus className="w-4 h-4 mr-2" />
              {hasResults ? 'Add More Results' : 'Add Results'}
            </Button>
          )}
        </div>
      </div>

      {!hasResults ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">No results recorded yet</p>
          {!isCenterRep && (
            <Button variant="primary" size="sm" onClick={onAddResults}>
              <Plus className="w-4 h-4 mr-2" />
              Add Results
            </Button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Assessment Series
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Level
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Module
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Paper
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mark
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Grade
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Comment
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entered By
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((result) => {
                  const grade = result.grade || getGrade(result.mark, 'practical');
                  const comment = result.comment || getComment(result.mark, 'practical');

                  return (
                    <tr key={result.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {result.assessment_series_name || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {result.level_name || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{result.module_code || '-'}</div>
                          <div className="text-xs text-gray-500">{result.module_name || '-'}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{result.paper_code || '-'}</div>
                          <div className="text-xs text-gray-500">{result.paper_name || '-'}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          Practical
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-center font-semibold text-gray-900">
                        {isCenterRep 
                          ? (result.mark !== null && result.mark !== undefined ? 'Uploaded' : '-')
                          : (result.mark !== null && result.mark !== undefined ? result.mark : '-')
                        }
                      </td>
                      <td className={`px-4 py-3 text-sm text-center font-semibold ${getGradeColor(grade)}`}>
                        {grade}
                      </td>
                      <td className={`px-4 py-3 text-sm text-center ${getCommentColor(comment)}`}>
                        {comment}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeColor(result.status)}`}>
                          {result.status || 'Normal'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {result.entered_by_name || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default CandidateResults;
