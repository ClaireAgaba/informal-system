import { Upload } from 'lucide-react';

export default function UploadMarksheets() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Upload className="h-7 w-7 text-green-600" />
          Upload Marksheets
        </h1>
        <p className="text-gray-600 mt-1">Upload completed marksheets with results</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <Upload className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Marksheets</h3>
        <p className="text-gray-600">This feature will be implemented soon</p>
      </div>
    </div>
  );
}
