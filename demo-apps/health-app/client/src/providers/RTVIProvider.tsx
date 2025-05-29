import { type PropsWithChildren, useEffect } from 'react';
import { LLMFunctionCallData, LLMHelper, RTVIClient } from '@pipecat-ai/client-js';
import { DailyTransport } from '@pipecat-ai/daily-transport';
import { RTVIClientProvider } from '@pipecat-ai/client-react';

const transport = new DailyTransport();

// Get the server URL from environment or use a default
const SERVER_URL = (import.meta as any).env?.VITE_SERVER_URL || 'http://localhost:7860';
console.log('Using server URL:', SERVER_URL);

const client = new RTVIClient({
  transport,
  params: {
    baseUrl: SERVER_URL,
    endpoints: {
      connect: '/connect',
    },
  },
  enableMic: true,
  enableCam: false,
});

const llmHelper = new LLMHelper({
  callbacks: {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onLLMFunctionCall: (func: LLMFunctionCallData) => {
      // console.log('Function call:', func);
    }
  },
});

client.registerHelper("llm", llmHelper);

export function RTVIProvider({ children }: PropsWithChildren) {
  useEffect(() => {
    // Add error handlers
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleError = (error: any) => {
      console.error('RTVI Client Error:', error);
    };

    const handleConnected = () => {
      console.log('RTVI Client Connected');
    };

    const handleDisconnected = () => {
      console.log('RTVI Client Disconnected');
    };

    client.on('error', handleError);
    client.on('connected', handleConnected);
    client.on('disconnected', handleDisconnected);

    return () => {
      client.off('error', handleError);
      client.off('connected', handleConnected);
      client.off('disconnected', handleDisconnected);
    };
  }, []);

  return <RTVIClientProvider client={client}>{children}</RTVIClientProvider>;
}
