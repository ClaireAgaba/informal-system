import { Routes, Route } from 'react-router-dom';
import FeesIndex from './pages/FeesIndex';
import CandidateFees from './pages/CandidateFees';
import CenterFees from './pages/CenterFees';
import CenterFeeView from './pages/CenterFeeView';

export default function FeesModule() {
  return (
    <Routes>
      <Route path="/" element={<FeesIndex />} />
      <Route path="candidate-fees" element={<CandidateFees />} />
      <Route path="center-fees" element={<CenterFees />} />
      <Route path="center-fees/:id" element={<CenterFeeView />} />
    </Routes>
  );
}
