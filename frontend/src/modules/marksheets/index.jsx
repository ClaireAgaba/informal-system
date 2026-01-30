import { Routes, Route } from 'react-router-dom';
import MarksheetsIndex from './pages/MarksheetsIndex';
import GenerateMarksheets from './pages/GenerateMarksheets';
import UploadMarksheets from './pages/UploadMarksheets';
import PrintMarksheets from './pages/PrintMarksheets';
import ExportResults from './pages/ExportResults';

export default function MarksheetsModule() {
  return (
    <Routes>
      <Route path="/" element={<MarksheetsIndex />} />
      <Route path="generate" element={<GenerateMarksheets />} />
      <Route path="upload" element={<UploadMarksheets />} />
      <Route path="print" element={<PrintMarksheets />} />
      <Route path="export" element={<ExportResults />} />
    </Routes>
  );
}
