/**
 * Traffic details panel showing full request/response information
 */

import { useState } from 'react';
import { cn, formatBytes, formatDuration, getMethodClass, getStatusCodeClass } from '@/lib/utils';
import { Tabs, TabPanel, useTabs } from '@/components/common/Tabs';
import { Button } from '@/components/common/Button';
import type { TrafficEntry } from '@/types';

export interface TrafficDetailsProps {
  entry: TrafficEntry | null;
  onClose: () => void;
}

export function TrafficDetails({ entry, onClose }: TrafficDetailsProps) {
  const { activeTab, setActiveTab } = useTabs('headers');
  const [showRaw, setShowRaw] = useState(false);

  if (!entry) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <p>Select a request to view details</p>
      </div>
    );
  }

  const tabs = [
    { id: 'headers', label: 'Headers' },
    { id: 'request', label: 'Request' },
    { id: 'response', label: 'Response' },
    { id: 'timing', label: 'Timing' },
  ];

  return (
    <div className="h-full flex flex-col bg-gray-900 border-l border-gray-700">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-700">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className={cn('px-2 py-0.5 rounded text-xs font-medium', getMethodClass(entry.method))}>
                {entry.method}
              </span>
              <span className={cn('font-mono text-sm', getStatusCodeClass(entry.statusCode))}>
                {entry.statusCode}
              </span>
            </div>
            <p className="text-sm text-gray-300 break-all font-mono">{entry.url}</p>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
              <span>{formatBytes(entry.requestSize)} sent</span>
              <span>{formatBytes(entry.responseSize)} received</span>
              <span>{formatDuration(entry.duration)}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 px-4 pt-2">
        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onChange={setActiveTab}
          variant="underline"
          size="sm"
        />
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-4">
        <TabPanel id="headers" activeTab={activeTab}>
          <HeadersPanel entry={entry} />
        </TabPanel>

        <TabPanel id="request" activeTab={activeTab}>
          <BodyPanel
            title="Request Body"
            body={entry.requestBody}
            contentType={entry.contentType}
            showRaw={showRaw}
            onToggleRaw={() => setShowRaw(!showRaw)}
          />
        </TabPanel>

        <TabPanel id="response" activeTab={activeTab}>
          <BodyPanel
            title="Response Body"
            body={entry.responseBody}
            contentType={entry.contentType}
            showRaw={showRaw}
            onToggleRaw={() => setShowRaw(!showRaw)}
          />
        </TabPanel>

        <TabPanel id="timing" activeTab={activeTab}>
          <TimingPanel entry={entry} />
        </TabPanel>
      </div>
    </div>
  );
}

// Headers panel
function HeadersPanel({ entry }: { entry: TrafficEntry }) {
  return (
    <div className="space-y-6">
      {/* Request Headers */}
      <div>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Request Headers</h3>
        <div className="bg-gray-800 rounded-lg p-3 font-mono text-xs">
          {entry.requestHeaders ? (
            Object.entries(entry.requestHeaders).map(([key, value]) => (
              <div key={key} className="flex gap-2 py-1">
                <span className="text-blue-400">{key}:</span>
                <span className="text-gray-300 break-all">{value}</span>
              </div>
            ))
          ) : (
            <p className="text-gray-500">No request headers captured</p>
          )}
        </div>
      </div>

      {/* Response Headers */}
      <div>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Response Headers</h3>
        <div className="bg-gray-800 rounded-lg p-3 font-mono text-xs">
          {entry.responseHeaders ? (
            Object.entries(entry.responseHeaders).map(([key, value]) => (
              <div key={key} className="flex gap-2 py-1">
                <span className="text-green-400">{key}:</span>
                <span className="text-gray-300 break-all">{value}</span>
              </div>
            ))
          ) : (
            <p className="text-gray-500">No response headers captured</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Body panel
function BodyPanel({
  title,
  body,
  contentType,
  showRaw,
  onToggleRaw,
}: {
  title: string;
  body?: string;
  contentType: string;
  showRaw: boolean;
  onToggleRaw: () => void;
}) {
  if (!body) {
    return (
      <div className="text-gray-500 text-center py-8">
        No body content available
      </div>
    );
  }

  const isJson = contentType.includes('json');
  let formattedBody = body;

  if (isJson && !showRaw) {
    try {
      formattedBody = JSON.stringify(JSON.parse(body), null, 2);
    } catch {
      // Keep original if parse fails
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-300">{title}</h3>
        <Button variant="ghost" size="sm" onClick={onToggleRaw}>
          {showRaw ? 'Format' : 'Raw'}
        </Button>
      </div>
      <pre className="bg-gray-800 rounded-lg p-3 font-mono text-xs text-gray-300 overflow-x-auto max-h-96">
        {formattedBody}
      </pre>
    </div>
  );
}

// Timing panel
function TimingPanel({ entry }: { entry: TrafficEntry }) {
  // Simulated timing breakdown (real implementation would get this from backend)
  const totalTime = entry.duration;
  const dns = Math.floor(totalTime * 0.05);
  const connect = Math.floor(totalTime * 0.1);
  const ssl = Math.floor(totalTime * 0.15);
  const send = Math.floor(totalTime * 0.05);
  const wait = Math.floor(totalTime * 0.5);
  const receive = totalTime - dns - connect - ssl - send - wait;

  const timings = [
    { name: 'DNS Lookup', value: dns, color: 'bg-blue-500' },
    { name: 'Connection', value: connect, color: 'bg-green-500' },
    { name: 'SSL/TLS', value: ssl, color: 'bg-purple-500' },
    { name: 'Send', value: send, color: 'bg-yellow-500' },
    { name: 'Wait (TTFB)', value: wait, color: 'bg-orange-500' },
    { name: 'Receive', value: receive, color: 'bg-red-500' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-medium text-gray-300">Request Timing</h3>
        <span className="text-xs text-gray-500">Total: {formatDuration(totalTime)}</span>
      </div>

      {/* Timing bar */}
      <div className="h-6 rounded-lg overflow-hidden flex">
        {timings.map((timing) => (
          <div
            key={timing.name}
            className={cn(timing.color, 'flex items-center justify-center text-xs text-white')}
            style={{ width: `${(timing.value / totalTime) * 100}%` }}
            title={`${timing.name}: ${formatDuration(timing.value)}`}
          >
            {timing.value > totalTime * 0.1 && formatDuration(timing.value)}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2">
        {timings.map((timing) => (
          <div key={timing.name} className="flex items-center gap-2 text-xs">
            <div className={cn('w-3 h-3 rounded', timing.color)} />
            <span className="text-gray-400">{timing.name}</span>
            <span className="text-gray-500 ml-auto">{formatDuration(timing.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
