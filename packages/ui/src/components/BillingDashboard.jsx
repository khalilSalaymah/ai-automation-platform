import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function BillingDashboard({ apiUrl = 'http://localhost:8000' }) {
  const { token, user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [quota, setQuota] = useState(null);
  const [usage, setUsage] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (token) {
      fetchBillingData();
    }
  }, [token]);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [subRes, quotaRes, usageRes, invoicesRes] = await Promise.all([
        fetch(`${apiUrl}/api/billing/subscription`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/billing/quota`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/billing/usage`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/billing/invoices`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
      ]);

      if (subRes.ok) {
        const subData = await subRes.json();
        setSubscription(subData);
      }

      if (quotaRes.ok) {
        const quotaData = await quotaRes.json();
        setQuota(quotaData);
      }

      if (usageRes.ok) {
        const usageData = await usageRes.json();
        setUsage(usageData);
      }

      if (invoicesRes.ok) {
        const invoicesData = await invoicesRes.json();
        setInvoices(invoicesData);
      }
    } catch (err) {
      setError('Failed to load billing data');
      console.error('Error fetching billing data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (priceId) => {
    try {
      const response = await fetch(`${apiUrl}/api/billing/checkout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          price_id: priceId,
          success_url: `${window.location.origin}/billing/success`,
          cancel_url: `${window.location.origin}/billing`,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        window.location.href = data.url;
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create checkout session');
      }
    } catch (err) {
      setError('Failed to create checkout session');
      console.error('Error creating checkout:', err);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/billing/portal`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        window.location.href = data.url;
      } else {
        setError('Failed to open customer portal');
      }
    } catch (err) {
      setError('Failed to open customer portal');
      console.error('Error opening portal:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (amount, currency = 'usd') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(amount);
  };

  const getUsagePercentage = (used, limit) => {
    if (limit === 0) return 0; // Unlimited
    return Math.min((used / limit) * 100, 100);
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      canceled: 'bg-gray-100 text-gray-800',
      past_due: 'bg-yellow-100 text-yellow-800',
      unpaid: 'bg-red-100 text-red-800',
      trialing: 'bg-blue-100 text-blue-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return <div className="p-6 text-center">Loading billing information...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Billing & Subscription</h1>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Subscription Status */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Current Subscription</h2>
        {subscription ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <span
                  className={`px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getStatusColor(
                    subscription.status
                  )}`}
                >
                  {subscription.status.toUpperCase()}
                </span>
                {subscription.cancel_at_period_end && (
                  <span className="ml-2 text-sm text-yellow-600">
                    (Cancels at period end)
                  </span>
                )}
              </div>
              <button
                onClick={handleManageSubscription}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Manage Subscription
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Current Period:</span>
                <div className="font-medium">
                  {formatDate(subscription.current_period_start)} -{' '}
                  {formatDate(subscription.current_period_end)}
                </div>
              </div>
              {subscription.trial_end && (
                <div>
                  <span className="text-gray-500">Trial Ends:</span>
                  <div className="font-medium">{formatDate(subscription.trial_end)}</div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            <p className="text-gray-600 mb-4">No active subscription</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold mb-2">Basic</h3>
                <p className="text-2xl font-bold mb-2">$29/mo</p>
                <ul className="text-sm text-gray-600 mb-4 space-y-1">
                  <li>100K tokens/month</li>
                  <li>1K API calls/month</li>
                  <li>100 scraping tasks/month</li>
                </ul>
                <button
                  onClick={() => handleUpgrade('price_basic')}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Subscribe
                </button>
              </div>
              <div className="border rounded-lg p-4 border-blue-500">
                <h3 className="font-semibold mb-2">Pro</h3>
                <p className="text-2xl font-bold mb-2">$99/mo</p>
                <ul className="text-sm text-gray-600 mb-4 space-y-1">
                  <li>1M tokens/month</li>
                  <li>10K API calls/month</li>
                  <li>1K scraping tasks/month</li>
                </ul>
                <button
                  onClick={() => handleUpgrade('price_pro')}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Subscribe
                </button>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold mb-2">Enterprise</h3>
                <p className="text-2xl font-bold mb-2">$299/mo</p>
                <ul className="text-sm text-gray-600 mb-4 space-y-1">
                  <li>Unlimited tokens</li>
                  <li>Unlimited API calls</li>
                  <li>Unlimited scraping tasks</li>
                </ul>
                <button
                  onClick={() => handleUpgrade('price_enterprise')}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Subscribe
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Usage Summary */}
      {usage && quota && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Usage This Month</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Tokens</span>
                <span>
                  {usage.tokens_used.toLocaleString()} /{' '}
                  {quota.max_tokens === 0
                    ? '∞'
                    : quota.max_tokens.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: `${getUsagePercentage(usage.tokens_used, quota.max_tokens)}%`,
                  }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>API Calls</span>
                <span>
                  {usage.api_calls_used.toLocaleString()} /{' '}
                  {quota.max_api_calls === 0
                    ? '∞'
                    : quota.max_api_calls.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: `${getUsagePercentage(usage.api_calls_used, quota.max_api_calls)}%`,
                  }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Scraping Tasks</span>
                <span>
                  {usage.scraping_tasks_used.toLocaleString()} /{' '}
                  {quota.max_scraping_tasks === 0
                    ? '∞'
                    : quota.max_scraping_tasks.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: `${getUsagePercentage(usage.scraping_tasks_used, quota.max_scraping_tasks)}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Invoices */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Invoices</h2>
        {invoices.length === 0 ? (
          <p className="text-gray-500">No invoices yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(invoice.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(invoice.amount, invoice.currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          invoice.status === 'paid'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {invoice.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {invoice.invoice_url && (
                        <a
                          href={invoice.invoice_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View
                        </a>
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
