/**
 * Grading System for Informal Assessment
 * Based on Theory and Practical score boundaries
 */

// Theory Scores Grading
export const THEORY_GRADES = [
  { grade: 'A+', min: 85, max: 100 },
  { grade: 'A', min: 80, max: 84 },
  { grade: 'B', min: 70, max: 79 },
  { grade: 'B-', min: 60, max: 69 },
  { grade: 'C', min: 50, max: 59 },
  { grade: 'C-', min: 40, max: 49 },
  { grade: 'D', min: 30, max: 39 },
  { grade: 'E', min: 0, max: 29 },
];

// Practical Scores Grading
export const PRACTICAL_GRADES = [
  { grade: 'A+', min: 90, max: 100 },
  { grade: 'A', min: 85, max: 89 },
  { grade: 'B+', min: 75, max: 84 },
  { grade: 'B', min: 65, max: 74 },
  { grade: 'B-', min: 60, max: 64 },
  { grade: 'C', min: 55, max: 59 },
  { grade: 'C-', min: 50, max: 54 },
  { grade: 'D', min: 40, max: 49 },
  { grade: 'D-', min: 30, max: 39 },
  { grade: 'E', min: 0, max: 29 },
];

// Pass marks (as per UVTAB grading system)
export const THEORY_PASS_MARK = 50;
export const PRACTICAL_PASS_MARK = 65;

/**
 * Get grade for a given mark and type
 * @param {number} mark - The mark scored
 * @param {string} type - 'theory' or 'practical'
 * @returns {string} The letter grade
 */
export const getGrade = (mark, type) => {
  if (mark === null || mark === undefined || mark === '') return '-';
  
  const numericMark = parseFloat(mark);
  if (isNaN(numericMark)) return '-';
  
  // -1 represents missing mark
  if (numericMark === -1) return '-';
  
  const grades = type === 'practical' ? PRACTICAL_GRADES : THEORY_GRADES;
  
  const gradeObj = grades.find(g => numericMark >= g.min && numericMark <= g.max);
  return gradeObj ? gradeObj.grade : '-';
};

/**
 * Get comment based on mark and type
 * @param {number} mark - The mark scored
 * @param {string} type - 'theory' or 'practical'
 * @returns {string} 'Success', 'Not Successful', or 'Missing'
 */
export const getComment = (mark, type) => {
  if (mark === null || mark === undefined || mark === '') return '-';
  
  const numericMark = parseFloat(mark);
  if (isNaN(numericMark)) return '-';
  
  // -1 represents missing mark (candidate enrolled but no mark available)
  if (numericMark === -1) return 'Missing';
  
  const passMark = type === 'practical' ? PRACTICAL_PASS_MARK : THEORY_PASS_MARK;
  return numericMark >= passMark ? 'Success' : 'Not Successful';
};

/**
 * Check if mark is passing
 * @param {number} mark - The mark scored
 * @param {string} type - 'theory' or 'practical'
 * @returns {boolean}
 */
export const isPassing = (mark, type) => {
  if (mark === null || mark === undefined || mark === '') return false;
  
  const numericMark = parseFloat(mark);
  if (isNaN(numericMark)) return false;
  
  const passMark = type === 'practical' ? PRACTICAL_PASS_MARK : THEORY_PASS_MARK;
  return numericMark >= passMark;
};

/**
 * Get grade color class
 * @param {string} grade - The letter grade
 * @returns {string} Tailwind color class
 */
export const getGradeColor = (grade) => {
  if (!grade || grade === '-') return 'text-gray-500';
  
  const firstChar = grade.charAt(0);
  switch (firstChar) {
    case 'A':
      return 'text-green-600 font-semibold';
    case 'B':
      return 'text-blue-600 font-semibold';
    case 'C':
      return 'text-yellow-600 font-semibold';
    case 'D':
      return 'text-orange-600 font-semibold';
    case 'E':
      return 'text-red-600 font-semibold';
    default:
      return 'text-gray-500';
  }
};

/**
 * Get comment color class
 * @param {string} comment - The comment text
 * @returns {string} Tailwind color class
 */
export const getCommentColor = (comment) => {
  if (comment === 'Success') return 'text-green-600 font-semibold';
  if (comment === 'Not Successful') return 'text-red-600 font-semibold';
  if (comment === 'Missing') return 'text-orange-600 font-semibold';
  return 'text-gray-500';
};

/**
 * Get status badge color
 * @param {string} status - 'Normal', 'Retake', or 'Missing'
 * @returns {string} Tailwind badge classes
 */
export const getStatusBadgeColor = (status) => {
  switch (status) {
    case 'Normal':
      return 'bg-blue-100 text-blue-800';
    case 'Retake':
      return 'bg-yellow-100 text-yellow-800';
    case 'Missing':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};
