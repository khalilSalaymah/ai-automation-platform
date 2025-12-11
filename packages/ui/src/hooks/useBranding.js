import { useState, useEffect } from 'react';

/**
 * Hook to load and apply branding settings for the organization
 */
export function useBranding(apiUrl, token) {
  const [branding, setBranding] = useState({
    logoUrl: null,
    customDomain: null,
    themeVariables: null,
    loading: true,
  });

  useEffect(() => {
    if (!apiUrl || !token) {
      setBranding(prev => ({ ...prev, loading: false }));
      return;
    }

    loadBranding();
  }, [apiUrl, token]);

  const loadBranding = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/branding/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBranding({
          logoUrl: data.logo_url,
          customDomain: data.custom_domain,
          themeVariables: data.theme_variables || {},
          loading: false,
        });

        // Apply theme variables
        if (data.theme_variables) {
          applyThemeVariables(data.theme_variables);
        }
      } else {
        setBranding(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      console.error('Error loading branding:', error);
      setBranding(prev => ({ ...prev, loading: false }));
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

  return branding;
}
