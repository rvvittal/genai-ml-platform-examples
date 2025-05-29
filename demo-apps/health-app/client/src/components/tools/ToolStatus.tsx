import { useState, useEffect } from 'react';
import { Box, Chip } from '@mui/material';
import { useRTVIClient } from '@pipecat-ai/client-react';
import { RTVIEvent } from '@pipecat-ai/client-js';
import Spinner from '@cloudscape-design/components/spinner';

export function ToolStatus() {
  const [currentAction, setCurrentAction] = useState<string | null>(null);
  const [actionDetails, setActionDetails] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const client = useRTVIClient();

  useEffect(() => {
    if (!client) return;

    const handleFunctionCall = (event: any) => {
      const { function_name, args } = event;
      setCurrentAction(` ${function_name.replace(/_/g, ' ')}`);
      setActionDetails(args);
      setIsProcessing(true);
    };

    const handleBotResponse = () => {
      setIsProcessing(false);
      setCurrentAction(null);
      setActionDetails(null);
    };

    client.on(RTVIEvent.LLMFunctionCall, handleFunctionCall);
    client.on(RTVIEvent.BotTranscript, handleBotResponse);

    return () => {
      client.off(RTVIEvent.LLMFunctionCall, handleFunctionCall);
      client.off(RTVIEvent.BotTranscript, handleBotResponse);
    };
  }, [client]);

  if (!currentAction && !isProcessing) return null;

  return (
    <div className='flex flex-row text-gray-600 font-light text-sm gap-2'>
      <div >
        {isProcessing && <Spinner size='normal' />}
      </div>
      <div className='flex-1 flex flex-col gap-1'>
        <span>
          <span className='font-medium'>Performing:</span>{currentAction}
        </span>
        <div className='flex'>
          {actionDetails && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {Object.entries(actionDetails).map(([key, value]) => {
                if (Array.isArray(value)) {
                  return value.map((item, index) => (
                    <Chip
                      key={`${key}-${index}`}
                      label={`${key}: ${item}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  ));
                }
                return (
                  <Chip
                    key={key}
                    label={`${key}: ${value}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                );
              })}
            </Box>
          )}
        </div>
      </div>
    </div>
  );
} 
