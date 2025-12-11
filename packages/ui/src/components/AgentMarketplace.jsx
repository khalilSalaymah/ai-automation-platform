import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import AgentConfigForm from './AgentConfigForm';

export default function AgentMarketplace({ apiUrl = 'http://localhost:8000' }) {
  const { token } = useAuth();
  const [agents, setAgents] = useState([]);
  const [orgAgents, setOrgAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showConfigForm, setShowConfigForm] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (token) {
      fetchAgents();
      fetchOrgAgents();
    }
  }, [token]);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/api/marketplace/agents`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setAgents(data);
      } else {
        setError('Failed to load agents');
      }
    } catch (err) {
      setError('Failed to load agents');
      console.error('Error fetching agents:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrgAgents = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/marketplace/organization/agents`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setOrgAgents(data);
      }
    } catch (err) {
      console.error('Error fetching organization agents:', err);
    }
  };

  const getAgentStatus = (agentId) => {
    const orgAgent = orgAgents.find((oa) => oa.agent_id === agentId);
    if (!orgAgent) return 'not_deployed';
    return orgAgent.status;
  };

  const handleDeploy = async (agent, config) => {
    try {
      setError(null);

      const response = await fetch(
        `${apiUrl}/api/marketplace/organization/agents/${agent.id}/deploy`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            config,
            enable_tasks: true,
            enable_tools: true,
          }),
        }
      );

      if (response.ok) {
        await fetchOrgAgents();
        setShowConfigForm(false);
        setSelectedAgent(null);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to deploy agent');
      }
    } catch (err) {
      setError('Failed to deploy agent');
      console.error('Error deploying agent:', err);
    }
  };

  const handleEnable = async (agentId) => {
    try {
      const response = await fetch(
        `${apiUrl}/api/marketplace/organization/agents/${agentId}/enable`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (response.ok) {
        await fetchOrgAgents();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to enable agent');
      }
    } catch (err) {
      setError('Failed to enable agent');
      console.error('Error enabling agent:', err);
    }
  };

  const handleDisable = async (agentId) => {
    try {
      const response = await fetch(
        `${apiUrl}/api/marketplace/organization/agents/${agentId}/disable`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (response.ok) {
        await fetchOrgAgents();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to disable agent');
      }
    } catch (err) {
      setError('Failed to disable agent');
      console.error('Error disabling agent:', err);
    }
  };

  const handleConfigUpdate = async (agentId, config) => {
    try {
      setError(null);

      const response = await fetch(
        `${apiUrl}/api/marketplace/organization/agents/${agentId}/config`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ config }),
        }
      );

      if (response.ok) {
        await fetchOrgAgents();
        setShowConfigForm(false);
        setSelectedAgent(null);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update configuration');
      }
    } catch (err) {
      setError('Failed to update configuration');
      console.error('Error updating config:', err);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      available: 'bg-gray-100 text-gray-800',
      deployed: 'bg-green-100 text-green-800',
      disabled: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      not_deployed: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status) => {
    const labels = {
      available: 'Available',
      deployed: 'Deployed',
      disabled: 'Disabled',
      error: 'Error',
      not_deployed: 'Not Deployed',
    };
    return labels[status] || status;
  };

  const filteredAgents = agents.filter((agent) => {
    const matchesCategory = categoryFilter === 'all' || agent.category === categoryFilter;
    const matchesSearch =
      searchQuery === '' ||
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const categories = ['all', ...new Set(agents.map((a) => a.category).filter(Boolean))];

  if (loading && agents.length === 0) {
    return <div className="p-6 text-center">Loading agents...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Agent Marketplace</h1>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <div className="flex-1">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents..."
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>
        <div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border rounded-lg"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => {
          const status = getAgentStatus(agent.id);
          const orgAgent = orgAgents.find((oa) => oa.agent_id === agent.id);

          return (
            <div
              key={agent.id}
              className="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold">{agent.display_name}</h3>
                  <p className="text-sm text-gray-500">{agent.name}</p>
                </div>
                {agent.icon_url && (
                  <img src={agent.icon_url} alt={agent.display_name} className="w-12 h-12" />
                )}
              </div>

              <p className="text-gray-700 mb-4 line-clamp-3">{agent.description}</p>

              <div className="flex flex-wrap gap-2 mb-4">
                {agent.category && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {agent.category}
                  </span>
                )}
                {agent.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between mb-4">
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                    status
                  )}`}
                >
                  {getStatusLabel(status)}
                </span>
                {agent.version && (
                  <span className="text-xs text-gray-500">v{agent.version}</span>
                )}
              </div>

              <div className="flex gap-2">
                {status === 'not_deployed' && (
                  <button
                    onClick={() => {
                      setSelectedAgent(agent);
                      setShowConfigForm(true);
                    }}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Deploy
                  </button>
                )}

                {status === 'deployed' && (
                  <>
                    <button
                      onClick={() => {
                        setSelectedAgent({ ...agent, orgAgent });
                        setShowConfigForm(true);
                      }}
                      className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                    >
                      Configure
                    </button>
                    <button
                      onClick={() => handleDisable(agent.id)}
                      className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
                    >
                      Disable
                    </button>
                  </>
                )}

                {status === 'disabled' && (
                  <>
                    <button
                      onClick={() => handleEnable(agent.id)}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      Enable
                    </button>
                    <button
                      onClick={() => {
                        setSelectedAgent({ ...agent, orgAgent });
                        setShowConfigForm(true);
                      }}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                    >
                      Configure
                    </button>
                  </>
                )}

                {status === 'error' && (
                  <>
                    <button
                      onClick={() => {
                        setSelectedAgent({ ...agent, orgAgent });
                        setShowConfigForm(true);
                      }}
                      className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                    >
                      Fix Configuration
                    </button>
                  </>
                )}

                {agent.documentation_url && (
                  <a
                    href={agent.documentation_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
                  >
                    Docs
                  </a>
                )}
              </div>

              {orgAgent?.last_error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  <strong>Error:</strong> {orgAgent.last_error}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filteredAgents.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No agents found matching your criteria.
        </div>
      )}

      {/* Config Form Modal */}
      {showConfigForm && selectedAgent && (
        <AgentConfigForm
          agent={selectedAgent}
          onClose={() => {
            setShowConfigForm(false);
            setSelectedAgent(null);
          }}
          onDeploy={handleDeploy}
          onConfigUpdate={handleConfigUpdate}
          apiUrl={apiUrl}
          token={token}
        />
      )}
    </div>
  );
}
