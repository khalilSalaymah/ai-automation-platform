import React, { useState, useEffect } from 'react';

export default function WhiteLabelConfig({ apiUrl, token, onClose }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Branding state
  const [logoUrl, setLogoUrl] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [customDomain, setCustomDomain] = useState('');
  const [themeVariables, setThemeVariables] = useState({
    primary_color: '#3b82f6',
    secondary_color: '#8b5cf6',
    accent_color: '#10b981',
    background_color: '#ffffff',
    text_color: '#1f2937',
    font_family: 'Inter, sans-serif',
    font_size_base: '16px',
    border_radius: '8px',
  });

  useEffect(() => {
    fetchBrandingSettings();
  }, []);

  const fetchBrandingSettings = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/api/branding/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setLogoUrl(data.logo_url);
        setLogoPreview(data.logo_url ? `${apiUrl}${data.logo_url}` : null);
        setCustomDomain(data.custom_domain || '');
        if (data.theme_variables) {
          setThemeVariables(prev => ({ ...prev, ...data.theme_variables }));
        }
      } else if (response.status !== 404) {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to load branding settings');
      }
    } catch (err) {
      setError('Failed to load branding settings');
      console.error('Error fetching branding settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Invalid file type. Please upload an image file (PNG, JPEG, SVG, GIF, or WebP).');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size exceeds 5MB limit.');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${apiUrl}/api/branding/logo/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setLogoUrl(data.logo_url);
        setLogoPreview(`${apiUrl}${data.logo_url}`);
        setSuccess('Logo uploaded successfully');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to upload logo');
      }
    } catch (err) {
      setError('Failed to upload logo');
      console.error('Error uploading logo:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteLogo = async () => {
    if (!confirm('Are you sure you want to delete the logo?')) return;

    try {
      setSaving(true);
      setError(null);

      const response = await fetch(`${apiUrl}/api/branding/logo`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setLogoUrl(null);
        setLogoPreview(null);
        setSuccess('Logo deleted successfully');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete logo');
      }
    } catch (err) {
      setError('Failed to delete logo');
      console.error('Error deleting logo:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch(`${apiUrl}/api/branding/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          custom_domain: customDomain || null,
          theme_variables: themeVariables,
        }),
      });

      if (response.ok) {
        setSuccess('Branding settings saved successfully');
        setTimeout(() => setSuccess(null), 3000);
        // Apply theme variables immediately
        applyThemeVariables(themeVariables);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to save branding settings');
      }
    } catch (err) {
      setError('Failed to save branding settings');
      console.error('Error saving branding settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const applyThemeVariables = (vars) => {
    const root = document.documentElement;
    if (vars.primary_color) {
      root.style.setProperty('--color-primary', vars.primary_color);
    }
    if (vars.secondary_color) {
      root.style.setProperty('--color-secondary', vars.secondary_color);
    }
    if (vars.accent_color) {
      root.style.setProperty('--color-accent', vars.accent_color);
    }
    if (vars.background_color) {
      root.style.setProperty('--color-background', vars.background_color);
    }
    if (vars.text_color) {
      root.style.setProperty('--color-text', vars.text_color);
    }
    if (vars.font_family) {
      root.style.setProperty('--font-family', vars.font_family);
    }
    if (vars.font_size_base) {
      root.style.setProperty('--font-size-base', vars.font_size_base);
    }
    if (vars.border_radius) {
      root.style.setProperty('--border-radius', vars.border_radius);
    }
  };

  const handleThemeChange = (key, value) => {
    setThemeVariables(prev => ({ ...prev, [key]: value }));
  };

  // Apply theme on load
  useEffect(() => {
    if (themeVariables) {
      applyThemeVariables(themeVariables);
    }
  }, [themeVariables]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p>Loading branding settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">White-Label Configuration</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
            {success}
          </div>
        )}

        {/* Logo Upload Section */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Logo</h3>
          <div className="flex items-center gap-4">
            {logoPreview && (
              <div className="relative">
                <img
                  src={logoPreview}
                  alt="Organization logo"
                  className="h-20 w-auto object-contain border border-gray-300 rounded"
                />
              </div>
            )}
            <div className="flex gap-2">
              <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer">
                {logoPreview ? 'Change Logo' : 'Upload Logo'}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/svg+xml,image/gif,image/webp"
                  onChange={handleLogoUpload}
                  className="hidden"
                  disabled={saving}
                />
              </label>
              {logoPreview && (
                <button
                  onClick={handleDeleteLogo}
                  disabled={saving}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  Delete Logo
                </button>
              )}
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Upload your organization logo (PNG, JPEG, SVG, GIF, or WebP, max 5MB)
          </p>
        </div>

        {/* Custom Domain Section */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Custom Domain</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domain
            </label>
            <input
              type="text"
              value={customDomain}
              onChange={(e) => setCustomDomain(e.target.value)}
              placeholder="example.com"
              className="w-full px-3 py-2 border rounded-lg"
            />
            <p className="text-sm text-gray-500 mt-1">
              Configure your custom domain for white-label access
            </p>
          </div>
        </div>

        {/* Theme Variables Section */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Theme Variables</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Primary Color
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={themeVariables.primary_color}
                  onChange={(e) => handleThemeChange('primary_color', e.target.value)}
                  className="h-10 w-20 border rounded"
                />
                <input
                  type="text"
                  value={themeVariables.primary_color}
                  onChange={(e) => handleThemeChange('primary_color', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg"
                  placeholder="#3b82f6"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Secondary Color
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={themeVariables.secondary_color}
                  onChange={(e) => handleThemeChange('secondary_color', e.target.value)}
                  className="h-10 w-20 border rounded"
                />
                <input
                  type="text"
                  value={themeVariables.secondary_color}
                  onChange={(e) => handleThemeChange('secondary_color', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg"
                  placeholder="#8b5cf6"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Accent Color
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={themeVariables.accent_color}
                  onChange={(e) => handleThemeChange('accent_color', e.target.value)}
                  className="h-10 w-20 border rounded"
                />
                <input
                  type="text"
                  value={themeVariables.accent_color}
                  onChange={(e) => handleThemeChange('accent_color', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg"
                  placeholder="#10b981"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Background Color
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={themeVariables.background_color}
                  onChange={(e) => handleThemeChange('background_color', e.target.value)}
                  className="h-10 w-20 border rounded"
                />
                <input
                  type="text"
                  value={themeVariables.background_color}
                  onChange={(e) => handleThemeChange('background_color', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg"
                  placeholder="#ffffff"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Text Color
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={themeVariables.text_color}
                  onChange={(e) => handleThemeChange('text_color', e.target.value)}
                  className="h-10 w-20 border rounded"
                />
                <input
                  type="text"
                  value={themeVariables.text_color}
                  onChange={(e) => handleThemeChange('text_color', e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg"
                  placeholder="#1f2937"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Font Family
              </label>
              <input
                type="text"
                value={themeVariables.font_family}
                onChange={(e) => handleThemeChange('font_family', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Inter, sans-serif"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base Font Size
              </label>
              <input
                type="text"
                value={themeVariables.font_size_base}
                onChange={(e) => handleThemeChange('font_size_base', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="16px"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Border Radius
              </label>
              <input
                type="text"
                value={themeVariables.border_radius}
                onChange={(e) => handleThemeChange('border_radius', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="8px"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
