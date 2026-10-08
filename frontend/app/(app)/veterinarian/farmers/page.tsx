'use client';

import { Fragment } from 'react';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { strftime } from '@/lib/utils/format';
import type { User } from '@/types/models';

function FarmerModal({ farmer }: { farmer: User }) {
  return (
    <div className="modal fade" id={`farmerModal${farmer.id}`} tabIndex={-1}>
      <div className="modal-dialog">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">{farmer.full_name || farmer.username}</h5>
            <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div className="modal-body">
            <p className="mb-1"><strong>Username:</strong> {farmer.username}</p>
            <p className="mb-1"><strong>Email:</strong> {farmer.email}</p>
            <p className="mb-1"><strong>Phone:</strong> {farmer.phone || '--'}</p>
            <p className="mb-1"><strong>Farm:</strong> {farmer.farm_name || '--'}</p>
            <p className="mb-1"><strong>Block:</strong> {farmer.location || '--'}</p>
            <p className="mb-1"><strong>Village:</strong> {farmer.specific_location || '--'}</p>
            <p className="mb-1"><strong>Animal Types:</strong> {farmer.animal_types || '--'}</p>
            <p className="mb-0"><strong>Production Focus:</strong> {farmer.production_focus || '--'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// templates/veterinarian/farmer_mapping.html
export default function FarmerMappingPage() {
  return (
    <FlaskPage<{ assigned_farmers: User[] }>
      title="Farmer Mapping - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="farmers" />}
    >
      {({ assigned_farmers }, page) => {
        const villagesCovered = new Set(assigned_farmers.map((farmer) => farmer.specific_location).filter(Boolean)).size;

        // Farmers per village, in the order the villages first appear.
        const villages = new Map<string, number>();
        for (const farmer of assigned_farmers) {
          const key = farmer.specific_location || farmer.location || 'Unspecified';
          villages.set(key, (villages.get(key) ?? 0) + 1);
        }

        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h2><i className="bi bi-people"></i> Farmer Mapping &amp; Network Management</h2>
            </div>

            <div className="alert alert-info d-flex align-items-center">
              <i className="bi bi-info-circle-fill me-2 fs-5"></i>
              <div>
                Farmers are <strong>automatically assigned</strong> to you when they register in your block
                (<strong>{page.user?.location || 'not set'}</strong>). Their symptom reports and AI predictions
                are routed to you for review &mdash; no manual mapping required.
              </div>
            </div>

            {/* Farmer Network Statistics */}
            <div className="row mb-4">
              <div className="col-md-4">
                <div className="card">
                  <div className="card-body text-center">
                    <h6 className="card-title text-muted">Assigned Farmers (Your Block)</h6>
                    <h2 className="text-primary mb-0">{assigned_farmers.length}</h2>
                  </div>
                </div>
              </div>
              <div className="col-md-4">
                <div className="card">
                  <div className="card-body text-center">
                    <h6 className="card-title text-muted">Your Block</h6>
                    <h2 className="text-success mb-0">{page.user?.location || 'Not set'}</h2>
                  </div>
                </div>
              </div>
              <div className="col-md-4">
                <div className="card">
                  <div className="card-body text-center">
                    <h6 className="card-title text-muted">Villages Covered</h6>
                    <h2 className="text-info mb-0">{villagesCovered}</h2>
                  </div>
                </div>
              </div>
            </div>

            {/* Assigned Farmers Table */}
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Assigned Farmers</h5>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  {/* Per-farmer details modals. The template wrote them between table
                      rows, where the browser moves them out to just before the table. */}
                  {assigned_farmers.map((farmer) => <FarmerModal key={farmer.id} farmer={farmer} />)}

                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Username</th>
                        <th>Farmer Name</th>
                        <th>Contact</th>
                        <th>Farm / Village</th>
                        <th>Animal Types</th>
                        <th>Registered</th>
                        <th>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {assigned_farmers.length > 0 ? (
                        assigned_farmers.map((f) => (
                          <tr key={f.id}>
                            <td>{f.username}</td>
                            <td>
                              <strong>{f.full_name || f.username}</strong><br />
                              <small className="text-muted">{f.email}</small>
                            </td>
                            <td>{f.phone || '--'}</td>
                            <td>
                              {f.farm_name || '-'}<br />
                              <small className="text-muted">{f.specific_location || f.location}</small>
                            </td>
                            <td>
                              {f.animal_types_list.length > 0 ? (
                                f.animal_types_list.map((animal, index) => (
                                  <Fragment key={index}><span className="badge bg-secondary">{animal}</span>{' '}</Fragment>
                                ))
                              ) : (
                                <span className="text-muted">-</span>
                              )}
                            </td>
                            <td>{f.registration_date ? strftime(f.registration_date, '%b %d, %Y') : '-'}</td>
                            <td>
                              <button type="button" className="btn btn-sm btn-outline-info" data-bs-toggle="modal" data-bs-target={`#farmerModal${f.id}`}>
                                <i className="bi bi-eye"></i> View
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="text-center text-muted py-4">
                            <i className="bi bi-people" style={{ fontSize: '2rem' }}></i>
                            <p className="mb-0 mt-2">No farmers have registered in your block yet. They will appear here automatically once they do.</p>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Village Distribution */}
            <div className="card mt-4">
              <div className="card-header">
                <h5 className="mb-0"><i className="bi bi-geo-alt"></i> Village Distribution</h5>
              </div>
              <div className="card-body">
                <div className="list-group list-group-flush">
                  {villages.size > 0 ? (
                    [...villages.entries()].map(([location, count]) => (
                      <div key={location} className="list-group-item d-flex justify-content-between">
                        <span>{location}</span>
                        <span className="badge bg-primary">{count} farmer{count !== 1 ? 's' : ''}</span>
                      </div>
                    ))
                  ) : (
                    <div className="list-group-item text-center text-muted">No farmers assigned yet.</div>
                  )}
                </div>
              </div>
            </div>
          </>
        );
      }}
    </FlaskPage>
  );
}
