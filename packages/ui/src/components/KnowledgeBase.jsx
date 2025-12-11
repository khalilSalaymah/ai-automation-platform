import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function KnowledgeBase({ apiUrl = 'http://localhost:8000' }) {
  const { token } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState('documents'); // 'documents', 'upload', 'url', 'notion', 'agents'
  const [urlInput, setUrlInput] = useState('');
  const [notionPageId, setNotionPageId] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [agentDocuments, setAgentDocuments] = useState({});

  useEffect(() => {
    if (token) {
      fetchDocuments();
    }
  }, [token]);

  // Poll for document status updates
  useEffect(() => {
    if (!token) return;

    const interval = setInterval(() => {
      const processingDocs = documents.filter(
        (doc) => doc.status === 'pending' || doc.status === 'processing'
      );
      if (processingDocs.length > 0) {
        fetchDocuments();
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [documents, token]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/api/knowledge/documents`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      } else {
        setError('Failed to load documents');
      }
    } catch (err) {
      setError('Failed to load documents');
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${apiUrl}/api/knowledge/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        await fetchDocuments();
        setActiveTab('documents');
        event.target.value = ''; // Reset input
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to upload document');
      }
    } catch (err) {
      setError('Failed to upload document');
      console.error('Error uploading document:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleUrlSync = async () => {
    if (!urlInput.trim()) return;

    try {
      setUploading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/api/knowledge/documents/url?url=${encodeURIComponent(urlInput)}&crawl=false`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchDocuments();
        setUrlInput('');
        setActiveTab('documents');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to sync URL');
      }
    } catch (err) {
      setError('Failed to sync URL');
      console.error('Error syncing URL:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleNotionImport = async () => {
    if (!notionPageId.trim()) return;

    try {
      setUploading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/api/knowledge/documents/notion?page_id=${encodeURIComponent(notionPageId)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchDocuments();
        setNotionPageId('');
        setActiveTab('documents');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to import Notion page');
      }
    } catch (err) {
      setError('Failed to import Notion page');
      console.error('Error importing Notion page:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      const response = await fetch(`${apiUrl}/api/knowledge/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchDocuments();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete document');
      }
    } catch (err) {
      setError('Failed to delete document');
      console.error('Error deleting document:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/api/knowledge/documents/search`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          top_k: 10,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
      } else {
        setError('Search failed');
      }
    } catch (err) {
      setError('Search failed');
      console.error('Error searching:', err);
    }
  };

  const handleLinkToAgent = async (agentName, documentIds) => {
    try {
      const response = await fetch(`${apiUrl}/api/knowledge/agents/${agentName}/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: agentName,
          document_ids: documentIds,
        }),
      });

      if (response.ok) {
        await fetchAgentDocuments(agentName);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to link documents');
      }
    } catch (err) {
      setError('Failed to link documents');
      console.error('Error linking documents:', err);
    }
  };

  const fetchAgentDocuments = async (agentName) => {
    try {
      const response = await fetch(`${apiUrl}/api/knowledge/agents/${agentName}/documents`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setAgentDocuments((prev) => ({
          ...prev,
          [agentName]: data.documents,
        }));
      }
    } catch (err) {
      console.error('Error fetching agent documents:', err);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getProgress = (doc) => {
    if (doc.total_chunks === 0) return 0;
    return Math.round((doc.processed_chunks / doc.total_chunks) * 100);
  };

  if (loading && documents.length === 0) {
    return <div className="p-6 text-center">Loading documents...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Knowledge Base</h1>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['documents', 'upload', 'url', 'notion', 'agents'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div>
          {/* Search */}
          <div className="mb-6 flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search documents..."
              className="flex-1 px-4 py-2 border rounded-lg"
            />
            <button
              onClick={handleSearch}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Search
            </button>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mb-6 bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Search Results</h2>
              <div className="space-y-4">
                {searchResults.map((result) => (
                  <div key={result.chunk_id} className="border rounded p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">{result.document_name}</h3>
                      <span className="text-sm text-gray-500">Score: {result.score.toFixed(3)}</span>
                    </div>
                    <p className="text-gray-700 text-sm">{result.content.substring(0, 200)}...</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Documents List */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Source
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{doc.name}</div>
                      {doc.source_url && (
                        <div className="text-sm text-gray-500">
                          <a
                            href={doc.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {doc.source_url}
                          </a>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {doc.source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                          doc.status
                        )}`}
                      >
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {doc.status === 'processing' || doc.status === 'pending' ? (
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${getProgress(doc)}%` }}
                          ></div>
                        </div>
                      ) : doc.status === 'completed' ? (
                        <span className="text-sm text-gray-500">
                          {doc.processed_chunks} / {doc.total_chunks} chunks
                        </span>
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Upload Document</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select File
              </label>
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={uploading}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                accept=".pdf,.txt,.md,.docx"
              />
            </div>
            {uploading && (
              <div className="text-sm text-gray-600">Uploading and processing document...</div>
            )}
          </div>
        </div>
      )}

      {/* URL Tab */}
      {activeTab === 'url' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Sync URL</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">URL</label>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>
            <button
              onClick={handleUrlSync}
              disabled={uploading || !urlInput.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {uploading ? 'Syncing...' : 'Sync URL'}
            </button>
          </div>
        </div>
      )}

      {/* Notion Tab */}
      {activeTab === 'notion' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Import Notion Page</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notion Page ID
              </label>
              <input
                type="text"
                value={notionPageId}
                onChange={(e) => setNotionPageId(e.target.value)}
                placeholder="Enter Notion page ID"
                className="w-full px-4 py-2 border rounded-lg"
              />
              <p className="mt-1 text-sm text-gray-500">
                Find the page ID in the Notion page URL
              </p>
            </div>
            <button
              onClick={handleNotionImport}
              disabled={uploading || !notionPageId.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {uploading ? 'Importing...' : 'Import Page'}
            </button>
          </div>
        </div>
      )}

      {/* Agents Tab */}
      {activeTab === 'agents' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Link Documents to Agents</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Agent Name</label>
              <input
                type="text"
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                placeholder="Enter agent name"
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>
            {selectedAgent && (
              <div>
                <button
                  onClick={() => fetchAgentDocuments(selectedAgent)}
                  className="mb-4 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Load Agent Documents
                </button>
                {agentDocuments[selectedAgent] && (
                  <div className="mt-4">
                    <h3 className="font-semibold mb-2">Linked Documents:</h3>
                    <div className="space-y-2">
                      {agentDocuments[selectedAgent].map((doc) => (
                        <div key={doc.id} className="p-2 bg-gray-50 rounded">
                          {doc.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="mt-4">
                  <h3 className="font-semibold mb-2">Select Documents to Link:</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {documents.map((doc) => (
                      <label key={doc.id} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          defaultChecked={
                            agentDocuments[selectedAgent]?.some((d) => d.id === doc.id) || false
                          }
                          className="rounded"
                        />
                        <span>{doc.name}</span>
                      </label>
                    ))}
                  </div>
                  <button
                    onClick={() => {
                      const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
                      const selectedIds = Array.from(checkboxes).map((cb) => {
                        const label = cb.closest('label');
                        const doc = documents.find((d) => d.name === label.querySelector('span').textContent);
                        return doc?.id;
                      }).filter(Boolean);
                      handleLinkToAgent(selectedAgent, selectedIds);
                    }}
                    className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Link Documents
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
