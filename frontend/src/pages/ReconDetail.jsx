import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

export default function ReconDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`/api/osint/${id}`).then((r) => r.json()).then(setData).catch(() => {});
  }, [id]);

  if (!data) return <p className="text-gold-dim italic">Loading...</p>;

  const findings = data.findings || {};

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ Recon #{data.id}</h1>

      {findings.discovery && (
        <Card>
          <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">✠ Subdomains</h2>
          <p className="text-gold-dim text-sm mb-2">{findings.discovery.subdomain_count || 0} found</p>
          <div className="flex flex-wrap gap-2">
            {(findings.discovery.subdomains || []).map((sub, i) => (
              <Badge key={i}>{sub}</Badge>
            ))}
          </div>
        </Card>
      )}

      {findings.discovery?.dns_records && (
        <Card>
          <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">✠ DNS Records</h2>
          <div className="overflow-x-auto">
            <table className="gothic-table">
              <thead>
                <tr><th>Type</th><th>Value</th></tr>
              </thead>
              <tbody>
                {Object.entries(findings.discovery.dns_records).map(([type, values]) => (
                  <tr key={type}>
                    <td className="font-heading text-gold-500 text-xs uppercase">{type}</td>
                    <td className="font-mono text-xs">{(Array.isArray(values) ? values : [values]).join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {findings.tech_detect && (
        <Card>
          <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">✠ Technology Stack</h2>
          <div className="space-y-2">
            {findings.tech_detect.server && (
              <p className="text-sm"><span className="text-gold-dim">Server:</span> {findings.tech_detect.server}</p>
            )}
            {(findings.tech_detect.cms || []).length > 0 && (
              <div>
                <span className="text-gold-dim text-sm">CMS:</span>
                <div className="flex gap-2 mt-1">{(findings.tech_detect.cms).map((c, i) => <Badge key={i}>{c}</Badge>)}</div>
              </div>
            )}
            {(findings.tech_detect.frameworks || []).length > 0 && (
              <div>
                <span className="text-gold-dim text-sm">Frameworks:</span>
                <div className="flex gap-2 mt-1">{(findings.tech_detect.frameworks).map((f, i) => <Badge key={i}>{f}</Badge>)}</div>
              </div>
            )}
          </div>
        </Card>
      )}

      {findings.email_recon && (
        <Card>
          <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">✠ Email Recon</h2>
          <p className="text-sm"><span className="text-gold-dim">Has MX:</span> {findings.email_recon.has_mx ? 'Yes' : 'No'}</p>
          {(findings.email_recon.guessed_emails || []).length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {findings.email_recon.guessed_emails.map((e, i) => (
                <Badge key={i} variant="crimson">{e.email}</Badge>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
