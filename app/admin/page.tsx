"use client";
import React, { useState } from 'react';

const MENU_ITEMS = [
  'Summary', 'Console', 'Hardware', 'Cloud-init', 'Options', 
  'Task history', 'Monitor', 'Backup', 'Replication', 'Snapshots', 
  'Firewalls', 'Permissions'
];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('Summary');

  return (
    <div className="page active" style={{ padding: '0 20px 40px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--g1-text)' }}>Datacenter</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button className="btn-ghost" style={{ padding: '6px 12px', fontSize: '13px' }}>Search</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '20px', flex: 1, alignItems: 'flex-start' }}>
        
        {/* LEFT LIST FRAME */}
        <div style={{ width: '220px', flexShrink: 0, borderRight: '1px solid var(--g1-border)', paddingRight: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {MENU_ITEMS.map(item => (
            <div 
              key={item}
              onClick={() => setActiveTab(item)} 
              style={{ padding: '8px 12px', borderRadius: '6px', cursor: 'pointer', background: activeTab === item ? 'rgba(37,99,235,0.1)' : 'transparent', color: activeTab === item ? '#60A5FA' : 'var(--g1-text)', fontWeight: activeTab === item ? 600 : 400, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', transition: 'background 0.2s' }}>
              <div style={{ width: '12px', height: '12px', background: activeTab === item ? '#60A5FA' : 'var(--g1-muted)', borderRadius: '2px' }}></div>
              {item}
            </div>
          ))}
        </div>

        {/* RIGHT CONTENT FRAME */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {activeTab === 'Summary' ? (
            <>
              {/* HEALTH */}
              <div className="pm-card" style={{ padding: '20px', animation: 'fadeUp 0.3s ease' }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#3b82f6', marginBottom: '24px' }}>Health</div>
                <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'flex-start' }}>
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{ fontWeight: 600, marginBottom: '16px' }}>Status</div>
                    <div style={{ width: '48px', height: '48px', background: '#22c55e', borderRadius: '50%', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '24px' }}>✓</div>
                    <div style={{ fontSize: '12px', marginTop: '12px', color: 'var(--g1-text)' }}>Cluster: eu-alps, Quorate: Yes</div>
                  </div>
                  <div style={{ textAlign: 'center', flex: 1 }}>
                     <div style={{ fontWeight: 600, marginBottom: '16px' }}>Nodes</div>
                     <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                       <div style={{ fontSize: '13px', display: 'flex', alignItems: 'center', gap: '24px' }}><span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><span style={{ color: '#22c55e', fontSize: '16px' }}>✓</span> Online</span> <span style={{ fontWeight: 600 }}>3</span></div>
                       <div style={{ fontSize: '13px', display: 'flex', alignItems: 'center', gap: '24px' }}><span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><span style={{ color: '#ef4444', fontSize: '16px' }}>✕</span> Offline</span> <span style={{ fontWeight: 600 }}>0</span></div>
                     </div>
                  </div>
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{ fontWeight: 600, marginBottom: '16px' }}>Ceph</div>
                    <div style={{ width: '48px', height: '48px', background: '#22c55e', borderRadius: '50%', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '24px' }}>✓</div>
                    <div style={{ fontSize: '12px', marginTop: '12px', color: 'var(--g1-text)' }}>HEALTH_OK</div>
                  </div>
                </div>
              </div>

              {/* GUESTS */}
              <div className="pm-card" style={{ padding: '20px', animation: 'fadeUp 0.3s ease 0.1s both' }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#3b82f6', marginBottom: '16px' }}>Guests</div>
                <div style={{ display: 'flex', justifyContent: 'space-around' }}>
                   <div style={{ flex: 1, borderRight: '1px solid var(--g1-border)', paddingRight: '20px' }}>
                     <div style={{ fontWeight: 600, marginBottom: '20px', textAlign: 'center' }}>Virtual Machines</div>
                     <div style={{ maxWidth: '200px', margin: '0 auto' }}>
                       <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '10px' }}><span><span style={{ color: '#22c55e', marginRight: '6px' }}>●</span> Running</span> <span style={{ fontWeight: 600 }}>9</span></div>
                       <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '10px' }}><span><span style={{ color: 'var(--g1-muted)', marginRight: '6px' }}>●</span> Stopped</span> <span style={{ fontWeight: 600 }}>58</span></div>
                       <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}><span><span style={{ color: 'var(--g1-muted)', marginRight: '6px', fontSize: '14px' }}>○</span> Templates</span> <span style={{ fontWeight: 600 }}>1</span></div>
                     </div>
                   </div>
                   <div style={{ flex: 1, paddingLeft: '20px' }}>
                     <div style={{ fontWeight: 600, marginBottom: '20px', textAlign: 'center' }}>LXC Container</div>
                     <div style={{ maxWidth: '200px', margin: '0 auto' }}>
                       <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '10px' }}><span><span style={{ color: '#22c55e', marginRight: '6px' }}>●</span> Running</span> <span style={{ fontWeight: 600 }}>10</span></div>
                       <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}><span><span style={{ color: 'var(--g1-muted)', marginRight: '6px' }}>●</span> Stopped</span> <span style={{ fontWeight: 600 }}>4019</span></div>
                     </div>
                   </div>
                </div>
              </div>

              {/* RESOURCES */}
              <div className="pm-card" style={{ padding: '20px', animation: 'fadeUp 0.3s ease 0.2s both' }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#3b82f6', marginBottom: '24px' }}>Resources</div>
                <div style={{ display: 'flex', justifyContent: 'space-around' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontWeight: 600, marginBottom: '12px' }}>CPU</div>
                    <div style={{ position: 'relative', width: '120px', height: '60px', margin: '0 auto', overflow: 'hidden' }}>
                       <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: '10px solid var(--g1-border)', position: 'absolute', top: 0, left: 0 }}></div>
                       <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: '10px solid transparent', borderTopColor: '#3b82f6', borderRightColor: '#3b82f6', position: 'absolute', top: 0, left: 0, transform: 'rotate(-45deg)', opacity: 0.8 }}></div>
                       <div style={{ position: 'absolute', bottom: '0px', width: '100%', textAlign: 'center', fontSize: '24px', color: 'var(--g1-text)' }}>13%</div>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--g1-muted)', marginTop: '8px' }}>of 36 CPU(s)</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontWeight: 600, marginBottom: '12px' }}>Memory</div>
                    <div style={{ position: 'relative', width: '120px', height: '60px', margin: '0 auto', overflow: 'hidden' }}>
                       <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: '10px solid var(--g1-border)', position: 'absolute', top: 0, left: 0 }}></div>
                       <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: '10px solid transparent', borderTopColor: '#3b82f6', borderRightColor: '#3b82f6', borderBottomColor: '#3b82f6', position: 'absolute', top: 0, left: 0, transform: 'rotate(-25deg)', opacity: 0.8 }}></div>
                       <div style={{ position: 'absolute', bottom: '0px', width: '100%', textAlign: 'center', fontSize: '24px', color: 'var(--g1-text)' }}>63%</div>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--g1-muted)', marginTop: '8px' }}>58.90 GiB of 93.70 GiB</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontWeight: 600, marginBottom: '12px' }}>Storage</div>
                    <div style={{ position: 'relative', width: '120px', height: '60px', margin: '0 auto', overflow: 'hidden' }}>
                       <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: '10px solid var(--g1-border)', position: 'absolute', top: 0, left: 0 }}></div>
                       <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: '10px solid transparent', borderTopColor: '#3b82f6', position: 'absolute', top: 0, left: 0, transform: 'rotate(-45deg)', opacity: 0.8 }}></div>
                       <div style={{ position: 'absolute', bottom: '0px', width: '100%', textAlign: 'center', fontSize: '24px', color: 'var(--g1-text)' }}>6%</div>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--g1-muted)', marginTop: '8px' }}>2.42 TiB of 39.69 TiB</div>
                  </div>
                </div>
              </div>

              {/* NODES */}
              <div className="pm-card" style={{ animation: 'fadeUp 0.3s ease 0.3s both' }}>
                <div style={{ padding: '16px 20px', fontSize: '14px', fontWeight: 600, color: '#3b82f6', borderBottom: '1px solid var(--g1-border)' }}>
                  Nodes
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--g1-border)' }}>
                    <tr>
                      <th style={{ padding: '12px 20px', textAlign: 'left', fontWeight: 500, color: 'var(--g1-muted)' }}>Name</th>
                      <th style={{ padding: '12px 20px', textAlign: 'left', fontWeight: 500, color: 'var(--g1-muted)' }}>ID</th>
                      <th style={{ padding: '12px 20px', textAlign: 'left', fontWeight: 500, color: 'var(--g1-muted)' }}>Online</th>
                      <th style={{ padding: '12px 20px', textAlign: 'left', fontWeight: 500, color: 'var(--g1-muted)' }}>CPU usage</th>
                      <th style={{ padding: '12px 20px', textAlign: 'left', fontWeight: 500, color: 'var(--g1-muted)' }}>Memory usage</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '12px 20px', color: 'var(--g1-text)' }}>prod1</td>
                      <td style={{ padding: '12px 20px', color: 'var(--g1-text)' }}>1</td>
                      <td style={{ padding: '12px 20px', color: '#22c55e', fontWeight: 'bold' }}>✓</td>
                      <td style={{ padding: '12px 20px' }}><div style={{ background: 'rgba(59,130,246,0.1)', color: '#60A5FA', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>20%</div></td>
                      <td style={{ padding: '12px 20px' }}><div style={{ background: 'rgba(59,130,246,0.2)', color: '#60A5FA', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>76%</div></td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '12px 20px', color: 'var(--g1-text)' }}>prod2</td>
                      <td style={{ padding: '12px 20px', color: 'var(--g1-text)' }}>2</td>
                      <td style={{ padding: '12px 20px', color: '#22c55e', fontWeight: 'bold' }}>✓</td>
                      <td style={{ padding: '12px 20px' }}><div style={{ background: 'rgba(59,130,246,0.1)', color: '#60A5FA', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>3%</div></td>
                      <td style={{ padding: '12px 20px' }}><div style={{ background: 'rgba(59,130,246,0.2)', color: '#60A5FA', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>61%</div></td>
                    </tr>
                    <tr>
                      <td style={{ padding: '12px 20px', color: 'var(--g1-text)' }}>prod3</td>
                      <td style={{ padding: '12px 20px', color: 'var(--g1-text)' }}>3</td>
                      <td style={{ padding: '12px 20px', color: '#22c55e', fontWeight: 'bold' }}>✓</td>
                      <td style={{ padding: '12px 20px' }}><div style={{ background: 'rgba(59,130,246,0.1)', color: '#60A5FA', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>6%</div></td>
                      <td style={{ padding: '12px 20px' }}><div style={{ background: 'rgba(59,130,246,0.2)', color: '#60A5FA', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>52%</div></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="pm-card" style={{ padding: '64px 32px', textAlign: 'center', color: 'var(--g1-muted)', animation: 'fadeUp 0.3s ease' }}>
               <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.2 }}>🛠</div>
               L'interface <strong style={{ color: 'var(--cyan)' }}>{activeTab}</strong> n'est pas encore implémentée dans cette maquette.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
