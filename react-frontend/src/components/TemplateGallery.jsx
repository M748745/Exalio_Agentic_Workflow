import React, { useState, useEffect } from 'react';
import './TemplateGallery.css';

const TemplateCard = ({ template, onImport, onPreview }) => {
  const getDifficultyColor = (difficulty) => {
    switch(difficulty?.toLowerCase()) {
      case 'beginner': return '#4caf50';
      case 'intermediate': return '#ff9800';
      case 'advanced': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  return (
    <div className="template-card">
      <div className="template-header">
        <h3 className="template-name">{template.name}</h3>
        <span
          className="template-difficulty"
          style={{ backgroundColor: getDifficultyColor(template.difficulty) }}
        >
          {template.difficulty || 'N/A'}
        </span>
      </div>

      <div className="template-category">{template.category}</div>

      <p className="template-description">{template.description}</p>

      <div className="template-stats">
        <span className="stat">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="3"/>
            <circle cx="6" cy="6" r="2"/>
            <circle cx="18" cy="6" r="2"/>
            <circle cx="6" cy="18" r="2"/>
            <circle cx="18" cy="18" r="2"/>
          </svg>
          {template.nodeCount || template.nodes?.length || 0} nodes
        </span>
        <span className="stat">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12h18M3 6h18M3 18h18"/>
          </svg>
          {template.edgeCount || template.edges?.length || 0} edges
        </span>
      </div>

      {template.tags && template.tags.length > 0 && (
        <div className="template-tags">
          {template.tags.slice(0, 3).map((tag, idx) => (
            <span key={idx} className="tag">{tag}</span>
          ))}
          {template.tags.length > 3 && (
            <span className="tag-more">+{template.tags.length - 3}</span>
          )}
        </div>
      )}

      <div className="template-actions">
        <button
          className="btn-preview"
          onClick={() => onPreview(template)}
        >
          Preview
        </button>
        <button
          className="btn-import"
          onClick={() => onImport(template)}
        >
          Import
        </button>
      </div>
    </div>
  );
};

const TemplatePreviewModal = ({ template, onClose, onImport }) => {
  // Add keyboard shortcut (ESC to close)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!template) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{template.name}</h2>
          <button className="modal-close" onClick={onClose} title="Close (ESC)">&times;</button>
        </div>

        <div className="modal-body">
          <div className="preview-section">
            <h4>Description</h4>
            <p>{template.description}</p>
          </div>

          <div className="preview-section">
            <h4>Details</h4>
            <div className="preview-details">
              <div className="detail-item">
                <strong>Category:</strong> {template.category}
              </div>
              <div className="detail-item">
                <strong>Difficulty:</strong> {template.difficulty}
              </div>
              <div className="detail-item">
                <strong>Nodes:</strong> {template.nodes?.length || 0}
              </div>
              <div className="detail-item">
                <strong>Version:</strong> {template.version || '1.0.0'}
              </div>
            </div>
          </div>

          {template.metadata?.requirements && (
            <div className="preview-section">
              <h4>Requirements</h4>
              <ul className="requirements-list">
                {template.metadata.requirements.map((req, idx) => (
                  <li key={idx}>{req}</li>
                ))}
              </ul>
            </div>
          )}

          {template.metadata?.useCases && (
            <div className="preview-section">
              <h4>Use Cases</h4>
              <ul className="use-cases-list">
                {template.metadata.useCases.map((useCase, idx) => (
                  <li key={idx}>{useCase}</li>
                ))}
              </ul>
            </div>
          )}

          {template.tags && template.tags.length > 0 && (
            <div className="preview-section">
              <h4>Tags</h4>
              <div className="template-tags">
                {template.tags.map((tag, idx) => (
                  <span key={idx} className="tag">{tag}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-cancel" onClick={onClose}>Cancel</button>
          <button className="btn-import-modal" onClick={() => {
            onImport(template);
            onClose();
          }}>
            Import Template
          </button>
        </div>
      </div>
    </div>
  );
};

const TemplateGallery = ({ onImportTemplate, onClose }) => {
  const [templates, setTemplates] = useState([]);
  const [filteredTemplates, setFilteredTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [previewTemplate, setPreviewTemplate] = useState(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  useEffect(() => {
    filterTemplates();
  }, [templates, selectedCategory, searchQuery]);

  // Add keyboard shortcut (ESC to close gallery)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !previewTemplate && onClose) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, previewTemplate]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/templates/list');

      if (!response.ok) {
        throw new Error(`Failed to fetch templates: ${response.statusText}`);
      }

      const data = await response.json();
      setTemplates(data.templates || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filterTemplates = () => {
    let filtered = templates;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(t =>
        t.category?.toLowerCase() === selectedCategory.toLowerCase()
      );
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(t =>
        t.name?.toLowerCase().includes(query) ||
        t.description?.toLowerCase().includes(query) ||
        t.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }

    setFilteredTemplates(filtered);
  };

  const handleImportTemplate = async (template) => {
    try {
      const response = await fetch('http://localhost:5000/api/templates/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ template_id: template.id }),
      });

      if (!response.ok) {
        throw new Error('Failed to import template');
      }

      const data = await response.json();

      // Call the parent callback with the loaded template
      if (onImportTemplate && data.template) {
        onImportTemplate(data.template);
      }

      alert(`Template "${template.name}" imported successfully!`);

      if (onClose) {
        onClose();
      }
    } catch (err) {
      console.error('Error importing template:', err);
      alert(`Failed to import template: ${err.message}`);
    }
  };

  const categories = ['all', ...new Set(templates.map(t => t.category).filter(Boolean))];

  return (
    <div className="template-gallery">
      <div className="gallery-header">
        <div className="header-top">
          <h2>Template Gallery</h2>
          {onClose && (
            <button className="close-gallery" onClick={onClose} title="Close (ESC)">
              &times;
            </button>
          )}
        </div>

        <div className="gallery-controls">
          <input
            type="text"
            className="search-input"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <div className="category-filters">
            {categories.map(category => (
              <button
                key={category}
                className={`category-filter ${selectedCategory === category ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                {category === 'all' ? 'All' : category}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="gallery-content">
        {loading && (
          <div className="gallery-loading">
            <div className="spinner"></div>
            <p>Loading templates...</p>
          </div>
        )}

        {error && (
          <div className="gallery-error">
            <p>Error loading templates: {error}</p>
            <button onClick={fetchTemplates}>Retry</button>
          </div>
        )}

        {!loading && !error && filteredTemplates.length === 0 && (
          <div className="gallery-empty">
            <p>No templates found matching your criteria.</p>
          </div>
        )}

        {!loading && !error && filteredTemplates.length > 0 && (
          <div className="templates-grid">
            {filteredTemplates.map(template => (
              <TemplateCard
                key={template.id}
                template={template}
                onImport={handleImportTemplate}
                onPreview={setPreviewTemplate}
              />
            ))}
          </div>
        )}
      </div>

      {previewTemplate && (
        <TemplatePreviewModal
          template={previewTemplate}
          onClose={() => setPreviewTemplate(null)}
          onImport={handleImportTemplate}
        />
      )}
    </div>
  );
};

export default TemplateGallery;
