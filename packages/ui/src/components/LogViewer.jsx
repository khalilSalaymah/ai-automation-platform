import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function LogViewer({ apiUrl = 'http://localhost:8080' }) {
  const { token } = useAuth();
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    trace_id: '',
    span_id: '',
    level: '',
    operation: '',
    service: '',
    source: 'both',
    limit: 100,
  });
  const [selectedTrace, setSelectedTrace] = useState(null);

  useEffect(() => {
    if (token) {
      fetchLogs();
      fetchStats();
    }
  }, [token, filters]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (filters.trace_id) params.append('trace_id', filters.trace_id);
      if (filters.span_id) params.append('span_id', filters.span_id);
      if (filters.level) params.append('level', filters.level);
      if (filters.operation) params.append('operation', filters.operation);
      if (filters.service) params.append('service', filters.service);
      params.append('limit', filters.limit);
      params.append('source', filters.source);

      const response = await fetch(`${apiUrl}/api/admin/logs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/admin/logs/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchTraceLogs = async (traceId) => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/api/admin/logs/trace/${traceId}?limit=1000`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedTrace({ traceId, logs: data });
      }
    } catch (error) {
      console.error('Error fetching trace logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getLevelColor = (level) => {
    const colors = {
      ERROR: 'bg-red-100 text-red-800',
      WARNING: 'bg-yellow-100 text-yellow-800',
      INFO: 'bg-blue-100 text-blue-800',
      DEBUG: 'bg-gray-100 text-gray-800',
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    setFilters({
      trace_id: '',
      span_id: '',
      level: '',
      operation: '',
      service: '',
      source: 'both',
      limit: 100,
    });
    setSelectedTrace(null);
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Log Viewer</h1>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">Total Logs</div>
            <div className="text-2xl font-bold">{stats.total}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">Errors</div>
            <div className="text-2xl font-bold text-red-600">{stats.error_count}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">Warnings</div>
            <div className="text-2xl font-bold text-yellow-600">{stats.warning_count}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-500">Operations</div>
            <div className="text-2xl font-bold">{Object.keys(stats.by_operation || {}).length}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Trace ID</label>
            <input
              type="text"
              value={filters.trace_id}
              onChange={(e) => handleFilterChange('trace_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="Filter by trace ID"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Span ID</label>
            <input
              type="text"
              value={filters.span_id}
              onChange={(e) => handleFilterChange('span_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="Filter by span ID"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
            <select
              value={filters.level}
              onChange={(e) => handleFilterChange('level', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Levels</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
              <option value="DEBUG">DEBUG</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Operation</label>
            <select
              value={filters.operation}
              onChange={(e) => handleFilterChange('operation', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Operations</option>
              <option value="llm_call">LLM Call</option>
              <option value="tool_execution">Tool Execution</option>
              <option value="http_request">HTTP Request</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service</label>
            <input
              type="text"
              value={filters.service}
              onChange={(e) => handleFilterChange('service', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="Filter by service"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
            <select
              value={filters.source}
              onChange={(e) => handleFilterChange('source', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="both">Both</option>
              <option value="database">Database</option>
              <option value="file">File</option>
            </select>
          </div>
        </div>
        <div className="mt-4 flex gap-2">
          <button
            onClick={fetchLogs}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
          >
            Apply Filters
          </button>
          <button
            onClick={clearFilters}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Trace View */}
      {selectedTrace && (
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Trace: {selectedTrace.traceId}</h2>
            <button
              onClick={() => setSelectedTrace(null)}
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm"
            >
              Close
            </button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {selectedTrace.logs.map((log, idx) => (
              <div key={idx} className="border-b border-gray-200 py-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs ${getLevelColor(log.level)}`}>
                    {log.level}
                  </span>
                  <span className="text-sm text-gray-600">{formatDate(log.timestamp)}</span>
                  {log.span_id && (
                    <span className="text-xs text-gray-500">Span: {log.span_id.substring(0, 8)}</span>
                  )}
                </div>
                <div className="text-sm mt-1">{log.message}</div>
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <details className="mt-1">
                    <summary className="text-xs text-gray-500 cursor-pointer">Metadata</summary>
                    <pre className="text-xs bg-gray-50 p-2 mt-1 rounded overflow-x-auto">
                      {JSON.stringify(log.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : logs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No logs found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Level
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Message
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trace ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Operation
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Service
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(log.timestamp)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded text-xs ${getLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 max-w-md truncate">
                      {log.message}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {log.trace_id ? (
                        <button
                          onClick={() => fetchTraceLogs(log.trace_id)}
                          className="text-blue-600 hover:text-blue-800 underline"
                          title="View trace"
                        >
                          {log.trace_id.substring(0, 8)}...
                        </button>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {log.operation || 'N/A'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {log.service || 'N/A'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {log.error_value && (
                        <details>
                          <summary className="text-red-600 cursor-pointer text-xs">Error</summary>
                          <div className="mt-2 p-2 bg-red-50 rounded text-xs">
                            <div className="font-semibold">{log.error_type}</div>
                            <div className="mt-1">{log.error_value}</div>
                            {log.error_traceback && (
                              <pre className="mt-2 text-xs overflow-x-auto">
                                {log.error_traceback}
                              </pre>
                            )}
                          </div>
                        </details>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
