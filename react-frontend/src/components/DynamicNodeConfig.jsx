import React from 'react';
import { getNodeConfigSchema } from '../nodeConfigSchemas';

/**
 * DynamicNodeConfig - Automatically generates configuration fields for ANY node
 * based on the node's type and category
 */
const DynamicNodeConfig = ({ node, updateNodeData }) => {
  const nodeType = node.data.nodeType;
  const category = node.data.category;
  const nodeName = node.data.label;
  const icon = node.data.icon;

  // Get the configuration schema for this node
  const configFields = getNodeConfigSchema(nodeType, category);

  // Render each configuration field dynamically
  const renderField = (field) => {
    const { name, label, type, placeholder, options, rows, min, max, step, default: defaultValue } = field;
    const currentValue = node.data[name] ?? defaultValue ?? '';

    switch (type) {
      case 'text':
      case 'email':
      case 'url':
      case 'password':
        return (
          <div key={name} className="config-field">
            <label>{label}</label>
            <input
              type={type}
              value={currentValue}
              onChange={(e) => updateNodeData(node.id, { [name]: e.target.value })}
              placeholder={placeholder || ''}
            />
          </div>
        );

      case 'number':
        return (
          <div key={name} className="config-field">
            <label>{label}</label>
            <input
              type="number"
              value={currentValue}
              onChange={(e) => updateNodeData(node.id, { [name]: parseFloat(e.target.value) || 0 })}
              placeholder={placeholder || ''}
              min={min}
              max={max}
              step={step}
            />
          </div>
        );

      case 'textarea':
        return (
          <div key={name} className="config-field">
            <label>{label}</label>
            <textarea
              value={currentValue}
              onChange={(e) => updateNodeData(node.id, { [name]: e.target.value })}
              rows={rows || 4}
              placeholder={placeholder || ''}
              style={{ fontFamily: 'Consolas, Monaco, monospace', fontSize: '13px' }}
            />
          </div>
        );

      case 'select':
        return (
          <div key={name} className="config-field">
            <label>{label}</label>
            <select
              value={currentValue}
              onChange={(e) => updateNodeData(node.id, { [name]: e.target.value })}
            >
              {options && options.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
        );

      case 'file':
        return (
          <div key={name} className="config-field">
            <label>{label}</label>
            <input
              type="file"
              onChange={(e) => {
                const file = e.target.files[0];
                if (file) {
                  updateNodeData(node.id, {
                    [name]: file.name,
                    [`${name}Data`]: file  // Store file object separately
                  });
                }
              }}
              accept="*/*"
            />
            {currentValue && <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Selected: {currentValue}</div>}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <div className="config-section-header">
        {icon} {nodeName} Configuration
      </div>

      {configFields.map(field => renderField(field))}
    </>
  );
};

export default DynamicNodeConfig;
