import React, { useState, useEffect } from 'react';

export default function AgentConfigForm({
  agent,
  onClose,
  onDeploy,
  onConfigUpdate,
  apiUrl,
  token,
}) {
  const [config, setConfig] = useState({});
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const isDeployed = agent.orgAgent && agent.orgAgent.status !== 'not_deployed';

  useEffect(() => {
    // Initialize config from existing deployment or defaults
    if (agent.orgAgent && agent.orgAgent.config) {
      setConfig(agent.orgAgent.config);
    } else {
      // Initialize with default values from schema
      const defaultConfig = {};
      if (agent.config_schema && agent.config_schema.properties) {
        Object.keys(agent.config_schema.properties).forEach((key) => {
          const prop = agent.config_schema.properties[key];
          if (prop.default !== undefined) {
            defaultConfig[key] = prop.default;
          } else if (prop.type === 'object') {
            defaultConfig[key] = {};
          } else if (prop.type === 'array') {
            defaultConfig[key] = [];
          } else if (prop.type === 'boolean') {
            defaultConfig[key] = false;
          } else if (prop.type === 'number' || prop.type === 'integer') {
            defaultConfig[key] = 0;
          } else {
            defaultConfig[key] = '';
          }
        });
      }
      setConfig(defaultConfig);
    }
  }, [agent]);

  const validateConfig = () => {
    const newErrors = {};
    if (!agent.config_schema || !agent.config_schema.properties) {
      return true; // No schema, skip validation
    }

    const required = agent.config_schema.required || [];
    const properties = agent.config_schema.properties;

    required.forEach((key) => {
      if (config[key] === undefined || config[key] === null || config[key] === '') {
        newErrors[key] = 'This field is required';
      }
    });

    Object.keys(properties).forEach((key) => {
      const value = config[key];
      const prop = properties[key];

      if (value === undefined || value === null || value === '') {
        return; // Skip validation for empty optional fields
      }

      // Type validation
      if (prop.type === 'string' && typeof value !== 'string') {
        newErrors[key] = 'Must be a string';
      } else if (prop.type === 'number' && typeof value !== 'number') {
        newErrors[key] = 'Must be a number';
      } else if (prop.type === 'integer' && (!Number.isInteger(value) || typeof value !== 'number')) {
        newErrors[key] = 'Must be an integer';
      } else if (prop.type === 'boolean' && typeof value !== 'boolean') {
        newErrors[key] = 'Must be a boolean';
      } else if (prop.type === 'array' && !Array.isArray(value)) {
        newErrors[key] = 'Must be an array';
      } else if (prop.type === 'object' && typeof value !== 'object' || Array.isArray(value)) {
        newErrors[key] = 'Must be an object';
      }

      // Format validation
      if (prop.format === 'email' && typeof value === 'string' && !value.includes('@')) {
        newErrors[key] = 'Must be a valid email';
      } else if (prop.format === 'uri' && typeof value === 'string') {
        try {
          new URL(value);
        } catch {
          newErrors[key] = 'Must be a valid URL';
        }
      }

      // Min/Max validation
      if (prop.minimum !== undefined && value < prop.minimum) {
        newErrors[key] = `Must be at least ${prop.minimum}`;
      }
      if (prop.maximum !== undefined && value > prop.maximum) {
        newErrors[key] = `Must be at most ${prop.maximum}`;
      }
      if (prop.minLength !== undefined && value.length < prop.minLength) {
        newErrors[key] = `Must be at least ${prop.minLength} characters`;
      }
      if (prop.maxLength !== undefined && value.length > prop.maxLength) {
        newErrors[key] = `Must be at most ${prop.maxLength} characters`;
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateConfig()) {
      return;
    }

    setSubmitting(true);
    try {
      if (isDeployed) {
        await onConfigUpdate(agent.id, config);
      } else {
        await onDeploy(agent, config);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (key, prop) => {
    const value = config[key];
    const error = errors[key];
    const required = (agent.config_schema.required || []).includes(key);
    const isPassword = prop.format === 'password' || key.toLowerCase().includes('password') || key.toLowerCase().includes('secret') || key.toLowerCase().includes('key');

    const handleChange = (newValue) => {
      setConfig((prev) => ({ ...prev, [key]: newValue }));
      // Clear error when user starts typing
      if (errors[key]) {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors[key];
          return newErrors;
        });
      }
    };

    switch (prop.type) {
      case 'boolean':
        return (
          <div key={key} className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={value || false}
                onChange={(e) => handleChange(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm font-medium text-gray-700">
                {prop.title || key}
                {required && <span className="text-red-500 ml-1">*</span>}
              </span>
            </label>
            {prop.description && (
              <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
            )}
            {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
          </div>
        );

      case 'integer':
      case 'number':
        return (
          <div key={key} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {prop.title || key}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <input
              type="number"
              value={value || ''}
              onChange={(e) => handleChange(prop.type === 'integer' ? parseInt(e.target.value, 10) : parseFloat(e.target.value))}
              min={prop.minimum}
              max={prop.maximum}
              step={prop.type === 'integer' ? 1 : 'any'}
              className={`w-full px-3 py-2 border rounded-lg ${error ? 'border-red-500' : ''}`}
            />
            {prop.description && (
              <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
            )}
            {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
          </div>
        );

      case 'array':
        return (
          <div key={key} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {prop.title || key}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <textarea
              value={Array.isArray(value) ? value.join('\n') : ''}
              onChange={(e) => handleChange(e.target.value.split('\n').filter((v) => v.trim()))}
              rows={4}
              className={`w-full px-3 py-2 border rounded-lg ${error ? 'border-red-500' : ''}`}
              placeholder="Enter one item per line"
            />
            {prop.description && (
              <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
            )}
            {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
          </div>
        );

      case 'object':
        return (
          <div key={key} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {prop.title || key}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <textarea
              value={typeof value === 'object' ? JSON.stringify(value, null, 2) : ''}
              onChange={(e) => {
                try {
                  handleChange(JSON.parse(e.target.value));
                } catch {
                  // Invalid JSON, don't update
                }
              }}
              rows={6}
              className={`w-full px-3 py-2 border rounded-lg font-mono text-sm ${error ? 'border-red-500' : ''}`}
              placeholder="{}"
            />
            {prop.description && (
              <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
            )}
            {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
          </div>
        );

      default:
        // string or other
        if (prop.enum) {
          return (
            <div key={key} className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {prop.title || key}
                {required && <span className="text-red-500 ml-1">*</span>}
              </label>
              <select
                value={value || ''}
                onChange={(e) => handleChange(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg ${error ? 'border-red-500' : ''}`}
              >
                <option value="">Select...</option>
                {prop.enum.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              {prop.description && (
                <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
              )}
              {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
            </div>
          );
        }

        return (
          <div key={key} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {prop.title || key}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <input
              type={isPassword ? 'password' : prop.format === 'email' ? 'email' : prop.format === 'uri' ? 'url' : 'text'}
              value={value || ''}
              onChange={(e) => handleChange(e.target.value)}
              placeholder={prop.default || prop.description}
              className={`w-full px-3 py-2 border rounded-lg ${error ? 'border-red-500' : ''}`}
            />
            {prop.description && (
              <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
            )}
            {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
          </div>
        );
    }
  };

  if (!agent.config_schema || !agent.config_schema.properties) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h2 className="text-2xl font-bold mb-4">Configure {agent.display_name}</h2>
          <p className="text-gray-600 mb-4">
            This agent does not require any configuration.
          </p>
          <div className="flex gap-2 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              onClick={() => onDeploy(agent, {})}
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Deploying...' : 'Deploy'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const fields = Object.keys(agent.config_schema.properties || {});

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">
          {isDeployed ? 'Configure' : 'Deploy'} {agent.display_name}
        </h2>
        <p className="text-gray-600 mb-6">{agent.description}</p>

        <form onSubmit={handleSubmit}>
          {fields.map((key) => {
            const prop = agent.config_schema.properties[key];
            return renderField(key, prop);
          })}

          {fields.length === 0 && (
            <p className="text-gray-600 mb-4">No configuration required.</p>
          )}

          <div className="flex gap-2 justify-end mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || Object.keys(errors).length > 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting
                ? isDeployed
                  ? 'Updating...'
                  : 'Deploying...'
                : isDeployed
                ? 'Update Configuration'
                : 'Deploy Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
