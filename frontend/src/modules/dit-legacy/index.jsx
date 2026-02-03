import { Routes, Route } from 'react-router-dom';
import DitLegacyIndex from './pages/DitLegacyIndex';
import DitLegacyPersonDetail from './pages/DitLegacyPersonDetail';

export default function DitLegacyModule() {
  return (
    <Routes>
      <Route path="/" element={<DitLegacyIndex />} />
      <Route path=":personId" element={<DitLegacyPersonDetail />} />
    </Routes>
  );
}
