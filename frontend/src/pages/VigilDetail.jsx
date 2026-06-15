import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

export default function VigilDetail() {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetch(`/api/scans/${id}`).then((r) => r.json()).then(setScan).catch(() => {});
  }, [id]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const r = await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scan_id: parseInt(id), agent_type: 'scan_advisor' }),
      });
      const data = await r.json();
      setAnalysis(data);
    } catch (e) {
      console.error(e);
    }
    setAnalyzing(false);
  };

  if (!scan) return <p className="text-gold-dim italic">Loading...</p>;

  const ports = scan.ports || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ Vigil #{scan.id}</h1>
        <span className={`gothic-badge gothic-badge-${scan.status === 'completed' ? 'gold' : 'crimson'}`}>{scan.status}</span>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card>
          <p className="text-gold-dim text-xs font-heading uppercase tracking-wider">Profile</p>
          <p className="font-display text-gold-500 text-lg">{scan.scan_profile}</p>
        </Card>
        <Card>
          <p className="text-gold-dim text-xs font-heading uppercase tracking-wider">Ports Open</p>
          <p className="font-display text-gold-500 text-lg">{ports.length}</p>
        </Card>
        <Card>
          <p className="text-gold-dim text-xs font-heading uppercase tracking-wider">Risk Score</p>
          <p className={`font-display text-2xl ${(scan.risk_score || 0) >= 50 ? 'text-crimson-400' : 'text-gold-500'}`}>
            {scan.risk_score ?? '-'}
          </p>
        </Card>
        <Card>
          <p className="text-gold-dim text-xs font-heading uppercase tracking-wider">Target ID</p>
          <p className="font-display text-gold-500 text-lg">#{scan.target_id}</p>
        </Card>
      </div>

      {ports.length > 0 && (
        <Card>
          <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">✠ Ports & Services</h2>
          <div className="overflow-x-auto">
            <table className="gothic-table">
              <thead>
                <tr>
                  <th>Port</th>
                  <th>Protocol</th>
                  <th>State</th>
                  <th>Service</th>
                  <th>Product</th>
                  <th>Version</th>
                  <th>CVEs</th>
                </tr>
              </thead>
              <tbody>
                {ports.map((p, i) => (
                  <tr key={i}>
                    <td className="text-gold-500">{p.port}</td>
                    <td>{p.protocol}</td>
                    <td>
                      <Badge variant={p.state === 'open' ? 'crimson' : 'gold'}>{p.state}</Badge>
                    </td>
                    <td className="font-body">{p.service}</td>
                    <td className="text-gold-dim text-xs">{p.product}</td>
                    <td className="text-gold-dim text-xs">{p.version}</td>
                    <td>
                      {p.vulnerability_hints?.length > 0 ? (
                        <div className="flex gap-1 flex-wrap">
                          {p.vulnerability_hints.map((v) => (
                            <Badge key={v} variant="crimson">{v}</Badge>
                          ))}
                        </div>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Card>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider">✠ AI Analysis</h2>
          <button className="gothic-btn text-xs" onClick={handleAnalyze} disabled={analyzing}>
            {analyzing ? 'Analyzing...' : 'Analyze with AI'}
          </button>
        </div>
        {analysis ? (
          <div className="text-sm whitespace-pre-wrap font-body leading-relaxed">
            <p className="text-gold-dim text-xs mb-2">Model: {analysis.model_used}</p>
            {analysis.response}
          </div>
        ) : (
          <p className="text-gold-dim italic text-sm">Click "Analyze with AI" for intelligence.</p>
        )}
      </Card>
    </div>
  );
}
