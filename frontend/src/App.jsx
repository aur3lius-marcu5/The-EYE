import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Sanctum from './pages/Sanctum';
import Vigils from './pages/Vigils';
import VigilDetail from './pages/VigilDetail';
import Recon from './pages/Recon';
import ReconDetail from './pages/ReconDetail';
import Targets from './pages/Targets';
import Scriptorium from './pages/Scriptorium';
import Pipeline from './pages/Pipeline';
import PipelineRun from './pages/PipelineRun';

export default function App() {
  return (
    <div className="flex min-h-screen bg-midnight-900">
      <Sidebar />
      <main className="flex-1 ml-56 p-6 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Sanctum />} />
          <Route path="/vigils" element={<Vigils />} />
          <Route path="/vigils/:id" element={<VigilDetail />} />
          <Route path="/recon" element={<Recon />} />
          <Route path="/recon/:id" element={<ReconDetail />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/pipeline/:id" element={<PipelineRun />} />
          <Route path="/reports" element={<Scriptorium />} />
        </Routes>
      </main>
    </div>
  );
}
